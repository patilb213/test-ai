# ============================================================
# TEST AI - SCRIPTLESS RECORDER API
# ============================================================

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import test_cases_collection

from .browser_recorder import (
    start_browser_recorder,
    stop_browser_recorder,
    browser_recorder_active,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/recorder",
    tags=["Recorder"],
)


# ============================================================
# ACTIVE RECORDING SESSIONS
# ============================================================

recording_sessions: dict[
    str,
    dict[str, Any]
] = {}


# ============================================================
# REQUEST MODELS
# ============================================================

class StartRecordingRequest(BaseModel):
    project_id: str
    name: str
    target_url: str


class RecorderTarget(BaseModel):
    role: str | None = None
    name: str | None = None
    label: str | None = None
    placeholder: str | None = None
    id: str | None = None
    nameAttr: str | None = None
    text: str | None = None
    css: str | None = None
    tag: str | None = None
    containerText: str | None = None
    testId: str | None = None
    type: str | None = None


class RecorderEventRequest(BaseModel):
    action: str

    target: RecorderTarget | None = None

    value: str | None = None

    url: str | None = None

    ms: int | None = None

    timestamp: str | None = None


class StopRecordingRequest(BaseModel):
    save_test: bool = True


# ============================================================
# TIME
# ============================================================

def utc_now():
    return datetime.now(
        timezone.utc
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    text = " ".join(
        str(value).split()
    ).strip()

    if not text:
        return None

    # Prevent huge text blocks from being stored.
    return text[:300]


# ============================================================
# TARGET NORMALIZATION
# ============================================================

def normalize_target(
    target: RecorderTarget | None,
):

    if target is None:
        return None

    raw = target.model_dump()

    normalized = {}

    for key, value in raw.items():

        value = normalize_text(
            value
        )

        if value:
            normalized[key] = value

    if not normalized:
        return None

    return normalized


# ============================================================
# SENSITIVE FIELD DETECTION
# ============================================================

def is_sensitive_target(
    target: dict | None,
):

    if not target:
        return False

    combined = " ".join(
        str(value).lower()
        for value in [
            target.get("name"),
            target.get("label"),
            target.get("placeholder"),
            target.get("id"),
            target.get("nameAttr"),
            target.get("type"),
        ]
        if value
    )

    sensitive_terms = [
        "password",
        "passwd",
        "passcode",
        "secret",
        "token",
        "otp",
        "one-time",
        "cvv",
        "cvc",
        "credit card",
        "card number",
        "security code",
        "ssn",
    ]

    return any(
        term in combined
        for term in sensitive_terms
    )


# ============================================================
# EVENT NORMALIZATION
# ============================================================

def sanitize_event(
    event: RecorderEventRequest,
):
    """
    Convert raw browser recorder events into
    the standard Test AI TestStep format.
    """

    action = (
        event.action
        .strip()
        .lower()
    )

    supported_actions = {
        "navigate",
        "click",
        "input",
        "select",
        "wait",
    }

    if (
        action
        not in supported_actions
    ):

        raise ValueError(
            "Unsupported recorder "
            f"action: {action}"
        )

    step = {
        "action": action
    }

    # ========================================================
    # TARGET
    # ========================================================

    target = normalize_target(
        event.target
    )

    if target:

        step["target"] = target

    # ========================================================
    # URL
    # ========================================================

    if event.url:

        step["url"] = (
            event.url.strip()
        )

    # ========================================================
    # WAIT
    # ========================================================

    if event.ms is not None:

        step["ms"] = max(
            0,
            int(event.ms),
        )

    # ========================================================
    # INPUT / SELECT VALUE
    # ========================================================

    if action == "input" and is_sensitive_target(target):
        step["sensitive"] = True
        step["value"] = ""

    elif event.value is not None:

        value = str(
            event.value
        )

        # Never save password-like values.
        if (
            action == "input"
            and is_sensitive_target(
                target
            )
        ):

            step["value"] = ""

            step["sensitive"] = True

        else:

            step["value"] = value

    return step


# ============================================================
# DUPLICATE EVENT CHECK
# ============================================================

def is_duplicate_event(events, new_step):
    """
    Consolidate consecutive input events.

    Preserve the latest field value while keeping
    intentional repeated clicks unchanged.
    """

    if not events:
        return False

    previous = events[-1]

    previous_action = previous.get("action")
    new_action = new_step.get("action")

    if previous_action != new_action:
        return False

    # Duplicate navigation to the same URL.
    if new_action == "navigate":
        return previous.get("url") == new_step.get("url")

    # Consolidate consecutive edits to the same field.
    # Ignore changing surrounding text and CSS paths when
    # stronger field identifiers are available.
    if new_action == "input":
        old_target = previous.get("target") or {}
        new_target = new_step.get("target") or {}

        def field_identity(target):
            if not isinstance(target, dict):
                return None

            for key in ("testId", "id", "nameAttr"):
                value = target.get(key)
                if value:
                    return (key, str(value))

            role = target.get("role")
            for key in ("label", "placeholder", "name"):
                value = target.get(key)
                if value:
                    return (role, key, str(value))

            css = target.get("css")
            if css:
                return ("css", str(css))

            return None

        old_identity = field_identity(old_target)
        new_identity = field_identity(new_target)

        same_field = (
            old_target == new_target
            or (
                old_identity is not None
                and old_identity == new_identity
                and old_target.get("tag") == new_target.get("tag")
            )
        )

        if same_field:
            if (
                previous.get("sensitive")
                or new_step.get("sensitive")
            ):
                previous["value"] = ""
                previous["sensitive"] = True
            else:
                previous["value"] = new_step.get("value", "")

            # Keep the most recently captured target metadata.
            previous["target"] = new_target
            return True

    # Ignore identical consecutive selection events.
    if new_action == "select":
        return (
            previous.get("target") == new_step.get("target")
            and previous.get("value") == new_step.get("value")
        )

    # Never remove clicks automatically.
    return False


# ============================================================
# ============================================================
# ADD EVENT TO SESSION
# ============================================================

def add_event_to_session(
    session_id: str,
    event_data: dict,
):
    """
    Used internally by browser_recorder.py.

    The tester never calls this manually.
    """

    session = (
        recording_sessions.get(
            session_id
        )
    )

    if not session:
        return False

    if (
        session.get("status")
        != "recording"
    ):
        return False

    try:

        event = (
            RecorderEventRequest(
                **event_data
            )
        )

        step = sanitize_event(
            event
        )

        if is_duplicate_event(
            session["events"],
            step,
        ):

            return False

        session[
            "events"
        ].append(
            step
        )

        return True

    except Exception as error:

        print(
            "Recorder event rejected:",
            error,
        )

        return False


# ============================================================
# SESSION RESPONSE
# ============================================================

def session_response(
    session_id: str,
    session: dict,
):

    started_at = (
        session.get(
            "started_at"
        )
    )

    finished_at = (
        session.get(
            "finished_at"
        )
    )

    return {

        "session_id":
            session_id,

        "project_id":
            session.get(
                "project_id"
            ),

        "name":
            session.get(
                "name"
            ),

        "target_url":
            session.get(
                "target_url"
            ),

        "status":
            session.get(
                "status"
            ),

        "browser_active":
            browser_recorder_active(
                session_id
            ),

        "event_count":
            len(
                session.get(
                    "events",
                    [],
                )
            ),

        "events":
            session.get(
                "events",
                [],
            ),

        "started_at":
            (
                started_at.isoformat()
                if isinstance(
                    started_at,
                    datetime,
                )
                else started_at
            ),

        "finished_at":
            (
                finished_at.isoformat()
                if isinstance(
                    finished_at,
                    datetime,
                )
                else finished_at
            ),
    }


# ============================================================
# START RECORDING
# ============================================================

@router.post("/start")
def start_recording(
    data: StartRecordingRequest,
):

    # ========================================================
    # VALIDATE PROJECT ID
    # ========================================================

    try:

        project_id = ObjectId(
            data.project_id
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid project ID",
        )

    # ========================================================
    # VALIDATE TEST NAME
    # ========================================================

    name = (
        data.name.strip()
    )

    if not name:

        raise HTTPException(
            status_code=400,
            detail=(
                "Test name is required."
            ),
        )

    # ========================================================
    # VALIDATE TARGET URL
    # ========================================================

    target_url = (
        data.target_url.strip()
    )

    if not target_url:

        raise HTTPException(
            status_code=400,
            detail=(
                "Target URL is required."
            ),
        )

    if not (
        target_url.startswith(
            "http://"
        )
        or target_url.startswith(
            "https://"
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Target URL must begin "
                "with http:// or https://"
            ),
        )

    # ========================================================
    # CREATE SESSION
    # ========================================================

    session_id = (
        uuid4().hex
    )

    recording_sessions[
        session_id
    ] = {

        "project_id":
            str(project_id),

        "name":
            name,

        "target_url":
            target_url,

        "events": [],

        "status":
            "recording",

        "started_at":
            utc_now(),

        "finished_at":
            None,
    }

    # ========================================================
    # CALLBACK FOR AUTOMATIC BROWSER EVENTS
    # ========================================================

    def receive_browser_event(
        event,
    ):

        if not isinstance(
            event,
            dict,
        ):
            return

        add_event_to_session(
            session_id,
            event,
        )

    # ========================================================
    # START REAL PLAYWRIGHT BROWSER
    # ========================================================

    try:

        start_browser_recorder(
            session_id=
                session_id,

            target_url=
                target_url,

            event_callback=
                receive_browser_event,
        )

    except Exception as error:

        # Remove broken session.
        recording_sessions.pop(
            session_id,
            None,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to launch "
                "recording browser: "
                f"{error}"
            ),
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Recording started. "
            "A browser window has "
            "been opened.",

        "session":
            session_response(
                session_id,
                recording_sessions[
                    session_id
                ],
            ),
    }


