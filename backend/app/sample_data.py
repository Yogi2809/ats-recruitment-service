from .documents import extract_paste
from .models import Candidate, JobDescription, Workspace


def sample_workspace() -> Workspace:
    jds = [
        JobDescription(
            "data-engineer",
            "Senior Data Engineer",
            ["Python", "SQL", "Airflow", "Data Pipelines"],
            ["AWS"],
            extract_paste(
                "Senior Data Engineer\nRequired: Python, SQL, Airflow, data pipelines. "
                "Build reliable batch and streaming data workflows.\nPreferred: AWS cloud experience."
            ),
            reviewed_at="synthetic-sample",
        ),
        JobDescription(
            "fullstack",
            "Full Stack Engineer",
            ["React", "TypeScript", "FastAPI", "PostgreSQL"],
            ["Docker"],
            extract_paste(
                "Full Stack Engineer\nRequired: React, TypeScript, FastAPI, PostgreSQL. "
                "Deliver accessible web applications and APIs.\nPreferred: Docker."
            ),
            reviewed_at="synthetic-sample",
        ),
    ]
    candidates = [
        Candidate("maya", "Maya Shah", extract_paste(
            "Maya Shah — synthetic candidate\nBuilt Python data pipelines using PostgreSQL and SQL. "
            "Designed and maintained Airflow DAGs for scheduled ingestion. "
            "Deployed workloads on AWS S3 and EC2."
        )),
        Candidate("arjun", "Arjun Rao", extract_paste(
            "Arjun Rao — synthetic candidate\nDeveloped Python ETL and SQL reporting pipelines. "
            "Used AWS S3 for data storage."
        )),
        Candidate("neha", "Neha Iyer", extract_paste(
            "Neha Iyer — synthetic candidate\nBuilt Python services and PostgreSQL databases. "
            "Created React dashboards for analysts."
        )),
        Candidate("samira", "Samira Khan", extract_paste(
            "Samira Khan — synthetic candidate\nBuilt React and TypeScript interfaces connected to FastAPI services. "
            "Used PostgreSQL and Docker for local development."
        )),
        Candidate("dev", "Dev Mehta", extract_paste(
            "Dev Mehta — synthetic candidate\nDeveloped React and TypeScript applications with PostgreSQL. "
            "Built Python data APIs and worked with Docker."
        )),
        Candidate("lena", "Lena Park", extract_paste(
            "Lena Park — synthetic candidate\nCreated TypeScript user interfaces and FastAPI backend services. "
            "Worked with SQL databases and accessible design."
        )),
    ]
    recruitment = [
        {"candidate_id": "maya", "stage": "Technical interview", "assessment": "No assessment assigned"},
        {"candidate_id": "arjun", "stage": "Recruiter screen", "assessment": "Data exercise pending"},
        {"candidate_id": "neha", "stage": "Application review", "assessment": "No assessment assigned"},
    ]
    return Workspace(jds, candidates, "data-engineer", recruitment)
