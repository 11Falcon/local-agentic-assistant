import re
def strip_thinking(text):
    print(re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL))
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()