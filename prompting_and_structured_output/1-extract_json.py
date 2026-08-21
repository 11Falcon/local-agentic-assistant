import json
def extract_json(text):
    """parses and returns the first JSON object in text as Python value"""
    start = text.find('{')
    counter = 1
    i = start + 1
    while start != -1 :
        while counter > 0 and i < len(text):
            if text[i] == '{':
                counter += 1
            elif text[i] == '}':
                counter -= 1
            i += 1
        if counter != 0:
            break
        try:
            js = json.loads(text[start: i])
            return js
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            i = start + 1
            counter = 1

    raise ValueError("no valid JSON object is found")
