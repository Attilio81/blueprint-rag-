# main.py
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="RAG Agent Preventivi")
    parser.add_argument("--reindex", action="store_true", help="Force re-indexing of all PDFs")
    parser.add_argument("--ingest-only", action="store_true", help="Only index, don't start chat")
    args = parser.parse_args()

    if args.reindex or args.ingest_only:
        from ingestion.pipeline import run_ingestion
        run_ingestion(reindex=args.reindex)
        if args.ingest_only:
            return

    from agent import build_agent
    agent = build_agent()

    print("\n=== Agente RAG Preventivi Leonardo ===")
    print("Digita 'exit' per uscire.\n")

    while True:
        try:
            user_input = input("Tu: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break
        agent.print_response(user_input, stream=True)
        print()

    print("Arrivederci!")


if __name__ == "__main__":
    main()
