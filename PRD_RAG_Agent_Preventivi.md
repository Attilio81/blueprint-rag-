# PRD — Agente RAG Multimodale per Analisi Preventivi Edilizi

## Contesto

IABGroup gestisce cantieri complessi con decine di preventivi eterogenei da fornitori diversi
(arredo urbano, insegnistiche, infissi, cartongesso, verde, ecc.).
I documenti contengono sia testo (prezzi, condizioni) che immagini (foto prodotti,
disegni tecnici, prospetti architettonici, loghi insegne).

L'obiettivo è un agente conversazionale che risponde a domande sui preventivi in linguaggio
naturale, aggregando informazioni da testo E immagini di documenti multipli.

---

## Stack Tecnico

| Componente       | Scelta                                              |
|------------------|-----------------------------------------------------|
| Orchestrazione   | **Agno** (AgentOS)                                  |
| LLM              | **DeepSeek** via API (testo/ragionamento)           |
| Vision Model     | **Gemini 2.0 Flash** (lettura immagini da PDF)      |
| Embedding        | **GeminiEmbedder** (`gemini-embedding-exp-03-07`)   |
| Vector Store     | **ChromaDB** (locale, persistente su disco)         |
| PDF Processing   | **pymupdf** (estrazione testo + rasterizzazione pagine) |
| Interfaccia      | CLI (prima fase) — nessuna UI                       |
| Runtime          | Python 3.11+                                        |

---

## Perché Google Embedding

| | `nomic-embed-text` (Ollama) | `text-embedding-3-small` (OpenAI) | `gemini-embedding-exp` (Google) |
|---|---|---|---|
| Costo | Gratis | ~$0.02/1M token | Free tier generoso |
| Qualità IT | Discreta | Buona | **Ottima** |
| Context window | 2048 token | 8191 token | **8192 token** |
| Multimodale | No | No | Si |
| Setup | Ollama locale | API key | API key |

La finestra da 8K token evita chunking aggressivo sulle tabelle prezzi.
L'italiano è gestito nativamente senza degradation.

---

## Strategia Multimodale

### Il problema
I PDF contengono:
- **Testo selezionabile** → estratto direttamente (prezzi, descrizioni, condizioni)
- **Immagini embedded** → foto prodotti (ONICE), loghi insegne (Adriatica Neon), schede tecniche
- **Pagine grafiche** → prospetti architettonici (NORD/SUD/OVEST), renders

### La soluzione: Page-as-Image + Vision Description

Ogni pagina PDF viene **rasterizzata come immagine** e passata a **Gemini Vision**
che genera una descrizione testuale strutturata. Questa descrizione viene poi
indicizzata insieme al testo estratto normalmente.

```
PDF Page
   ├── Testo estratto (pymupdf)      → chunk testuale  → ChromaDB
   └── Pagina rasterizzata (png)     → Gemini Vision   → descrizione → ChromaDB
```

Entrambi i chunk finiscono in ChromaDB con lo stesso embedder Google.

### Cosa estrae Gemini Vision dalle pagine

**Da ONICE.pdf (scheda prodotto):**
> "Fioriera circolare ONICE in PDM sabbiato. Tre misure: Ø800mm H480mm 278kg,
> Ø1200mm H620mm 753kg, Ø1500mm H760mm 1361kg. Design: Staubach & Kuckertz.
> Accessori: panca circolare in acciaio verniciato Ø1200 e Ø1500."

**Da Prospetti architettonici:**
> "Prospetto Nord del Centro Commerciale Leonardo Imola. Facciata con insegna
> LEONARDO in lettere scatolate a luce diretta, posizionata in alto al centro.
> Presenza di frangisole orizzontali. Ingresso principale con pensilina vetrata."

---

## Struttura del Progetto

