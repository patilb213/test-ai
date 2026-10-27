
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .auth import get_current_user
from .database import projects_collection


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
    dependencies=[Depends(get_current_user)],
)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_url: str = Field(min_length=1, max_length=2048)
    description: str = Field(default="", max_length=3000)


def validate_target_url(value: str) -> str:
    value = value.strip()

    try:
        parsed = urlsplit(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid target URL.",
        )

    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise HTTPException(
            status_code=422,
            detail="Enter a valid HTTP or HTTPS target URL.",
        )

    return value


def serialize_project(project: dict) -> dict:
    return {
        "id": str(project["_id"]),
        "name": project.get("name", ""),
        "target_url": project.get("target_url", ""),
        "description": project.get("description", ""),
    }


@router.post("")
def create_project(
    name: str = Query(min_length=1, max_length=200),
    target_url: str = Query(min_length=1, max_length=2048),
    description: str = Query(default="", max_length=3000),
    current_user: dict = Depends(get_current_user),
):
    """
    Supports the existing frontend's query-parameter format.
    """

    clean_name = name.strip()

    if not clean_name:
        raise HTTPException(
            status_code=422,
            detail="Project name cannot be empty.",
        )

    document = {
        "name": clean_name,
        "target_url": validate_target_url(target_url),
        "description": description.strip(),
        "owner_id": current_user["id"],
        "created_at": datetime.now(timezone.utc),
    }

    result = projects_collection.insert_one(document)

    document["_id"] = result.inserted_id

    return {
        "message": "Project created successfully",
        "project": serialize_project(document),
    }


@router.get("")
def get_projects(
    current_user: dict = Depends(get_current_user),
):
    projects = [
        serialize_project(project)
        for project in projects_collection.find(
            {"owner_id": current_user["id"]}
        ).sort("created_at", -1)
    ]

    return {
        "projects": projects,
    }
