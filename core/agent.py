import os
import time

from core import llm

# Set AGENT_DEBUG=1 to print where each turn spends its time.
DEBUG = os.environ.get("AGENT_DEBUG") == "1"


def _dim(text):
    if DEBUG:
        print(f"\033[2m{text}\033[0m", flush=True)


class Agent:
    def __init__(self, name, system_prompt, registry = None,
                 client = None, model = None, max_iterations = 8):
        if not client:
            client = llm.get_client()
        if not model:
            model = llm.get_model()
        self.name = name
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.registry = registry
        self.max_iterations = max_iterations
        self.messages = [{'role': "system", "content": system_prompt}]
        self.trace = []
    
    def run(self, user_input) -> str:
        self.messages.append({"role": "user", "content": user_input})
        self.trace.append({"type" : "user", "content":user_input})
        for i in range(self.max_iterations):
            _t0 = time.perf_counter()
            resp = self.client.chat.completions.create(
                model = self.model,
                messages = self.messages,
                # qwen3 emits <think> blocks by default; for a tool-calling agent
                # that is wasted generation. Halves the time on Ollama.
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                **({"tools": self.registry.get_schemas()} if self.registry else {}),
            ).choices[0].message
            _dim(f"  [{self.name} iter {i+1}/{self.max_iterations}] "
                 f"model {time.perf_counter() - _t0:5.1f}s  "
                 f"({len(self.messages)} messages in context)")
            if resp.tool_calls:
                if not self.registry:
                    # Nothing would be appended below, so the next iteration would
                    # send an identical context and spin to max_iterations for free.
                    msg = resp.content or "I tried to use a tool but I have none available."
                    self.messages.append({"role": "assistant", "content": msg})
                    self.trace.append({"type": "assistant", "content": msg})
                    return msg
                # Plain dicts only - a raw ChatCompletionMessage is not
                # JSON-serializable and breaks save_session().
                self.messages.append({
                    "role": "assistant",
                    "content": resp.content or "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name,
                                      "arguments": tc.function.arguments}}
                        for tc in resp.tool_calls
                    ],
                })
                for request in resp.tool_calls:
                    self.trace.append({"type": "tool_call", "name":request.function.name, "arguments": request.function.arguments})
                    _t1 = time.perf_counter()
                    call_answer = self.registry.execute(request.function.name, request.function.arguments)
                    _dim(f"      tool {request.function.name}"
                         f"({request.function.arguments}) -> {time.perf_counter() - _t1:5.1f}s")
                    self.messages.append({"role":"tool","tool_call_id": request.id ,  "content": call_answer})
                    self.trace.append({"type": "tool_result", "name": request.function.name, "content":call_answer})
            else:
                self.messages.append({"role": "assistant", "content": resp.content})
                self.trace.append({"type": "assistant", "content": resp.content})
                return resp.content
        msg = f"I couldn't finish within the step limit"
        self.messages.append({"role": 'assistant', "content": msg})
        return msg