```
rag_preventivi/
├── main.py                  # Entry point — avvia l'agente CLI
├── agent.py                 # Definizione agente Agno
├── knowledge.py             # Setup ChromaDB
├── ingestion/
│   ├── text_extractor.py    # Estrazione testo da PDF (pymupdf)
│   ├── image_extractor.py   # Rasterizzazione pagine + Vision description
│   └── pipeline.py          # Orchestrazione ingestion completa
├── config.py                # Costanti, path, chiavi API
├── documents/               # PDF sorgente (da indicizzare)
│   ├── ONICE.pdf
│   ├── prev.pdf
│   ├── prev__2_.pdf
│   ├── PROT_31_IAB_SOC_COOP__130125.pdf
│   ├── 24-0546.pdf
│   ├── 0475.pdf
│   ├── LEONARDO_IMOLA_Prospetto_NORD.pdf
│   ├── LEONARDO_IMOLA_Prospetto_OVEST.pdf
│   └── LEONARDO_IMOLA_Prospetto_SUD.pdf
├── chroma_db/               # Dati ChromaDB persistenti (gitignore)
├── requirements.txt
└── .env                     # GOOGLE_API_KEY, DEEPSEEK_API_KEY
```

---

## Funzionalità Richieste

### F1 — Pipeline di Indicizzazione Multimodale

Per ogni PDF, la pipeline esegue **due passaggi**:

**Passaggio 1 — Testo:**
- Estrazione testo con `pymupdf`
- Chunking (chunk_size 1000, overlap 200)
- Embedding con `GeminiEmbedder`
- Salvataggio in ChromaDB con metadata: `{source, page, type: "text"}`

**Passaggio 2 — Immagini/Pagine:**
- Rasterizzazione ogni pagina a 150 DPI (png in memoria, no file temporanei)
- Invio a Gemini Vision con prompt strutturato
- Descrizione testuale generata → chunk
- Embedding con `GeminiEmbedder`
- Salvataggio in ChromaDB con metadata: `{source, page, type: "vision"}`

**Logica di deduplicazione:**
- Skip se documento già indicizzato (hash file salvato in file locale `indexed.json`)
- Re-indicizzazione forzata con flag `--reindex`

**Prompt Vision per Gemini:**
```
Sei un assistente tecnico che analizza documenti edilizi e preventivi.
Descrivi in italiano tutto ciò che vedi in questa pagina:
- Prodotti con dimensioni, materiali, codici articolo
- Prezzi, importi, totali
- Nomi di aziende, fornitori, contatti
- Elementi grafici rilevanti (insegne, prospetti, schemi tecnici)
- Qualsiasi dato tecnico visibile
Sii preciso e strutturato. Non inventare dati non visibili.
```

### F2 — Agente conversazionale CLI

- Loop interattivo: domanda → retrieval → risposta
- L'agente usa `search_knowledge_base` come tool (built-in Agno)
- Il retrieval restituisce chunk sia di tipo `text` che `vision`
- Supporto domande multi-step e aggregate
- Comando `exit` per uscire

### F3 — Tipi di query supportate

**Query su testo:**
- "Qual è il prezzo della fioriera ONICE Ø1200?"
- "Quali sono le condizioni di pagamento di Metro Infissi?"
- "Elenca tutti i preventivi con totali IVA esclusa"

**Query su contenuti visivi:**
- "Come appare il prospetto Nord del Leonardo?"
- "Descrivi le insegne del prospetto Ovest"
- "Ci sono disegni tecnici con misure nella scheda ONICE?"

**Query aggregate multi-documento:**
- "Dammi un riepilogo costi per categoria di fornitura"
- "Differenza costo diurno vs notturno su tutte le insegne"
- "Quali offerte includono trasporto?"

### F4 — Qualità delle risposte
- Citare sempre il documento sorgente + tipo chunk (testo o visione)
- Se un dato viene da Vision description, indicarlo: "(da analisi immagine)"
- Non inventare dati non presenti nel KB
- Rispondere in italiano
- Importi: sempre specificare IVA inclusa/esclusa

---

## Dettagli Implementativi

### config.py
```python
DOCUMENTS_DIR = "documents/"
CHROMA_PATH = "chroma_db/"
CHROMA_COLLECTION = "preventivi_leonardo"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 6          # 3 text + 3 vision chunks
PAGE_DPI = 150             # risoluzione rasterizzazione pagine
VISION_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "gemini-embedding-exp-03-07"
```

