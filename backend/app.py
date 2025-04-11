import os
import uuid
import glob
import re
from schemas import *
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, delete, and_
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from resume import generate_latex
from typing import Dict
from pydantic import BaseModel
from openai import OpenAI
import requests
from fpdf import FPDF

from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

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
        # with open("data.json", "w") as f:
        #     json.dump(data, f)
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


@app.post("/add-job")
async def add_job(request:Request):
    data = await request.json()
    unique_id = data['unique_id']
    job_name = data['job_name']
    job_uuid = str(uuid.uuid1().int)
    job = UserJobs(job_uuid, unique_id, job_name)
    session.add(job)
    session.commit()
    return JSONResponse(content={
        "Message": "Successfully Added Job!",
        "Job" : f"{job.job_uuid} {job_name}"
    }, status_code=200)

@app.post("/remove-job")
async def remove_job(request:Request):
    data = await request.json()
    unique_id = data['unique_id']
    job_name = data['job_name']
    tab = session.query(UserJobs).filter(and_(
            UserJobs.job_name == job_name,
            UserJobs.unique_id == unique_id
        )).first()
    session.delete(tab)
    tab = session.query(Jobs).filter(and_(
            Jobs.job_name == job_name,
            Jobs.unique_id == unique_id
        )).first()
    session.delete(tab)
    session.commit()
    return JSONResponse(content={
        "Message": "Successfully Deleted Job!",
        "Job" : f"{job_name}"
    }, status_code=200)


@app.get("/load-jobs")
def load_jobs(unique_id: str):
    row = session.query(UserJobs.job_name).filter(UserJobs.unique_id == unique_id).all()
    if not row:
        return JSONResponse(content={"jobs" : []})
    job_names = [job[0] for job in row]
    print(job_names)
    return JSONResponse(content={"jobs" : job_names})

def get_job_uuid(unique_id, job_name):
    row = session.query(UserJobs.job_id).filter(and_(
                UserJobs.job_name == job_name,
                UserJobs.unique_id == unique_id
            )).first()
    return row[0]

@app.get("/get-job-uuid")
async def get_job_id(request: Request):
    data = await request.json()
    unique_id = data['unique_id']
    job_name = data['job_name']
    row = session.query(UserJobs.job_id).filter(and_(
                UserJobs.job_name == job_name,
                UserJobs.unique_id == unique_id
            )).first()
    return JSONResponse(content={"job_uuid" : row[0]})

@app.post("/fetch-description")
async def fetch_description(request: Request):
    data = await request.json()
    unique_id = data['unique_id']
    job_name = data['job_name']
    job_url = data['job_url']
    job_uuid = get_job_uuid(unique_id, job_name)
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(job_url, headers=headers)
    content = response.text
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "developer",
                "content" : "You are a Bot that scrapes a job portal website to get the job description. You are given the HTML scraped content of a job portal. Write the description of the job in around 200 words without bullet points in one paragraph, preferably in point of view of the employer. The response must only contain the relevant text about the responsibilities and requirements of the role mentioned in the HTML."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        max_tokens=512,
    )
    desc = completion.choices[0].message.content
    
    job = Jobs(job_uuid, unique_id, job_name, job_url, desc)
    session.add(job)
    session.commit()
    return JSONResponse(content={
        "Message": "Successfully Added Job!",
        "Description" : f"{desc}"
    }, status_code=200)

@app.get("/get-job-details")
async def get_job_details(request: Request):
    data = await request.json()
    unique_id = data['unique_id']
    job_name = data['job_name']
    job_uuid = get_job_uuid(unique_id, job_name)
    row = session.query(Jobs).filter(and_(
                Jobs.job_id == job_uuid,
                Jobs.job_name == job_name,
                Jobs.unique_id == unique_id
            )).first()
    if not row:
        return JSONResponse(content={"job_url" : "", "description" : ""})
    return JSONResponse(content={"job_url" : row.job_url, "description" : row.job_desc})


@app.post("/generate-tailored-resume")
async def generate_tailored_resume(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    content = data['data']
    job_desc = data['job_desc']
    fields = [['education', 'description'], ['work_experience', 'work_desc'], ['projects', 'project_desc']]

    new_json = {
        'personal_details' : content['personal_details']
    }
    
    for field, key in fields:
        value = content[field]
        new_json[field] = []
        
        for v in value:
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "developer",
                        "content" : f"""
                        You are a Resume Bot that tailors the resume details according to a job description. You are given a job description and a particular section from the resume. 
                        Rewrite the Resume section to suit it for a professional career resume. You should only return the relevant rewritten description as response without any extra words or notes.
                        Each line in the rewritten description should be in separate lines without any bullets. Do not add any extra new lines in-between.
                        Only rewrite the given lines of the Resume section. Do not add irrelevant information that is not present in the Resume Section."""
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Resume section: {v[key].encode('utf-8', 'ignore').decode('utf-8')}
                        Job Description: {job_desc}"""
                    }
                ],
                max_tokens=512,
            )
            
            response = completion.choices[0].message.content
            response = re.sub(r'\n+', '\n', response)
            response = response.rstrip("\n")
            v[key] = response
            new_json[field].append(v)
            
    new_json['skills'] = content['skills']

    return await generate_resume({'data': new_json}, background_tasks)

def create_pdf_from_string(text: str, filename: str):
    pdf = FPDF()
    pdf.add_font("NotoSans", style="", fname="./fonts/NotoSans-VariableFont_wdth,wght.ttf", uni=True)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("NotoSans", size=10)
    pdf.multi_cell(w=0, h=7, txt=text)
    pdf.output(filename)


@app.post("/generate-cover-letter")
async def generate_tailored_resume(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    resume = data['resume']
    job_desc = data['job_desc']
    rand_uuid = str(uuid.uuid1().int)
    directory = "cover-letter/"
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "developer",
                "content" : f'''You are a Cover Letter generation bot that tailors the cover letter according to a job description. You are given the JSON content of a resume.
                    Write a cover letter at around 250 words by using the resume details such that the it is tailored for the responsibilities and requirements of the role mentioned in the following Job description.
                    Return only the letter - No extra words. Paraphrase the words so that it does not seem AI-generated from the Job Description.
                    You may add my name and contact details at the top. Do Not Add any Address or Date in the letter, it is only an electronic document. Only add name at the end of the letter.'''
            },
            {
                "role": "user",
                "content": f'''
                    Resume JSON: {resume}
                    Job Description: {job_desc}'''
            }
        ],
        max_tokens=1024,
    )

    response = completion.choices[0].message.content
    create_pdf_from_string(response, f"{directory}{rand_uuid}.pdf")
    background_tasks.add_task(delete_files, directory, rand_uuid)
    return FileResponse(path=directory + rand_uuid + ".pdf",
                        filename=f"{rand_uuid}.pdf",
                        media_type="application/pdf")

