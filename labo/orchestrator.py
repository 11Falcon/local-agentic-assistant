from openai import OpenAI
import os
import re
import string

def route(client, model, user_input, routes, default = "general"):
    if not client :
        client = OpenAI(base_url="http://localhost:11434/v1", api_key = "ollama")
    if not model :
        model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    resp = client.completions.create(
        model= model,
        messages = [
            {"role":"system", "content":(
                "You are a helpfull assistant, based on the list or routes you will answer with one and only one word in reply"
                "the list of routes is "
                "\n".join(rt for rt in routes)
            )},
            {"role" : "user",
             "content" : user_input}
        ],
    )
    resp = resp.choices[0].messages.content
    clearn = re.sub("<think>.*?</think>", "", resp, flags=re.DOTALL).split(string.punctuation, string.whitespace).lower()
    return clearn if clearn in routes else default