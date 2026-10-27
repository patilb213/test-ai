
from datetime import datetime
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .auth import get_current_user
from .database import (
    projects_collection,
    test_cases_collection,
    test_runs_collection,
)


router = APIRouter(
    prefix="/api/runs",
    tags=["Test Runs"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# HELPERS
# ============================================================

def valid_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=400,
            detail="Invalid ID",
        )
    return ObjectId(value)


def serialize_datetime(value):
    from datetime import datetime, timezone

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    return value


def evidence_url_from_path(path_value):
    if not path_value:
        return None

    value = str(path_value)

    if value.startswith("/evidence/"):
        return value

    filename = Path(value.replace("\\", "/")).name

    if not filename:
        return None

    # These URLs are retained for compatibility with
    # existing reports. Public evidence serving remains
    # disabled until authenticated retrieval is implemented.
    return f"/evidence/{filename}"


def normalize_status(item: dict) -> str:
    status = str(item.get("status") or "").upper()

    if status in {"PASS", "PASSED", "SUCCESS"}:
        return "PASS"

    if status == "HEALED":
        return "HEALED"

    if status in {"SKIPPED", "PENDING"}:
        return "SKIPPED"

    if status in {"FAIL", "FAILED", "ERROR"}:
        return "FAIL"

    if item.get("passed") is True:
        return "HEALED" if item.get("healed") else "PASS"

    return "FAIL"


def normalize_step(step):
    if not isinstance(step, dict):
        return {
            "status": "FAIL",
            "message": str(step),
        }

    normalized = dict(step)
    normalized["status"] = normalize_status(step)

    screenshot = (
        step.get("screenshot")
        or step.get("screenshot_path")
        or step.get("evidence_path")
    )

    if screenshot:
        normalized["screenshot"] = evidence_url_from_path(
            screenshot
        )

    for key in ("started_at", "finished_at"):
        if key in normalized:
            normalized[key] = serialize_datetime(
                normalized[key]
            )

    healing = step.get("healing")

    if isinstance(healing, dict):
        normalized["healing"] = {
            "healed": bool(healing.get("healed", True)),
            "original_locator": healing.get("original_locator"),
            "replacement_locator": healing.get("replacement_locator"),
            "confidence": healing.get("confidence"),
            "reason": healing.get("reason"),
        }

    return normalized


def normalize_verification(verification):
    if not isinstance(verification, dict):
        return {
            "status": "FAIL",
            "passed": False,
            "message": str(verification),
        }

    normalized = dict(verification)
    normalized["status"] = normalize_status(verification)

    if "passed" not in normalized:
        normalized["passed"] = normalized["status"] in {
            "PASS",
            "HEALED",
        }

    screenshot = (
        verification.get("screenshot")
        or verification.get("screenshot_path")
        or verification.get("evidence_path")
    )

    if screenshot:
        normalized["screenshot"] = evidence_url_from_path(
            screenshot
        )

    for key in ("started_at", "finished_at"):
        if key in normalized:
            normalized[key] = serialize_datetime(
                normalized[key]
            )

    return normalized


def serialize_run(run: dict) -> dict:
    mongo_id = str(run["_id"])

    test_case_id = run.get("test_case_id")

    if test_case_id is not None:
        test_case_id = str(test_case_id)

    steps = [
        normalize_step(step)
        for step in (run.get("steps") or [])
    ]

    verifications = [
        normalize_verification(item)
        for item in (run.get("verifications") or [])
    ]

    evidence = []

    for item in (run.get("evidence") or []):
        if not isinstance(item, dict):
            continue

        copy = dict(item)
        url = copy.get("url")

        if url:
            copy["url"] = evidence_url_from_path(url)
            evidence.append(copy)

    for index, step in enumerate(steps, start=1):
        screenshot = step.get("screenshot")

        if screenshot:
            evidence.append({
                "type": "step_screenshot",
                "step": index,
                "url": screenshot,
                "name": Path(screenshot).name,
            })

    for index, verification in enumerate(
        verifications,
        start=1,
    ):
        screenshot = verification.get("screenshot")

        if screenshot:
            evidence.append({
                "type": "verification_screenshot",
                "verification": index,
                "url": screenshot,
                "name": Path(screenshot).name,
            })

    unique_evidence = []
    seen = set()

    for item in evidence:
        url = item.get("url")

        if not url or url in seen:
            continue

        seen.add(url)
        unique_evidence.append(item)

    healing_details = run.get("healing_details") or []

    healing_count = run.get("healing_count")

    if healing_count is None:
        healing_count = len(healing_details)

    healed = bool(
        run.get("healed", healing_count > 0)
    )

    return {
        "id": mongo_id,
        "test_run_id": run.get("run_id") or mongo_id,
        "test_case_id": test_case_id,
        "test_name": run.get("test_name", "Unnamed Test"),
        "target_url": run.get("target_url", ""),
        "status": normalize_status(run),
        "message": run.get("message", ""),
        "started_at": serialize_datetime(
            run.get("started_at")
        ),
        "finished_at": serialize_datetime(
            run.get("finished_at")
        ),
        "duration_ms": run.get("duration_ms"),
        "steps": steps,
        "verifications": verifications,
        "evidence": unique_evidence,
        "screenshot": evidence_url_from_path(run.get("screenshot")),
        "healed": healed,
        "healing_count": healing_count,
        "approval_required_count": run.get(
            "approval_required_count", 0
        ),
        "healing_details": healing_details,
        "error": run.get("error"),
        "created_at": serialize_datetime(
            run.get("created_at")
        ),
    }


# ============================================================
# OWNERSHIP
# ============================================================

def find_test_case(test_case_id):
    if not test_case_id:
        return None

    try:
        object_id = ObjectId(str(test_case_id))
    except (ValueError, TypeError):
        return None

    return test_cases_collection.find_one({
        "_id": object_id,
    })


def owned_project_ids(current_user: dict):
    return [
        project["_id"]
        for project in projects_collection.find(
            {"owner_id": current_user["id"]},
            {"_id": 1},
        )
    ]


def owned_test_ids(current_user: dict):
    project_ids = owned_project_ids(current_user)

    if not project_ids:
        return []

    project_keys = project_ids + [
        str(project_id)
        for project_id in project_ids
    ]

    return [
        test["_id"]
        for test in test_cases_collection.find(
            {"project_id": {"$in": project_keys}},
            {"_id": 1},
        )
    ]


def run_query_for_user(current_user: dict):
    test_ids = owned_test_ids(current_user)

    if not test_ids:
        return {"_id": {"$in": []}}

    return {
        "test_case_id": {
            "$in": test_ids + [
                str(test_id)
                for test_id in test_ids
            ]
        }
    }


def require_owned_run(run_id: str, current_user: dict):
    object_id = valid_id(run_id)

    query = run_query_for_user(current_user)
    query["_id"] = object_id

    run = test_runs_collection.find_one(query)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Test run not found",
        )

    return run


