SCOPES = ["https://www.googleapis.com/auth/calendar"]
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from datetime import datetime, timezone, timedelta

def get_calendar_service(credentials_path="credentials.json", token_path="token_calendar.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.environ.get("NO_INTERACTIVE_AUTH") == "1":
                # No browser inside a container - see the note in gmail_agent.
                raise RuntimeError(
                    "no valid Calendar token and interactive OAuth is disabled. "
                    "Run assistant.py on the HOST once to create "
                    "token_calendar.json, then restart the container.")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port = 0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def upcoming_events(service, max_results=10):
    now_iso = datetime.now(timezone.utc).isoformat()
    resp = service.events().list(calendarId = "primary", timeMin = now_iso, maxResults = max_results, singleEvents = True, orderBy = "startTime").execute()
    out = []

    for event in resp.get("items", []):
        start = event.get("start", {})
        end = event.get("end", {})
        out.append({
            "id" : event.get("id"),
            "summary" : event.get("summary", ""),
            "start" : start.get("dateTime", start.get("date")),
            "end" : end.get("dateTime", end.get("date"))
        })
    return out

def create_event(service, summary, start_iso, end_iso, attendees=None):
    body = {
        "summary" : summary,
        "start" : {"dateTime" : start_iso},
        "end" : {"dateTime" : end_iso}
    }
    if attendees:
        body["attendees"] = [{"email" : e} for e in attendees]
    resp = service.events().insert(calendarId = "primary", body = body).execute()
    return {"id": resp.get("id"), "link": resp.get("htmlLink")}

def find_free_slots(busy, day_start, day_end, duration_minutes):
    #sorting busy
    busy = sorted(busy, key=lambda st : datetime.fromisoformat(st["start"]))
    cursor = datetime.fromisoformat(day_start)
    need = timedelta(minutes = duration_minutes)
    end_limit = datetime.fromisoformat(day_end)
    out = []
    for event in busy:

        block_start = datetime.fromisoformat(event["start"])
        block_end = datetime.fromisoformat(event["end"])
        if block_start - cursor >= need:
            out.append({"start": cursor.isoformat(), "end": block_start.isoformat()})
        cursor = max(cursor, block_end)
    if end_limit - cursor >= need :
        out.append({"start": cursor.isoformat(), "end":end_limit.isoformat()})
    return out

def build_calendar_registry(service):
    from core.tools import ToolRegistry

    register = ToolRegistry()

    def list_events(max_results = 10):
        the_list = upcoming_events(service, max_results )
        return "\n".join(
            f"id : [{event['id']}] | start date : [{event['start']}] | end date : [{event['end']}] | summary : [{event['summary']}]"
            for event in the_list
        )
    register.register(name="list_events", fn = list_events, schema={
        "type" : "function",
        "function" : {
            "name" : "list_events",
            "description" :"listing the events from the google calender account of the user with a max_results parameter",
            "parameters": {
                "type" :"object",
                "properties": {"max_results":{"type": "integer", "description":"the number of events the user requested to review"}},
                "required" :[]
            }
        }
    })
    def create_event_tool(summary, start_iso, end_iso:str, attendees=None):
        creation = create_event(service, summary, start_iso, end_iso, attendees)
        return f"the event is created id :  [{creation['id']}] | htmlLink [{creation['link']}]"

    
    register.register(name="create_event", fn= create_event_tool, schema={
        'type' : 'function',
        'function': {
            "name" : "create_event",
            "description" : "creating an event in the calendar of the user using start_iso, end_iso and summary of the event",
            "parameters":{
                "type" : "object",
                "properties":{"summary" : {"type":"string", "description" : " the summary of the event"},
                              "start_iso" : {"type":"string", "description" : "the start date of the event that should be in the exact datetime format and must use : (RFC3339, e.g. 2026-07-14T15:00:00+01:00) "},
                              "end_iso" : {"type":"string", "description" : "the end date of the event that should be in the exact datetime format and must use : (RFC3339, e.g. 2026-07-14T15:00:00+01:00) "},
                              "attendees":{"type":"array", "items": {"type": "string"}, "description":"the list of emails someone@x.com of the attendees for this event"},},
                "required":["summary", "start_iso", "end_iso"],
        },
    }})
    return register