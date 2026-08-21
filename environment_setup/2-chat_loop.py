def build_messages(history, user_input, system_prompt="You are a helpful assistant."):
    new_hist = history[:]
    new_hist.append({"role":"user", "content": user_input})
    new_hist.insert(0, {'role':'system', "content" : system_prompt})
    return new_hist