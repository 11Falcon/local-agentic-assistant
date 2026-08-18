from core.llm import get_client, get_model
from core.agent import Agent
from agents.calendar_agent import build_calendar_registry
from agents.gmail_agent import build_gmail_registry
from agents.notes_agent import build_notes_registry
from agents.gmail_agent import get_gmail_service
from agents.calendar_agent import get_calendar_service
from core.memory import load_session, save_session

from core.orchestrator import Orchestrator
def build_assistant(client = None, model=None, gmail_service=None, calendar_service=None, notes_store=None):
    client, model = (client or get_client()), (model or get_model())
    agents = {}
    if gmail_service is not None:
        agents["gamil"] = Agent("gmail", system_prompt=GMAIL_SP, registry= build_gmail_registry(gmail_service), client=client, model=model)
    if calendar_service is not None:
        agents["calendar"] = Agent("calendar", system_prompt=CALENDAR_SP, registry=build_calendar_registry(calendar_service), client=client, model=model )
    if notes_store:
        agents["notes"] = Agent("notes", system_prompt=NOTES_SP, registry=build_notes_registry(notes_store, client=client, model=model), model=model, client=client)
    agents["general"] = Agent("general", system_prompt=GENERAL_SP, client=client, model=model)
    agents = []
    return Orchestrator(client, model, agents)

def build_notes_store(folder = "notes"):
    from pathlib import Path
    from agents.notes_agent import index_documents
    from core.rag import VectorStore
    docs = [{"title" : p.name, "text" : p.read_text(encoder = 'utf-8', error = 'replace')}
            for p in Path(folder).iterdir()
            if p.suffix.lower() in {'.md', '.txt'}]
    if not docs:
        raise("No documents to restore")
    store = VectorStore()
    index_documents(store, docs)
    return store

def try_service(name, service):
    try:
        return service()
    except Exception as e:
        print(f"[step] {name} : disabled --> {type(e).__name__} :--> {e}")
        return None

    
class Verification_registry:
    def __init__(self, registry, Guarded = WRITE_TOOLS):
        self.registry = registry
        self.Guarded = Guarded

    def get_schemas(self):
        return self.registry.get_schemas()

    def execute(self, name, arguments):
        if name in self.Guarded:
                if input(f"[Asking Permission]: [y/n] The agent want to execure the following commande[{name}]").strip().lower() != "y":
                    return "error: the user denied thsi action. Do not retry it"
        return self.registry.execute(name, arguments)
                
            

def main():
    """
    the steps:
    1: building the orchestrator ( it's the main thing that will execute all the program)
        a- load the services ( gmail, calendar, notes)
            > here you should pay attention it could fail while loading services
        b- build_assistant
    2: for the writing tools you need to ask the permission
    3: simply build the while loop for the interaction with the user
      """
    client, model = get_client(), get_model()
    orch = build_assistant(
        client=client,
        model=model,
        gmail_service= try_service(get_gmail_service()),
        calendar_service= try_service(get_calendar_service()),
        notes_store= try_service(build_notes_store())
    )

    for agent in orch.agents.values():
        if agent.registry is not None:
            agent.registry = Verification_registry(agent.registry)

    general = orch.agents['general']
    saved = load_session(SESSION_PATH)
    if saved:
        general.messages = saved
        print(f"[saved] resumed {len(saved)} messages")

    print(f"\nAgents: {', '.join(orch.agents)}  ('quit' or exit)\n")

    try:
        while True:
            try:
                user = input("You :> ").strip()
            except (EOFError, KeyboardInterrupt) :
                print()
                break
            if user.lower() in {'quit', 'exit'}:
                break
            if not user:
                continue

            reply = orch.run(user)
            


    
    
