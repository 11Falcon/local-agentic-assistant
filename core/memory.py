import json
import os
from core.llm import get_client, get_model

def trim_messages(messages, max_messages = 20):
    if len(messages) <= max_messages:
        return list(messages)
    if messages[0].get("role") == "system":
        return [messages[0]] +  list(messages[- (max_messages  - 1) :])
    else:
        return messages[- max_messages :]

def save_session(path, messages):
    with open(path, mode="w", encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def load_session(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding="utf-8") as f:
        return json.load(f)


def summarize_and_compact(client, model, messages, keep_last = 4):
    has_system = bool(messages) and messages[0].get("role") == "system"
    head = [messages[0]] if has_system else []
    body = messages[len(head) : ]

    if len(body) <= keep_last:
        return list(messages)


    old, recent = body[:-keep_last], body[-keep_last:]
    transcript = "\n".join(f"{m.get('role')} : {m.get('content')}" for m in old)

    if not client:
        client = get_client()

    if not model:
        model = get_model()

    resp = client.chat.completions.create(
        model = model,
        messages = [{"role": "user",
                     "content" : "Summarize this conversation concisely, keeping every "
                     "fact, name, date and decision: \n\n" + transcript}]
    )
    summary = resp.choices[0].message.content or ""
    return head + [{"role" : "system",
                    "content" : f"Summary of the convarsation so far : {summary}"}] + list(recent)