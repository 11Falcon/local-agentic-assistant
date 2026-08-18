# 0x02 — Tool calling

## Concepts

**Tools are what turn a chatbot into an agent.** An LLM can only produce text — it
cannot read your inbox or check a calendar. *Tool calling* (also "function calling")
is the protocol that fixes this:

1. You describe your functions to the model as **JSON schemas** (name, description,
   parameters) passed in the `tools=` argument.
2. Instead of replying with text, the model may reply with **`tool_calls`** — "please
   run `calculator` with arguments `{"expression": "6*7"}`" . The model never executes
   anything; it only *asks*.
3. **Your code** executes the function, appends the result as a `role="tool"` message
   (carrying the `tool_call_id`), and calls the model again.
4. Repeat until the model replies with plain text — the final answer.

That request → execute → feed back → repeat cycle is **the agent loop**. Everything
in modules 0x03–0x09 is this loop with better packaging.

```
model:  tool_calls=[calculator({"expression": "6*7"})]
you:    run calculator → "42" → append {"role":"tool", "tool_call_id":..., "content":"42"}
model:  "The answer is 42."
```

**Descriptions are prompts.** The model chooses tools *only* from your names,
descriptions, and parameter descriptions. Vague description ⇒ wrong tool calls.

**Never trust tool arguments.** They are model-generated text. Your calculator must
not `eval()` whatever arrives — you'll parse expressions safely with the `ast` module.

**The registry pattern.** Rather than a pile of `if name == "calculator"` branches,
you'll build a `ToolRegistry` that maps names → (function, schema), and always returns
a *string* result — including `"Error: ..."` on failure, because the model can read an
error message and try again, but an uncaught exception kills your whole agent.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (max 10 min):**
- Ollama tool-support post — short, has one complete example; read it fully:
  https://ollama.com/blog/tool-support

**Only when a task sends you there (lookup, not reading):**
- Task 0/3 — OpenAI function-calling guide: look ONLY at the example tool schema
  and the example response with `tool_calls`; ignore everything else on the page:
  https://platform.openai.com/docs/guides/function-calling
- Task 1 — `ast` docs, search for `ast.parse` and `m      ode="eval"` (5 min):
  https://docs.python.org/3/library/ast.html

**After the module is green (30 min, worth it):** Anthropic's "Building effective
agents" — read from the start through the "Agents" section. It will land 10×
better now that you've built the loop yourself:
https://www.anthropic.com/engineering/building-effective-agents

## You're done when you can answer these without Google

- Who actually executes a tool call — the model or your code? What does the model
  really "do" when it uses a tool?
- What three things travel back to the model after you run a tool, and in what
  kind of message?
- Why must `ToolRegistry.execute` return an error *string* instead of raising?
- Why is `eval()` on tool arguments dangerous even though "it's just a calculator"?

## General requirements

- Files live in `0x02-tool_calling/`.
- `ToolRegistry.execute` **never raises** — it returns an error string instead.
- Verify: `python checker.py 0x02`

---

## Tasks

### 0. Describe a tool (mandatory)
**File:** `0-tool_schema.py`

Write `make_tool_schema(name, description, parameters)` → returns the OpenAI-format
dict:

```python
{"type": "function",
 "function": {"name": name, "description": description, "parameters": parameters}}
```

where `parameters` is a JSON-schema dict like
`{"type": "object", "properties": {...}, "required": [...]}`.

```powershell
python checker.py 0x02 0
```

### 1. A safe calculator tool (mandatory)
**File:** `1-calculator.py`

Write `calculator(expression)` → evaluates an arithmetic expression string
(`+ - * / ** %` and parentheses) and returns the numeric result.
**Forbidden:** `eval()`/`exec()` on the raw string. Parse with
`ast.parse(expression, mode="eval")` and walk the tree, allowing only numeric
constants, the arithmetic operators, and unary minus. Anything else (names, calls,
attributes...) raises `ValueError`.

Also define module-level `TOOL_SCHEMA`: the schema for this tool (name
`"calculator"`, one required string parameter `expression`).

```powershell
python checker.py 0x02 1
```

### 2. The tool registry (mandatory)
**File:** `2-registry.py`

Write `class ToolRegistry` with:
- `register(name, fn, schema)` — store a tool
- `get_schemas()` — list of all schemas (for the `tools=` argument)
- `execute(name, arguments)` — `arguments` is a **JSON string** (exactly what
  `tool_call.function.arguments` gives you). Parse it, call `fn(**args)`, return
  `str(result)`. Unknown tool or any exception from `fn` → return a string starting
  with `"Error:"` (never raise).

```powershell
python checker.py 0x02 2
```

### 3. The tool loop (mandatory)
**File:** `3-tool_loop.py`

Write `run_with_tools(client, model, messages, registry, max_turns=5)`:
1. Call `client.chat.completions.create(model=..., messages=..., tools=registry.get_schemas())`.
2. If the reply message has `tool_calls`: append the assistant message to `messages`,
   then for **each** tool call execute it via the registry and append
   `{"role": "tool", "tool_call_id": call.id, "content": result}`. Go to 1.
3. Otherwise return the reply's text content.
4. If `max_turns` model calls happen without a final text answer, return a string
   saying the turn limit was reached.

Bonus (not checked): make `python 3-tool_loop.py` an interactive demo with the real
model — ask it "what is 391 * 27 + 4?" and watch it call your calculator.

```powershell
python checker.py 0x02 3
python checker.py 0x02 --integration
```
