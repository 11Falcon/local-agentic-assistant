from openai import OpenAI
import os
def ask_qwen(prompt, client=None, model=None):
    if not client:
        client = OpenAI(base_url= 'http://localhost:11434/v1', api_key='ollama')
    if not model:
        model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    resp = client.chat.completions.create(
        model = model,
        messages = [{'role': 'user', "content": prompt}]
    )
    return resp.choices[0].message.content