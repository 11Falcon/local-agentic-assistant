def make_agent_messages(role_description, user_input):
    return [{'role':'system', 'content':role_description}, {'role':'user', 'content': user_input}]