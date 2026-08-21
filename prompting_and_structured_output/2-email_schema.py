from pydantic import BaseModel, field_validator
import json

class EmailDraft(BaseModel):
    to: str
    subject : str
    body : str
    
    @field_validator("to")
    @classmethod
    def is_an_email(cls, value):
        if "@" in value:
            return value
        raise ValueError("'to' is not an email")

def parse_email_draft(raw):
    r = json.loads(raw)
    return EmailDraft.model_validate(r)