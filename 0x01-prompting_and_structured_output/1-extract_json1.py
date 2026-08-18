import json

def extract_json(text):
    """ parses and returns the first json object in text"""

    start = text.find('{')
    while start != -1:
        count = 1
        i = start + 1
        while i < len(text) and count > 0:
            if text[i] == "{":
                count += 1
            elif text[i] == "}":
                count -= 1
            i += 1
            
            if count != 0:
                break
            try:
                js = json.loads(text[start: i])
                return js
            except json.JSONDecodeError:
                start = text.find("{", start + 1)

    raise ValueError("no valid JSON object is found")