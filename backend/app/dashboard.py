from fastapi import APIRouter

from .database import (
    projects_collection,
    test_cases_collection,
    test_runs_collection,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/stats")
def get_dashboard_stats():
    """
    Return overall Test AI dashboard statistics.
    """

    total_projects = projects_collection.count_documents({})
    total_tests = test_cases_collection.count_documents({})
    total_runs = test_runs_collection.count_documents({})

    passed_runs = test_runs_collection.count_documents({
        "status": "PASS"
    })

    healed_runs = test_runs_collection.count_documents({
        "status": "HEALED"
    })

    failed_runs = test_runs_collection.count_documents({
        "status": "FAIL"
    })

    return {
        "total_projects": total_projects,
        "total_tests": total_tests,
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "healed_runs": healed_runs,
        "failed_runs": failed_runs,
    }