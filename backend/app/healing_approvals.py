
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from .database import (
    projects_collection,
    test_cases_collection,
    test_runs_collection,
)


def utc_now():
    return datetime.now(timezone.utc)


def approval_collection():
    return test_runs_collection.database["healing_approvals"]


def serialize_request(document):
    if not document:
        return None

    result = dict(document)
    result["id"] = str(result.pop("_id"))

    for key in ("created_at", "updated_at", "decided_at"):
        if isinstance(result.get(key), datetime):
            result[key] = result[key].isoformat()

    if result.get("test_case_id") is not None:
        result["test_case_id"] = str(result["test_case_id"])

    if result.get("project_id") is not None:
        result["project_id"] = str(result["project_id"])

    return result


def owned_tests(current_user):
    projects = list(
        projects_collection.find(
            {"owner_id": current_user["id"]},
            {"_id": 1},
        )
    )

    project_ids = [item["_id"] for item in projects]

    if not project_ids:
        return {}

    project_keys = project_ids + [
        str(item) for item in project_ids
    ]

    tests = test_cases_collection.find(
        {"project_id": {"$in": project_keys}},
        {"_id": 1, "project_id": 1, "name": 1},
    )

    return {
        str(test["_id"]): test
        for test in tests
    }


def sync_approval_requests(current_user):
    """
    Discover review-required events belonging to the user.
    Existing approval decisions are never overwritten.
    """

    tests = owned_tests(current_user)

    if not tests:
        return 0

    test_keys = []

    for test_id in tests:
        test_keys.extend([test_id, ObjectId(test_id)])

    runs = test_runs_collection.find(
        {
            "test_case_id": {"$in": test_keys},
            "approval_required_count": {"$gt": 0},
        },
        {
            "test_case_id": 1,
            "test_name": 1,
            "healing_history": 1,
        },
    )

    collection = approval_collection()
    created = 0

    for run in runs:
        test_id = str(run.get("test_case_id"))
        test = tests.get(test_id)

        if not test:
            continue

        for index, event in enumerate(
            run.get("healing_history") or []
        ):
            if not isinstance(event, dict):
                continue

            if event.get("resolution_status") != "REVIEW_REQUIRED":
                continue

            event_key = f"{run['_id']}:{index}"

            document = {
                "event_key": event_key,
                "run_id": str(run["_id"]),
                "test_case_id": test_id,
                "project_id": str(test["project_id"]),
                "test_name": run.get("test_name") or test.get("name"),
                "owner_id": current_user["id"],
                "source": event.get("source"),
                "step": event.get("step"),
                "action": event.get("action"),
                "verification": event.get("verification"),
                "original_locator": event.get("original_locator"),
                "replacement_locator": event.get("replacement_locator"),
                "confidence": event.get("confidence"),
                "reason": event.get("reason"),
                "replacement_target": event.get("replacement_target"),
                "ai_model": event.get("ai_model"),
                "ai_similarity": event.get("ai_similarity"),
                "ai_margin": event.get("ai_margin"),
                "healing_decision": event.get("healing_decision"),
                "healing_decision_reason": event.get(
                    "healing_decision_reason"
                ),
                "status": "PENDING",
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }

            result = collection.update_one(
                {"event_key": event_key},
                {"$setOnInsert": document},
                upsert=True,
            )

            if result.upserted_id:
                created += 1

    return created


def get_approval_requests(current_user, status=None):
    sync_approval_requests(current_user)

    tests = owned_tests(current_user)

    if not tests:
        return []

    query = {
        "test_case_id": {"$in": list(tests.keys())}
    }

    if status:
        query["status"] = status.upper()

    documents = approval_collection().find(query).sort(
        "created_at", -1
    ).limit(500)

    return [
        serialize_request(doc)
        for doc in documents
        if str(doc.get("test_case_id")) in tests
    ]


def get_approval_request(request_id, current_user):
    if not ObjectId.is_valid(request_id):
        return None

    tests = owned_tests(current_user)

    document = approval_collection().find_one({
        "_id": ObjectId(request_id),
        "test_case_id": {"$in": list(tests.keys())},
    })

    return serialize_request(document)


def decide_approval(request_id, decision, current_user):
    if not ObjectId.is_valid(request_id):
        return None

    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Invalid approval decision.")

    tests = owned_tests(current_user)

    document = approval_collection().find_one_and_update(
        {
            "_id": ObjectId(request_id),
            "test_case_id": {"$in": list(tests.keys())},
            "status": "PENDING",
        },
        {
            "$set": {
                "status": decision,
                "reviewed_by": current_user["name"],
                "reviewed_by_user_id": current_user["id"],
                "decided_at": utc_now(),
                "updated_at": utc_now(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    return serialize_request(document)