### Configurazione Agno Agent
```python
from agno.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
from agno.models.deepseek import DeepSeek

Agent(
    model=DeepSeek(id="deepseek-chat"),
    knowledge=knowledge_base,
    search_knowledge=True,
    instructions=[
        "Sei un assistente specializzato nell'analisi di preventivi edilizi.",
        "Il progetto è il Centro Commerciale Leonardo di Imola (BO), cliente IABGroup.",
        "Cita sempre il documento sorgente nella risposta.",
        "Se un'informazione proviene dall'analisi visiva di una pagina, indicalo con '(da analisi immagine)'.",
        "Per gli importi specifica sempre se IVA inclusa o esclusa.",
        "Se non trovi l'informazione nel knowledge base, dillo chiaramente.",
        "Rispondi sempre in italiano.",
    ],
    show_tool_calls=True,
)
```

### Gestione PDF con encoding corrotto
`PROT_31_IAB_SOC_COOP__130125.pdf` ha encoding corrotto.
La pipeline deve:
1. Provare estrazione testo normale
2. Se testo estratto contiene >30% caratteri non-ASCII → considerarlo scansionato
3. In quel caso usare **solo** il passaggio Vision
4. Loggare il warning ma non bloccare l'ingestion degli altri PDF

---

## Requirements.txt

```
agno
chromadb
pymupdf
google-generativeai
python-dotenv
Pillow
```

---

## Fasi di Sviluppo

### Fase 1 — Pipeline testo + CLI (priorità)
- [ ] Setup progetto, dipendenze, .env
- [ ] Indicizzazione testo-only con GeminiEmbedder + ChromaDB
- [ ] Agente CLI base funzionante
- [ ] Test T1, T2, T3 (vedi sotto)

### Fase 2 — Pipeline Vision
- [ ] Rasterizzazione pagine con pymupdf
- [ ] Integrazione Gemini Vision per descrizione pagine
- [ ] Indicizzazione chunk vision in ChromaDB
- [ ] Gestione PDF con encoding corrotto
- [ ] Test T4, T5

### Fase 3 — Qualità
- [ ] Metadata arricchiti (fornitore, categoria, data offerta)
- [ ] Output tabellare per query aggregate
- [ ] Comando `--reindex` da CLI

### Fase 4 — Opzionale
- [ ] Interfaccia Streamlit
- [ ] Export risposta in markdown

---

## Note per Claude Code

1. **Inizia dalla Fase 1** — verifica che GeminiEmbedder + ChromaDB funzionino prima di aggiungere Vision
2. **Stessa GOOGLE_API_KEY** per embedding e Vision
3. **Costo Vision** — ~45 chiamate Gemini per 9 PDF da ~5 pagine. Accettabile per test, aggiungere rate limiting (1 req/sec)
4. **show_tool_calls=True** obbligatorio in sviluppo
5. **Non usare PDFKnowledgeBase built-in di Agno** — implementare pipeline custom in `ingestion/` per controllo completo
6. Chunk vision e testo separati ma stesso ChromaDB, differenziati via metadata `type`
7. Le immagini rasterizzate NON vanno salvate su disco — processare in memoria

---

## Criteri di Accettazione

| Test | Query | Risposta attesa |
|------|-------|-----------------|
| T1 | "Prezzo fioriera ONICE Ø1200?" | €746,20 — Metalco |
| T2 | "Totale insegne Prospetto Nord?" | €31.350 diurno / €32.755 notturno — Adriatica Neon |
| T3 | "Elenca tutti i fornitori" | Metalco, Adriatica Neon, Metro Infissi, Adria System |
| T4 | "Descrivi il prospetto Nord" | Risposta da chunk Vision con descrizione facciata |
| T5 | "Dimensioni fioriera ONICE dalla scheda" | Ø800/1200/1500mm con altezze e pesi (da Vision) |
| T6 | "Offerte con validità scaduta al 25/03/2026" | Metro Infissi 10gg da 16/01/2025, altri da valutare |
