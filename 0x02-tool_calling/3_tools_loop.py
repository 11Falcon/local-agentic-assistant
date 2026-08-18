import os
import json
from openai import OpenAI

def run_with_tools(client, model, messages, registry, max_turns = 5):
    if not model :
        model = os.environ.get("QWEN_MODEL", 'qwen3:8b')
    if not client:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key = "ollama")
    
    for i in range(max_turns):
        resp = client.chat.completions.create(
            model = model,
            messages= messages,
            tools= registry.get_schemas()
        )
        message = resp.choices[0].message

        if message.tool_calls:
            messages.append(message)

            for request in message.tool_calls:
                answer = registry.execute(request.function.name, request.function.arguments)
                messages.append({'role': 'tool',
                                 'tool_call_id': request.id,
                                 'content': answer,
                                 })
        else:
            message.append({'role': 'assistant',
                            'content': message.content})
            return message.content
    return "the turn limit was reached"