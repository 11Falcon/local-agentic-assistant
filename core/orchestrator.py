from openai import OpenAI
import os
import re
import string

def strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
def route(client, model, user_input, routes, default='general') :

    """
    prompt the model with the user request and the list of route names;
    ask for exactly one word in reply
    """
    if not client :
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    if not model:
        model = os.environ.get("QWEN_MODEL", "qwen3:8b")
    route_list = ", ".join(routes)
    route_list = ", ".join(routes)
    content = (
        "You route requests to specialists. Reply with EXACTLY one word.\n"
        f"Specialists: {route_list}"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role" : "system", "content":content},
                  {"role": "user", "content" : user_input}]
    )
    response = resp.choices[0].message.content
    striped = strip_think(response).strip(string.whitespace + string.punctuation).lower()
    return striped if striped in routes else default

# an orchestrator is just a tool (mandatory)
def agent_to_tool(agent, name, description):
    from core.agent import Agent
    def fn(request):
        return agent.run(request)
    """return  (schema, fn)"""
    schema = {
        "type" : "function",
        "function" :{
            "name" : name,
            "description" : description,
            "parameters":{
                "type": "object",
                "properties": {"request" :{"type":"string", "description":"one required string ('what to ask this agent, in plain language')"}},
                "required":['request']
            }
        }
    }
    return (schema, fn)

# the orchestrator

class Orchestrator:
    def __init__(self, client, model, agents, default = "general"):
        # agents : disct name -> Agent, must contain the default
        self.client = client
        self.model = model
        self.agents = agents
        self.default = default
        self.last_route = None

    def run(self, user_input) ->str :
        choice = route(self.client, self.model, user_input, list(self.agents), self.default)
        self.last_route = choice
        return self.agents[choice].run(user_input)