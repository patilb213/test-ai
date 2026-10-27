
from datetime import datetime, timezone
from urllib.parse import urlsplit

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

from .auth import get_current_user
from .database import (
    projects_collection,
    test_cases_collection,
    test_runs_collection,
)
from .runner import run_test


# ============================================================
# TEST AI — SECURE TEST CASE MANAGEMENT
# ============================================================

router = APIRouter(
    prefix="/api/tests",
    tags=["Test Cases"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class TestCaseCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=1, max_length=200)
    target_url: str = Field(min_length=1, max_length=2048)


class TestStepsUpdate(BaseModel):
    steps: list[dict] = Field(default_factory=list)


class VerificationCreate(BaseModel):
    verifications: list[dict] = Field(default_factory=list)


# ============================================================
# HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc)


def get_object_id(value: str):
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=400,
            detail="Invalid ID",
        )

    return ObjectId(value)


def validate_target_url(value: str):
    value = value.strip()

    try:
        parsed = urlsplit(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid target URL",
        )

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise HTTPException(
            status_code=422,
            detail="A valid HTTP or HTTPS URL is required",
        )

    return value


def serialize_test(test_case):
    return {
        "id": str(test_case["_id"]),
        "project_id": str(test_case["project_id"]),
        "name": test_case.get("name", ""),
        "target_url": test_case.get("target_url", ""),
        "steps": test_case.get("steps", []),
        "verifications": test_case.get("verifications", []),
        "created_at": test_case.get("created_at"),
        "updated_at": test_case.get("updated_at"),
    }


def get_owned_project(project_id, current_user):
    object_id = get_object_id(str(project_id))

    project = projects_collection.find_one({
        "_id": object_id,
        "owner_id": current_user["id"],
    })

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


def get_owned_test(test_id, current_user):
    object_id = get_object_id(test_id)

    test_case = test_cases_collection.find_one({
        "_id": object_id,
    })

    if test_case is None:
        raise HTTPException(
            status_code=404,
            detail="Test case not found",
        )

    get_owned_project(
        test_case["project_id"],
        current_user,
    )

    return test_case


# ============================================================
# CREATE TEST CASE
# ============================================================

