"""
The tool Loop (mandatory)
"""
import os
from openai import OpenAI

def run_with_tools(client, model, messages, registry, max_turns=5):
    if not model:
        model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    if not client:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


    for i in range(max_turns):    
        resp = client.chat.completions.create(
            model = model, 
            messages = messages, 
            tools = registry.get_schemas() )
        print(resp)
        
        msg = resp.choices[0].message

        if msg.tool_calls:
            print(msg)
            messages.append(msg)

            for request in msg.tool_calls:
                answer = registry.execute(
                    request.function.name, 
                    request.function.arguments)
                
                messages.append({
                    'role':"tool", 
                    "tool_call_id":request.id, 
                    "content": answer})
        else:
            messages.append({'role': 'assistant', "content": msg.content})
            return msg.content
    return "the turn limit was reached"

    

