from openai import OpenAI
import os

def call_model(client, model, messages):
    """Ask"""
    if not client:
        client = OpenAI(base_url = "http://localhost:11434/v1", api_key="ollama")
    if not model:
        model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    resp = client.chat.completions.create(
        model = model,
        messages = messages
    )
    return resp.choices[0].message.content


def ask_until_valid(client, model, messages, validator, max_attempts=3):
    """There is no way i already reached here"""

    for i in range(max_attempts):
        resp = call_model(client, model, messages)
        try:
            return  validator(resp)
        except ValueError as e:
            messages.append({'role': "assistant", "content": resp})
            t = "Your reply was invalid: " + str(e) + " Reply again, following the required format"
            messages.append({'role': "user", "content": t})
    raise ValueError("3iyyan : no VALID reply after 3 attemps")