@router.post("")
def create_test_case(
    data: TestCaseCreate,
    current_user: dict = Depends(get_current_user),
):
    project = get_owned_project(
        data.project_id,
        current_user,
    )

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Test name cannot be empty",
        )

    target_url = validate_target_url(data.target_url)

    document = {
        "project_id": project["_id"],
        "name": name,
        "target_url": target_url,
        "steps": [],
        "verifications": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    result = test_cases_collection.insert_one(document)

    document["_id"] = result.inserted_id

    return {
        "message": "Test case created successfully",
        "test": serialize_test(document),
    }


# ============================================================
# LIST TEST CASES
# ============================================================

@router.get("")
def get_test_cases(
    project_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    if project_id:
        project = get_owned_project(
            project_id,
            current_user,
        )

        project_ids = [project["_id"]]

    else:
        project_ids = [
            project["_id"]
            for project in projects_collection.find(
                {"owner_id": current_user["id"]},
                {"_id": 1},
            )
        ]

    if not project_ids:
        return {
            "tests": [],
            "total": 0,
        }

    project_id_strings = [
        str(project_id)
        for project_id in project_ids
    ]

    query = {
        "project_id": {
            "$in": project_ids + project_id_strings
        }
    }

    tests = [
        serialize_test(item)
        for item in test_cases_collection
        .find(query)
        .sort("created_at", -1)
    ]

    return {
        "tests": tests,
        "total": len(tests),
    }


# ============================================================
# GET TEST CASE
# ============================================================

@router.get("/{test_id}")
def get_test_case(
    test_id: str,
    current_user: dict = Depends(get_current_user),
):
    test_case = get_owned_test(
        test_id,
        current_user,
    )

    return {
        "test": serialize_test(test_case),
    }


# ============================================================
# UPDATE RECORDED STEPS
# ============================================================

@router.put("/{test_id}/steps")
def update_test_steps(
    test_id: str,
    data: TestStepsUpdate,
    current_user: dict = Depends(get_current_user),
):
    test_case = get_owned_test(
        test_id,
        current_user,
    )

    test_cases_collection.update_one(
        {"_id": test_case["_id"]},
        {
            "$set": {
                "steps": data.steps,
                "updated_at": utc_now(),
            }
        },
    )

    return {
        "message": "Test steps updated successfully",
    }


# ============================================================
# UPDATE EXPECTED RESULTS
# ============================================================

@router.put("/{test_id}/verifications")
def update_test_verifications(
    test_id: str,
    data: VerificationCreate,
    current_user: dict = Depends(get_current_user),
):
    test_case = get_owned_test(
        test_id,
        current_user,
    )

    # An empty list is allowed so that users can remove
    # previously configured verifications.
    test_cases_collection.update_one(
        {"_id": test_case["_id"]},
        {
            "$set": {
                "verifications": data.verifications,
                "updated_at": utc_now(),
            }
        },
    )

    return {
        "message": "Expected results saved successfully",
    }


# ============================================================
# EXECUTE TEST CASE
# ============================================================

@router.post("/{test_id}/run")
def run_test_case(
    test_id: str,
    current_user: dict = Depends(get_current_user),
):
    test_case = get_owned_test(
        test_id,
        current_user,
    )

    if not test_case.get("steps"):
        raise HTTPException(
            status_code=400,
            detail="Test case has no recorded steps",
        )

    if not test_case.get("verifications"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Test case has no expected results. "
                "Add at least one verification before running."
            ),
        )

    # Ownership is verified before calling the existing
    # Playwright runner.
    #
    # The runner must still receive network isolation,
    # URL restrictions and execution limits before
    # this service is exposed publicly.

    try:
        # TEST_AI_APPROVED_STEP_TARGETS_V1
        # Apply only account-owned, approved suggestions.
        # Never modify the stored recording.
        from copy import deepcopy
        from .healing import locator_to_string

        execution_test = deepcopy(test_case)
        execution_steps = execution_test.get("steps", [])

        approvals = list(
            test_runs_collection.database["healing_approvals"]
            .find({
                "test_case_id": str(test_case["_id"]),
                "owner_id": current_user["id"],
                "status": "APPROVED",
                "source": "step",
            })
            .sort("decided_at", -1)
        )

        applied_steps = set()

        for approval in approvals:
            step_number = approval.get("step")
            replacement = approval.get("replacement_target")

            if (
                type(step_number) is not int
                or not 1 <= step_number <= len(execution_steps)
                or step_number in applied_steps
                or not isinstance(replacement, dict)
            ):
                continue

            # Only allow stable, explicit target properties.
            allowed = {
                "role", "name", "label", "placeholder",
                "id", "nameAttr", "text", "css", "tag",
            }

            if (
                not replacement
                or any(key not in allowed for key in replacement)
                or any(
                    not isinstance(value, str)
                    or not value.strip()
                    or len(value) > 500
                    for value in replacement.values()
                )
            ):
                continue

            step = execution_steps[step_number - 1]
            if not isinstance(step, dict):
                continue

            original = step.get("target")

            if not isinstance(original, dict):
                continue

            approved_action = approval.get("action")

            if (
                not isinstance(approved_action, str)
                or approved_action.strip().lower()
                != str(step.get("action", "")).strip().lower()
            ):
                continue

            # A recommendation for an older recording must not
            # silently replace a subsequently edited target.
            if (
                locator_to_string(original)
                != approval.get("original_locator")
            ):
                continue

            step["target"] = replacement
            applied_steps.add(step_number)

        test_case = execution_test
        run = run_test(test_case)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Test execution failed. "
                "Check the backend logs for details."
            ),
        )

    return {
        "message": "Test execution completed",
        "run": run,
    }


# ============================================================
# DELETE TEST CASE
# ============================================================

@router.delete("/{test_id}")
def delete_test_case(
    test_id: str,
    current_user: dict = Depends(get_current_user),
):
    test_case = get_owned_test(
        test_id,
        current_user,
    )

    object_id = test_case["_id"]

    # Remove run records associated with this test.
    # This preserves the previous API's delete behavior.
    test_runs_collection.delete_many({
        "$or": [
            {"test_case_id": str(object_id)},
            {"test_case_id": object_id},
        ]
    })

    test_cases_collection.delete_one({
        "_id": object_id,
    })

    return {
        "message": "Test case deleted successfully",
    }
