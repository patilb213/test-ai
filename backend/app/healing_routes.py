
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from .healing_approvals import (
    get_approval_requests,
    get_approval_request,
    decide_approval,
)


router = APIRouter(
    prefix="/api/healing",
    tags=["Healing Approvals"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/requests")
def list_requests(
    status: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    if status and status.upper() not in (
        "PENDING",
        "APPROVED",
        "REJECTED",
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid status filter.",
        )

    return {
        "requests": get_approval_requests(
            current_user,
            status,
        )
    }


@router.get("/requests/{request_id}")
def read_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = get_approval_request(
        request_id,
        current_user,
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    return request


@router.post("/requests/{request_id}/approve")
def approve_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = decide_approval(
        request_id,
        "APPROVED",
        current_user,
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Pending approval request not found.",
        )

    return request


@router.post("/requests/{request_id}/reject")
def reject_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = decide_approval(
        request_id,
        "REJECTED",
        current_user,
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Pending approval request not found.",
        )

    return request
