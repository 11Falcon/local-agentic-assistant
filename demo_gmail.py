from core.agent import Agent
from agents.gmail_agent import get_gmail_service, build_gmail_registry

agent = Agent("gmail", "You are an email assistant. Use tools; never invent emails.",
              registry=build_gmail_registry(get_gmail_service()))
print(agent.run("Any unread emails from the last 2 days? Summarize them."))