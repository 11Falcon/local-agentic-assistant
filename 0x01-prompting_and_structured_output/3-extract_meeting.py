from openai import OpenAI
import json

def extract_json(text):
    start = text.find('{')
    while start != -1:
        closed = 1
        i = start + 1
        while i < len(text) and closed > 0:
            if text[i] == "{":
                closed += 1
            elif text[i] == "}":
                closed -= 1
            i += 1
        if closed != 0:
            raise ValueError("no json found!!")
        try:
            js = json.loads(text[start: i ])
            print(js)
            return js
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
    raise ValueError("no json found!")
def extract_meeting(text, client=None, model=None):
    if not client:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key = "ollama")
    if not model:
        model = "qwen3:8b"
    resp = client.chat.completions.create(
        model = model,
        messages= [
            {"role": "system","content": "you are an information extractor. you give the needed informations in a Json format, the keys are : title, date, time, attendees(list)"},
            {"role": "user", "content":text}
        ],
    )
    response = resp.choices[0].message.content
    print(response)
    return extract_json(response)
