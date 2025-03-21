from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv
load_dotenv()


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

class Login(Base):
    __tablename__ = "login"
    unique_id = Column("unique_id", String, primary_key=True)
    name = Column("name", String)

    def __init__(self, unique_id, name):
        self.unique_id = unique_id
        self.name = name
    
    def __repr__(self):
        return f"{self.unique_id}, {self.name}"

class Personal_Details(Base):
    __tablename__ = "personal"
    unique_id = unique_id = Column("unique_id", String, primary_key=True)
    first_name = Column("first_name", String)
    last_name = Column("last_name", String)
    email = Column("email", String)
    phone = Column("phone", String)
    linkedin = Column("linkedin", Text)
    github = Column("github", Text)

    def __init__(self, unique_id, first_name, last_name, email, phone, linkedin, github):
        self.unique_id = unique_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.linkedin = linkedin
        self.github  = github
    
    def __repr__(self):
        return f"{self.unique_id}, {self.first_name}, {self.last_name}, {self.email}, {self.phone}, {self.linkedin}, {self.github}"
    
class Education_Details(Base):
    __tablename__ = "education"
    uid = Column("uid", String, primary_key=True)
    unique_id = Column("unique_id", String)
    university = Column("university", Text)
    degree = Column("degree", Text)
    start_year = Column("start_year", Integer)
    graduation_year = Column("graduation_year", Integer)
    gpa = Column("gpa", Float)
    description = Column("description", Text)

    def __init__(self, uid, unique_id, university, degree, start_year, graduation_year, gpa, description):
        self.uid = uid
        self.unique_id = unique_id
        self.university = university
        self.degree = degree
        self.start_year = start_year
        self.graduation_year = graduation_year
        self.gpa = gpa
        self.description = description
    
    def __repr__(self):
        return f"{self.unique_id}, {self.university}, {self.degree}, {self.start_year}, {self.graduation_year}, {self.gpa} {self.description}"

class Work_Details(Base):
    __tablename__ = "work"
    uid = Column("uid", String, primary_key=True)
    unique_id = Column("unique_id", String)
    company = Column("company", Text)
    location = Column("location", Text)
    job_title = Column("job_title", Text)
    start_year = Column("start_year", Integer)
    end_year = Column("end_year", Integer)
    work_desc = Column("work_desc", Text)

    def __init__(self, uid, unique_id, company, location, job_title, start_year, end_year, work_desc):
        self.uid = uid
        self.unique_id = unique_id
        self.company = company
        self.location = location
        self.job_title = job_title
        self.start_year = start_year
        self.end_year = end_year
        self.work_desc = work_desc
    
    def __repr__(self):
        return f"{self.unique_id}, {self.company}, {self.location}, {self.job_title}, {self.start_year}, {self.end_year}, {self.work_desc}"

class Project_Details(Base):
    __tablename__ = "project"
    uid = Column("uid", String, primary_key=True)
    unique_id = Column("unique_id", String)
    project_name = Column("project_name", String)
    project_tech = Column("project_tech", Text)
    project_link = Column("project_link", Text)
    project_desc = Column("project_desc", Text)

    def __init__(self, uid, unique_id, project_name, project_tech, project_link, project_desc):
        self.uid = uid
        self.unique_id = unique_id
        self.project_name = project_name
        self.project_tech = project_tech
        self.project_link = project_link
        self.project_desc = project_desc
    
    def __repr__(self):
        return f"{self.unique_id}, {self.name}, {self.project_tech}, {self.project_link}, {self.project_desc}"

class Skills(Base):
    __tablename__ = "skills"
    unique_id = Column("unique_id", String, primary_key=True)
    skills = Column("skills", ARRAY(String))

    def __init__(self, unique_id, skills):
        self.unique_id = unique_id
        self.skills = skills

    def __repr__(self):
        return f"{self.unique_id}, {self.skills}"


Base.metadata.create_all(bind=engine)