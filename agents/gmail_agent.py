SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
import base64

def get_gmail_service(credentials_path="credentials.json", token_path="token.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.environ.get("NO_INTERACTIVE_AUTH") == "1":
                # In a container there is no browser and no way to receive the
                # redirect: run_local_server() would block forever instead of
                # failing. Turn that hang into a clean, catchable error.
                raise RuntimeError(
                    "no valid Gmail token and interactive OAuth is disabled. "
                    "Run assistant.py on the HOST once to create token.json, "
                    "then restart the container.")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)    

def list_recent(service, max_results=5):
    msgs = service.users().messages().list(userId="me",  maxResults=max_results).execute()
    messages = []
    for msg in msgs.get("messages", []):
        message = service.users().messages().get(userId="me", id=msg['id'], format="metadata").execute()
        headers = {header["name"].lower(): header["value"]
                   for header in message.get("payload", {}).get("headers", [])}
        messages.append({
            "id" : message["id"],
            "from" : headers.get("from", ""),
            "subject" : headers.get("subject", ""),
            "snippet" : message.get("snippet", ""),
        })
    return messages

def search_messages(service, query, max_results=10):
    msgs = service.users().messages().list(userId = 'me', q=query, maxResults = max_results).execute()
    messages = []
    for msg in msgs.get("messages", []):
        message = service.users().messages().get(userId = "me", id = msg["id"], format="metadata").execute()
        headers = {header["name"].lower() : header["value"]
                   for header in message.get("payload", {}).get("headers", [])}
        messages.append({
            "id" : message["id"],
            "from" : headers.get("from", ""),
            "subject" : headers.get("subject", ""),
            "snippet" : message.get("snippet", ""),
        })
    return messages

def create_draft(service, to, subject, body):
    message = EmailMessage()
    message['to'] = to
    message['subject'] = subject
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body = {
            "message" : {'raw' : raw}
        }
    ).execute()
    return draft["id"]

def read_email(service, message_id):
    msg = service.users().messages().get(          # messages() — you dropped the ()
        userId="me", id=message_id, format="metadata").execute()
    headers = {h["name"].lower(): h["value"]       # .lower() — Gmail sends "From", you look up "from"
               for h in msg.get("payload", {}).get("headers", [])}
    return "\n".join([
        f"From: {headers.get('from', '')}",
        f"Subject: {headers.get('subject', '')}",
        msg.get("snippet", ""),
    ])

def build_gmail_registry(service):
    from core.tools import ToolRegistry
    registry = ToolRegistry()

    def list_recent_emails(max_results=5):
        results = list_recent(service, max_results=max_results)
        if not results:
            return "No recent emails."
        return "\n".join(
            f"[{r['id']}] from {r['from']} | {r['subject']} | {r['snippet']}"
            for r in results
        )
    registry.register(
        name="list_recent_emails",
        fn=list_recent_emails,
        schema={
            "type": "function",
            "function": {
                "name": "list_recent_emails",
                "description": ("List the most recent emails in the user's inbox, "
                                "newest first. Use this for requests like 'my last "
                                "3 emails' or 'what is new in my inbox'. Do NOT use "
                                "search_email for that - search_email needs a real "
                                "query and will return nothing without one."),
                "parameters": {
                    "type": "object",
                    "properties": {"max_results": {
                        "type": "integer",
                        "description": "how many emails to return, default 5"}},
                    "required": [],
                },
            },
        },
    )

    def search_email(query):
        results = search_messages(service, query)
        if not results:
            return "No matching emails."
        return  "\n".join(
            f"[{r['id']}] from {r['from']} | {r['subject']} | {r['snippet']}"
            for r in results
        )
    registry.register(
    name="search_email",
    fn=search_email,
    schema={
        "type": "function",
        "function": {
            "name": "search_email",
            "description": (
                "Search the user's Gmail and return matching messages. "
                "A BARE WORD OR PHRASE searches the FULL TEXT of every email - sender, "
                "subject AND body - and is usually what you want: query='Alice' finds "
                "every email mentioning Alice anywhere, including in the signature. "
                "Optional operators, combinable with bare words: from:someone@x.com, to:, "
                "subject:, is:unread, has:attachment, newer_than:7d, after:2026/08/01. "
                "There is NO body: operator. Do not invent operators - an unknown one "
                "matches nothing. If a query using an operator returns no results, retry "
                "with the plain keywords alone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Gmail search query used to find the emails. "
                            "Examples: 'from:alice@example.com', "
                            "'is:unread', 'subject:meeting newer_than:7d'."
                        ),
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
)

    def read_email_tool(message_id):
        message = read_email(service=service, message_id=message_id)
        if not message:
            return "No email is found"
        return message
    registry.register(
    name="read_email",
    fn=read_email_tool,
    schema={
        "type": "function",
        "function": {
            "name": "read_email",
            "description": (
                "Read an email using its Gmail message ID. "
                "Use this tool after search_email when you need to inspect "
                "the content of a specific email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": (
                            "The Gmail message ID returned by search_email."
                        ),
                    }
                },
                "required": ["message_id"],
                "additionalProperties": False,
            },
        },
    },
)

    ### now let's move to the next function that is : create_draft

    def create_draft_tool(to, subject, body:str):
        draft_id = create_draft(service= service, to=to, subject=subject, body = body )
        return f"the email is drafted | id : {draft_id} | to : {to}"

    registry.register(
    name="create_draft",
    fn=create_draft_tool,
    schema={
        "type": "function",
        "function": {
            "name": "create_draft",
            "description": (
                "Create a Gmail draft without sending it. "
                "Use this tool when the user asks to draft, write, "
                "prepare, or compose an email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": (
                            "Recipient email address, for example "
                            "'alice@example.com'."
                        ),
                    },
                    "subject": {
                        "type": "string",
                        "description": (
                            "Short subject line of the email."
                        ),
                    },
                    "body": {
                        "type": "string",
                        "description": (
                            "Complete email body to put in the draft."
                        ),
                    },
                },
                "required": ["to", "subject", "body"],
                "additionalProperties": False,
            },
        },
    },
)


    return registry