# agent.py
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.db.in_memory import InMemoryDb
from agno.tools.websearch import WebSearchTools
from knowledge import build_knowledge
from config import PROJECT_CONTEXT
from catalogo_tools import CatalogoTools

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


def build_chat_agent() -> Agent:
    """Agente con memoria di sessione in-memory per chat multi-turno e ricerca web su richiesta."""
    knowledge, _ = build_knowledge()
    return Agent(
        model=DeepSeek(id="deepseek-chat"),
        knowledge=knowledge,
        search_knowledge=True,
        db=InMemoryDb(),
        add_history_to_context=True,
        tools=[WebSearchTools(), CatalogoTools()],
        instructions=[
            "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
            f"Il progetto è {PROJECT_CONTEXT}.",
            "Cita sempre il documento sorgente nella risposta.",
            "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
            "Per gli importi specifica sempre se IVA inclusa o esclusa.",
            "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
            "Rispondi sempre in italiano.",
            "Usa lo strumento di ricerca web SOLO se l'utente chiede esplicitamente di cercare online o usa parole come 'cerca sul web', 'trova online'.",
            "Usa i tool del catalogo (cerca_articoli_catalogo, cerca_per_codice_fornitore, confronta_fornitori) quando l'utente chiede di confrontare prezzi, trovare fornitori alternativi, verificare se un articolo è presente nel catalogo interno, o controllare se c'è un prezzo migliore per un articolo del preventivo.",
        ],
        markdown=True,
    )
