import os
import uuid
import glob
from schemas import *
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from resume import generate_latex
from typing import Dict
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

Base = declarative_base()
DATABASE_URL = URL.create(
    drivername=os.getenv("PSQL_DRIVERNAME"),
    username=os.getenv("PSQL_USERNAME"),
    password=os.getenv("PSQL_PASSWORD"),
    host=os.getenv("PSQL_HOST"),
    port=os.getenv("PSQL_PORT"),
    database=os.getenv("PSQL_DATABASE")
)
engine = create_engine(DATABASE_URL, echo=True)

Session = sessionmaker(bind=engine)
session = Session()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

def to_dict(model):
    """Convert SQLAlchemy model instance to dictionary, ignoring internal attributes."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns  if column.name not in ["uid", "unique_id"]}

@app.get("/")
def root():
    return JSONResponse(content={"Message" : "Hello, World!"}, status_code=200)

@app.get("/login")
def login(unique_id: str):
    row = session.query(Login).filter(Login.unique_id == unique_id).first()
    
    if row:
        return JSONResponse(content={
            "Message": "Successfully Logged in!",
            "name" : row.name
        }, status_code=200)
    
    else:
        return JSONResponse(content={
            "Error": "User not found. Register first!"
        }, status_code=400)


@app.post("/register")
def register(unique_id: str, name: str):
    row = session.query(Login).filter(Login.unique_id == unique_id).first()
    print(row)
    if row:
        return JSONResponse(content={
            "Message": f"Hello {row.name}"
        }, status_code=200)
    
    else:
        user = Login(unique_id, name)
        session.add(user)
        session.commit()
        return JSONResponse(content={
            "Message": "Successfully Registered!",
            "name" : user.name
        }, status_code=200)

@app.post("/update-details")
async def update_details(request: Request):
    data = await request.json()
    unique_id = data['unique_id']
    content = data['content']
    content['personal_details']['unique_id'] = unique_id
    list_keys = ['education', 'work_experience', 'projects']
    for key in list_keys:
        for entry in content[key]:
            entry['uid'] = str(uuid.uuid1().int)
            entry['unique_id'] = unique_id
    tmp = content['skills']
    del content['skills']
    content['skills'] = {'unique_id': unique_id, 'skills': tmp}
    tables = {
        "personal_details" : Personal_Details,
        "education" : Education_Details,
        "work_experience" : Work_Details,
        "projects" : Project_Details,
        "skills" : Skills
              }
    for table in tables.values():
        stmt = delete(table).where(table.unique_id == unique_id)
        session.execute(stmt)
    session.commit()
    for ck, cv in content.items():
        if type(cv) == list:
            for item in cv:
                row =  tables[ck](**item)
                session.add(row)
        else:
            row =  tables[ck](**cv)
            session.add(row)
    session.commit()

@app.get("/load-details")
def load_details(unique_id: str):
    tables = {
        "personal_details" : Personal_Details,
        "education" : Education_Details,
        "work_experience" : Work_Details,
        "projects" : Project_Details,
        "skills" : Skills
              }
    data = {}
    for tablek, tablev in tables.items():
        if tablek in ["personal_details", "skills"]:
            results = session.query(tablev).filter(tablev.unique_id == unique_id).first()
            results_dict = to_dict(results) if results else None
        else:
            results = session.query(tablev).filter(tablev.unique_id == unique_id).all()
            results_dict = [to_dict(result) for result in results]
        data[tablek] = results_dict
        with open("data.json", "w") as f:
            json.dump(data, f)
    return JSONResponse(content=data, status_code=200)

class ResumeRequest(BaseModel):
    content: Dict

def delete_files(directory: str, base_name: str):
    pattern = os.path.join(directory, f"{base_name}.*")
    files_to_delete = glob.glob(pattern)

    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")

@app.post("/generate-resume")
async def generate_resume(content: dict, background_tasks: BackgroundTasks):
    rand_uuid = str(uuid.uuid1().int)
    directory = "resume/"
    await generate_latex(content['data'], rand_uuid)
    background_tasks.add_task(delete_files, directory, rand_uuid)
    return FileResponse(path=directory + rand_uuid + ".pdf",
                        filename=f"resume_{rand_uuid}.pdf",
                        media_type="application/pdf")

@app.post("/ai-resume-enhance")
async def ai_resume_enhance(request:Request):
    data = await request.json()
    content = data['content']
    print()