# ============================================================
# MANUALLY ADD EVENT
# ============================================================

@router.post(
    "/{session_id}/event"
)
def add_recording_event(
    session_id: str,
    event: RecorderEventRequest,
):
    """
    Primarily useful for internal integrations
    and future browser extensions.

    Normal testers do NOT need to call this.
    """

    session = (
        recording_sessions.get(
            session_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "Recording session "
                "not found."
            ),
        )

    if (
        session.get("status")
        != "recording"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Recording session "
                "is not active."
            ),
        )

    try:

        step = sanitize_event(
            event
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    if is_duplicate_event(
        session["events"],
        step,
    ):

        return {

            "message":
                "Duplicate event ignored",

            "event_count":
                len(
                    session[
                        "events"
                    ]
                ),
        }

    # ========================================================
    # SAVE EVENT
    # ========================================================

    session[
        "events"
    ].append(
        step
    )

    return {

        "message":
            "Recorder event captured",

        "event_count":
            len(
                session[
                    "events"
                ]
            ),

        "event":
            step,
    }


# ============================================================
# GET RECORDING SESSION
# ============================================================

@router.get(
    "/{session_id}"
)
def get_recording_session(
    session_id: str,
):

    session = (
        recording_sessions.get(
            session_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "Recording session "
                "not found."
            ),
        )

    return {

        "session":
            session_response(
                session_id,
                session,
            )
    }


# ============================================================
# STOP RECORDING + SAVE TEST CASE
# ============================================================

@router.post(
    "/{session_id}/stop"
)
def stop_recording(
    session_id: str,
    data: StopRecordingRequest,
):

    session = (
        recording_sessions.get(
            session_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "Recording session "
                "not found."
            ),
        )

    if (
        session.get("status")
        != "recording"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Recording has already "
                "been stopped."
            ),
        )

    # ========================================================
    # STOP PLAYWRIGHT BROWSER
    # ========================================================

    stop_browser_recorder(
        session_id
    )

    # ========================================================
    # COMPLETE SESSION
    # ========================================================

    session["status"] = (
        "completed"
    )

    session["finished_at"] = (
        utc_now()
    )

    # ========================================================
    # DON'T SAVE TEST
    # ========================================================

    if not data.save_test:

        return {

            "message":
                "Recording stopped.",

            "session":
                session_response(
                    session_id,
                    session,
                ),
        }

    # ========================================================
    # REQUIRE RECORDED EVENTS
    # ========================================================

    if not session["events"]:

        raise HTTPException(
            status_code=400,
            detail=(
                "No browser actions "
                "were recorded."
            ),
        )

    # ========================================================
    # CREATE TEST CASE
    # ========================================================

    test_case = {

        "project_id":
            ObjectId(
                session[
                    "project_id"
                ]
            ),

        "name":
            session[
                "name"
            ],

        "target_url":
            session[
                "target_url"
            ],

        "steps":
            session[
                "events"
            ],

        # Expected results are added
        # by the tester after recording.
        "verifications": [],

        # ====================================================
        # RECORDER INFORMATION
        # ====================================================

        "recording_metadata": {

            "recorder_version":
                "2.0",

            "session_id":
                session_id,

            "scriptless":
                True,

            "captured_fields": [
                "role",
                "name",
                "label",
                "placeholder",
                "id",
                "nameAttr",
                "text",
                "css",
                "tag",
            ],
        },

        "created_at":
            utc_now(),

        "updated_at":
            utc_now(),
    }

    # ========================================================
    # SAVE TO MONGODB
    # ========================================================

    result = (
        test_cases_collection
        .insert_one(
            test_case
        )
    )

    test_id = str(
        result.inserted_id
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Recording completed "
            "and test case created.",

        "test": {

            "id":
                test_id,

            "project_id":
                session[
                    "project_id"
                ],

            "name":
                session[
                    "name"
                ],

            "target_url":
                session[
                    "target_url"
                ],

            "steps":
                session[
                    "events"
                ],

            "verifications": [],
        },

        "session":
            session_response(
                session_id,
                session,
            ),
    }


# ============================================================
# CANCEL / DELETE RECORDING SESSION
# ============================================================

@router.delete(
    "/{session_id}"
)
def cancel_recording(
    session_id: str,
):

    session = (
        recording_sessions.get(
            session_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail=(
                "Recording session "
                "not found."
            ),
        )

    # ========================================================
    # CLOSE BROWSER IF RUNNING
    # ========================================================

    stop_browser_recorder(
        session_id
    )

    # ========================================================
    # DELETE TEMPORARY SESSION
    # ========================================================

    recording_sessions.pop(
        session_id,
        None,
    )

    return {

        "message":
            "Recording session "
            "cancelled and deleted."
    }