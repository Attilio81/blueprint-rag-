# agent.py
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from knowledge import build_knowledge
from config import PROJECT_CONTEXT

load_dotenv()


def build_agent() -> Agent:
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            f"Il progetto è {PROJECT_CONTEXT}.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
        ],
        markdown=True,
    )