def enrich_run(run):
    response = serialize_run(run)

    test_case = find_test_case(
        run.get("test_case_id")
    )

    if test_case:
        response["test"] = {
            "id": str(test_case["_id"]),
            "name": test_case.get("name", ""),
            "target_url": test_case.get("target_url", ""),
        }

        response["test_name"] = test_case.get(
            "name",
            response["test_name"],
        )

        response["target_url"] = test_case.get(
            "target_url",
            response["target_url"],
        )

    return response


# ============================================================
# LIST AUTHORIZED RUNS
# ============================================================

@router.get("")
def get_runs(
    test_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    query = run_query_for_user(current_user)

    if test_id is not None:
        object_id = valid_id(test_id)

        allowed_ids = owned_test_ids(current_user)

        if object_id not in allowed_ids:
            raise HTTPException(
                status_code=404,
                detail="Test case not found",
            )

        query["test_case_id"] = {
            "$in": [object_id, str(object_id)]
        }

    runs = [
        enrich_run(run)
        for run in test_runs_collection
        .find(query)
        .sort("started_at", -1)
        .limit(500)
    ]

    return {
        "runs": runs,
        "total": len(runs),
    }


# ============================================================
# GET AUTHORIZED RUN
# ============================================================

@router.get("/{run_id}")
def get_run(
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    run = require_owned_run(
        run_id,
        current_user,
    )

    return {
        "run": enrich_run(run),
    }



# ============================================================
# SECURE SCREENSHOT EVIDENCE
# ============================================================

@router.get("/{run_id}/evidence/{filename}")
def get_run_evidence(
    run_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    run = require_owned_run(run_id, current_user)

    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "\\" in filename
        or not filename.lower().endswith(".png")
    ):
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    def stored_filename(value):
        if not isinstance(value, str) or not value:
            return None
        return Path(value.replace("\\", "/")).name

    allowed = set()

    def add(value):
        name = stored_filename(value)
        if name:
            allowed.add(name)

    add(run.get("screenshot"))

    for step in run.get("steps") or []:
        if isinstance(step, dict):
            for key in (
                "screenshot",
                "screenshot_path",
                "evidence_path",
            ):
                add(step.get(key))

    for verification in run.get("verifications") or []:
        if isinstance(verification, dict):
            for key in (
                "screenshot",
                "screenshot_path",
                "evidence_path",
            ):
                add(verification.get(key))

    for item in run.get("evidence") or []:
        if isinstance(item, dict):
            for key in (
                "url",
                "screenshot",
                "path",
                "evidence_path",
            ):
                add(item.get(key))

    if filename not in allowed:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    evidence_dir = (
        Path(__file__).resolve().parent.parent / "evidence"
    ).resolve()

    candidate = (evidence_dir / filename).resolve()

    if (
        candidate.parent != evidence_dir
        or not candidate.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    return FileResponse(
        candidate,
        media_type="image/png",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ============================================================
# DELETE AUTHORIZED RUN
# ============================================================

@router.delete("/{run_id}")
def delete_run(
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    run = require_owned_run(
        run_id,
        current_user,
    )

    result = test_runs_collection.delete_one({
        "_id": run["_id"],
    })

    if result.deleted_count != 1:
        raise HTTPException(
            status_code=404,
            detail="Test run not found",
        )

    return {
        "message": "Test run deleted successfully",
    }
