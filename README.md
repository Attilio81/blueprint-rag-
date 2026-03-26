# Agente RAG per i Preventivi — Guida Completa

> Questa guida è pensata per chi non ha mai sentito parlare di RAG o di AI applicata ai documenti.
> La leggi dall'inizio alla fine e alla fine sai usare il sistema.

---

## Indice

1. [Cos'è un RAG? (spiegazione per neofiti)](#1-cosè-un-rag-spiegazione-per-neofiti)
2. [Il problema che risolve questo progetto](#2-il-problema-che-risolve-questo-progetto)
3. [Come funziona — architettura semplificata](#3-come-funziona--architettura-semplificata)
4. [I componenti del sistema](#4-i-componenti-del-sistema)
5. [Come è strutturato il progetto](#5-come-è-strutturato-il-progetto)
6. [Prima installazione — passo passo](#6-prima-installazione--passo-passo)
7. [Indicizzare i PDF](#7-indicizzare-i-pdf)
8. [Fare domande all'agente](#8-fare-domande-allagente)
9. [Aggiungere nuovi documenti](#9-aggiungere-nuovi-documenti)
10. [Domande frequenti](#10-domande-frequenti)

---

## 1. Cos'è un RAG? (spiegazione per neofiti)

**RAG** sta per **Retrieval-Augmented Generation**, che in italiano possiamo chiamare
"generazione aumentata dal recupero". È una tecnica per far rispondere un'AI a domande
su documenti reali, senza "inventare" risposte.

### Il problema delle AI classiche

Un modello di linguaggio come ChatGPT è addestrato su miliardi di testi trovati su internet.
Sa moltissime cose di carattere generale. Ma **non conosce i tuoi documenti** —
i tuoi preventivi, le tue offerte, i tuoi schemi tecnici.

Se gli chiedi "Qual è il prezzo del prodotto X nel preventivo del fornitore Y?",
non sa rispondere. O peggio: inventa una risposta plausibile ma sbagliata.
Questo si chiama **allucinazione**.

### Come funziona il RAG

Il RAG risolve il problema in due passaggi:

```
[FASE 1 — INDICIZZAZIONE]

I tuoi PDF ──► Estrai il testo ──► Dividi in piccoli pezzi (chunk)
                                   ──► Converti ogni pezzo in un numero (embedding)
                                   ──► Salva in un database vettoriale

[FASE 2 — RISPOSTA]

La tua domanda ──► Converti anche lei in un numero (embedding)
               ──► Trova i pezzi più "vicini" per significato
               ──► Passa quei pezzi + la domanda all'AI
               ──► L'AI risponde basandosi SOLO su quei pezzi
```

### Il trucco degli "embedding"

Un **embedding** è la traduzione di un testo in un array di numeri (un vettore).
Testi con significato simile producono numeri simili. Quindi:

- "Prezzo fioriera grande" e "costo vaso esterno Ø1200" producono numeri vicini
- "Preventivo facciata nord" e "offerta insegne fronte edificio" producono numeri vicini

Questo permette di trovare documenti pertinenti anche se non usano le stesse parole
esatte della domanda.

---

## 2. Il problema che risolve questo progetto

Un progetto edilizio tipico accumula diversi preventivi da fornitori diversi, in formati diversi:

| Documento | Contenuto |
|-----------|-----------|
| `scheda_prodotto.pdf` | Scheda prodotto con prezzi e dimensioni |
| `preventivo_fornitore_a.pdf` | Preventivo Fornitore A per forniture |
| `offerta_insegne.pdf` | Offerta insegne e segnaletica |
| `offerta_facciata.pdf` | Offerta facciata continua |
| `preventivo_edile.pdf` | Preventivo lavori edili |
| `disegni_tecnici.pdf` | Disegni tecnici di facciata |
| `offerta_verde.pdf` | Offerta verde/giardino |

Senza il sistema, per rispondere a domande come "Qual è il totale delle insegne?"
bisognava aprire ogni PDF, cercare manualmente, fare calcoli.

**Con il sistema**, si scrive la domanda in italiano e si ottiene la risposta in pochi secondi,
con indicato il documento sorgente.

---

## 3. Come funziona — architettura semplificata

```
                    ┌─────────────────────────────────────────┐
                    │           FASE DI INDICIZZAZIONE        │
                    │          (si fa una volta sola)         │
                    └─────────────────────────────────────────┘

Preventivi/
├── scheda_prodotto.pdf ────────────────────────────────────────────────┐
├── offerta_facciata.pdf ───────────────────────────────────────────── │
├── preventivo_fornitore.pdf ────────────────────────────────────────── │
└── ... altri PDF ...                                                    │
                                                                         ▼
                                            ┌────────────────────────────────┐
                                            │      PIPELINE INGESTION        │
                                            │                                │
                                            │  Passaggio 1 — TESTO           │
                                            │  pymupdf estrae il testo       │
                                            │  grezzo da ogni pagina         │
                                            │                                │
                                            │  Passaggio 2 — VISIONE         │
                                            │  Ogni pagina viene             │
                                            │  "fotografata" e mandata a     │
                                            │  Gemini 2.5 Flash che la       │
                                            │  descrive in italiano          │
                                            └─────────────┬──────────────────┘
                                                          │
                                                          ▼
                                            ┌────────────────────────────────┐
                                            │    gemini-embedding-2-preview  │
                                            │                                │
                                            │  Ogni pezzo di testo diventa   │
                                            │  un vettore di 3072 numeri     │
                                            └─────────────┬──────────────────┘
                                                          │
                                                          ▼
                                            ┌────────────────────────────────┐
                                            │         ChromaDB               │
                                            │    (database vettoriale)       │
                                            │    salvato in chroma_db/       │
                                            └────────────────────────────────┘


                    ┌─────────────────────────────────────────┐
                    │           FASE DI RISPOSTA              │
                    │        (ogni volta che fai domande)     │
                    └─────────────────────────────────────────┘

Tu: "Qual è il prezzo del prodotto X nel preventivo?"
          │
          ▼
┌─────────────────────┐        ┌──────────────────────────────────────────┐
│ La domanda diventa  │        │  ChromaDB cerca i 6 chunk più simili     │
│ anche lei un vettore│──────► │  per significato alla domanda            │
│ di 3072 numeri      │        │  ("prodotto X", "prezzo", "preventivo")  │
└─────────────────────┘        └───────────────────┬──────────────────────┘
                                                    │
                                                    │  Restituisce i chunk più rilevanti:
                                                    │  "Codice prodotto X, dimensioni..."
                                                    │  "Prezzo: € XXX,XX IVA esclusa..."
                                                    │  ...
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │         DeepSeek Chat         │
                                    │                               │
                                    │  Riceve:                      │
                                    │  - I chunk trovati            │
                                    │  - La tua domanda             │
                                    │  - Le istruzioni del progetto │
                                    │                               │
                                    │  Risponde in italiano,        │
                                    │  citando la fonte             │
                                    └───────────────────────────────┘
                                                    │
                                                    ▼
                                    "Il prodotto X costa € XXX,XX IVA esclusa.
                                     Fonte: Fornitore A (preventivo_fornitore_a.pdf)"
```

---

## 4. I componenti del sistema

| Componente | Ruolo | Tecnologia |
|------------|-------|------------|
| **Estrazione testo** | Legge il testo dai PDF | `pymupdf` |
| **Visione pagine** | "Guarda" le immagini e le descrive | `Gemini 2.5 Flash` via `google.genai` |
| **Embedding** | Trasforma testi in numeri | `gemini-embedding-2-preview` (3072 dim.) |
| **Database vettoriale** | Archivia e cerca per similarità | `ChromaDB` (locale, nessun server) |
| **Knowledge base** | Collega embedding e ricerca | `Agno` framework |
| **Modello di chat** | Genera la risposta finale | `DeepSeek Chat` |
| **CLI** | Interfaccia utente a riga di comando | Python `argparse` + `input()` |
| **Deduplicazione** | Evita di re-indicizzare PDF già visti | SHA-256 hash + `indexed.json` |

---

## 5. Come è strutturato il progetto

```
C:\Progetti Pilota\EsploraPreventivi\
│
├── Preventivi\                  ← I tuoi PDF (metti qui i nuovi)
│   ├── scheda_prodotto.pdf
│   ├── preventivo_fornitore.pdf
│   └── ...
│
├── rag_preventivi\              ← Il codice del sistema
│   ├── config.py                ← Impostazioni (modelli, soglie, path)
│   ├── knowledge.py             ← Configura ChromaDB + GeminiEmbedder
│   ├── agent.py                 ← Crea l'agente DeepSeek
│   ├── main.py                  ← Punto di ingresso (lo esegui tu)
│   │
│   ├── ingestion\               ← Pipeline di indicizzazione
│   │   ├── text_extractor.py    ← Estrae testo con pymupdf
│   │   ├── image_extractor.py   ← Visione pagine con Gemini
│   │   └── pipeline.py          ← Orchestrazione + deduplicazione
│   │
│   └── tests\                   ← Test automatici (14 test)
│       ├── conftest.py
│       ├── test_text_extractor.py
│       ├── test_image_extractor.py
│       └── test_pipeline.py
│
├── chroma_db\                   ← Database vettoriale (auto-creato)
├── indexed.json                 ← Registro dei PDF già indicizzati
├── .env                         ← Le tue chiavi API (non condividere!)
├── .gitignore                   ← Protegge .env e chroma_db da git
└── README.md                    ← Questo file
```

---

## 6. Prima installazione — passo passo

### Prerequisiti

- Python 3.11 o superiore installato
- Connessione internet (per le API)
- Le chiavi API (vedi sotto)

### Passo 1 — Ottieni le chiavi API

Hai bisogno di due chiavi:

**Google API Key** (per Gemini Vision + Embedding):
1. Vai su [aistudio.google.com](https://aistudio.google.com)
2. Clicca su "Get API Key"
3. Copia la chiave (inizia con `AIza...`)

**DeepSeek API Key** (per il modello di chat):
1. Vai su [platform.deepseek.com](https://platform.deepseek.com/api_keys)
2. Crea un account e genera una chiave API
3. Copia la chiave

### Passo 2 — Crea il file .env

Nella cartella `C:\Progetti Pilota\EsploraPreventivi\` crea un file chiamato `.env`
(senza nome, solo estensione) con questo contenuto:

```
GOOGLE_API_KEY=AIzaSy...la_tua_chiave...
DEEPSEEK_API_KEY=sk-...la_tua_chiave...
```

> **Importante**: non condividere mai questo file. È già protetto da `.gitignore`
> quindi non viene mai caricato su git per errore.

### Passo 3 — Installa le dipendenze

Apri un terminale nella cartella del progetto e digita:

```bash
pip install -r rag_preventivi/requirements.txt
```

Questo installa: agno, chromadb, pymupdf, google-generativeai, python-dotenv, Pillow, pytest.

### Passo 4 — Verifica l'installazione

```bash
cd rag_preventivi
python -c "from knowledge import build_knowledge; kb, vdb = build_knowledge(); print('OK!')"
```

Se stampa `OK!` senza errori, sei pronto.

---

## 7. Indicizzare i PDF

L'indicizzazione è il processo che legge i PDF, li analizza e li salva nel database
vettoriale. Si fa **una volta sola** per ogni set di documenti. I documenti già
indicizzati vengono automaticamente saltati alle esecuzioni successive.

### Comando base

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python main.py --ingest-only
```

**Cosa succede:**

```
[INGEST] scheda_prodotto.pdf
  → 8 chunk testo
  → 2 chunk vision
  ✓ scheda_prodotto.pdf indicizzato

[INGEST] preventivo_fornitore.pdf
  → 20 chunk testo
  → 5 chunk vision
  ✓ preventivo_fornitore.pdf indicizzato

[SKIP] offerta_insegne.pdf già indicizzato    ← PDF non modificato, viene saltato
...
Ingestion completata.
```

**Quanto ci vuole?**
Per una decina di PDF: circa 3-5 minuti.
Il sistema processa ~1 pagina al secondo (limite di sicurezza dell'API Gemini).

### Re-indicizzare tutto da zero

Se vuoi rielaborare tutti i PDF (ad esempio dopo aver cambiato il modello di embedding):

```bash
python main.py --reindex --ingest-only
```

> **Attenzione**: `--reindex` cancella e ricostruisce tutti gli embedding.
> I PDF non vengono toccati, solo il database vettoriale.

### Cosa analizza il sistema per ogni pagina

Per ogni pagina di ogni PDF, il sistema fa **due passaggi**:

1. **Testo**: estrae il testo grezzo con `pymupdf`. Veloce, gratuito, funziona bene
   per PDF con testo selezionabile.

2. **Visione**: rasterizza la pagina come immagine (150 DPI) e la invia a
   `Gemini 2.5 Flash` che la "guarda" e produce una descrizione in italiano.
   Questo recupera informazioni da tabelle, schemi, loghi, elementi grafici
   che il testo grezzo non cattura.

> **Se un PDF è solo immagine** (scansionato, senza testo selezionabile),
> il sistema salta il passaggio testo e usa solo la visione.

---

## 8. Fare domande all'agente

### Avviare la chat

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python main.py
```

Vedrai:

```
=== Agente RAG Preventivi ===
Digita 'exit' per uscire.

Tu: _
```

Digita la tua domanda in italiano e premi Invio.

### Esempi di domande

**Prezzi e quantità:**
```
Tu: Qual è il prezzo del prodotto X?
Tu: Qual è il totale del preventivo del fornitore Y?
Tu: Elenca tutti i prodotti con il loro prezzo
```

**Fornitori:**
```
Tu: Chi sono i fornitori del progetto?
Tu: Chi fornisce le insegne luminose?
Tu: Quali sono i contatti del fornitore X?
```

**Elementi tecnici:**
```
Tu: Che sistema di facciata continua è previsto?
Tu: Dimensioni del prodotto X dalla scheda tecnica
Tu: Com'è descritto il prospetto principale?
```

**Confronti e analisi:**
```
Tu: Quale preventivo ha il totale più alto?
Tu: Ci sono informazioni sulle tempistiche di consegna?
```

### Come leggere la risposta

L'agente cita sempre la fonte:

```
Il prodotto X ha un prezzo di **€ XXX,XX IVA esclusa**.

Fonte: Fornitore A, preventivo_fornitore_a.pdf

---

Sono disponibili anche le taglie:
- Taglia S: dimensioni, peso → € [prezzo]
- Taglia L: dimensioni, peso → € [prezzo]
(da analisi immagine)
```

> La dicitura **"(da analisi immagine)"** indica che l'informazione viene
> da un chunk visione — l'AI ha visto la pagina come immagine, non come testo.

### Uscire dalla chat

Digita `exit`, `quit` oppure premi `Ctrl+C`.

---

## 9. Aggiungere nuovi documenti

### Aggiungere un PDF

1. Copia il PDF nella cartella `Preventivi\`
2. Esegui l'indicizzazione:

```bash
cd rag_preventivi
python main.py --ingest-only
```

Il sistema rileva automaticamente il nuovo file (hash SHA-256 non presente
in `indexed.json`) e lo indicizza. I file già indicizzati vengono saltati.

### Aggiornare un PDF esistente

Se modifichi un PDF già indicizzato:

1. Sovrascrivi il file nella cartella `Preventivi\`
2. Esegui `python main.py --ingest-only`

Il sistema rileva che l'hash è cambiato e re-indicizza automaticamente solo
quel file.

### Formati supportati

| Formato | Supportato | Note |
|---------|-----------|------|
| `.pdf` con testo selezionabile | ✅ | Testo + visione |
| `.pdf` scansionato (solo immagine) | ✅ | Solo visione (Gemini) |
| `.pdf` con encoding corrotto | ✅ | Salta testo, usa solo visione |
| `.xlsx` / `.xls` (Excel) | ❌ | Non ancora supportato |
| `.docx` (Word) | ❌ | Non ancora supportato |

---

## 10. Domande frequenti

### "L'agente ha risposto una cosa sbagliata"

Può succedere se l'informazione non è nei documenti indicizzati, o se è in una
parte del documento non estratta correttamente. Prova a:
- Riformulare la domanda con termini più vicini a quelli nel documento
- Verificare manualmente nel PDF di origine
- Se l'informazione è in una tabella o grafico complesso, potrebbe non essere
  stata estratta correttamente dalla visione

### "Ho ricevuto un errore 429"

Significa che hai superato il limite di chiamate all'API Gemini.
Il sistema ha già un rate limiting interno (1 richiesta/secondo).
Se persiste, attendi qualche minuto e riprova.

### "Il database vettoriale sembra corrotto"

Elimina la cartella `chroma_db\` e il file `indexed.json`, poi esegui:
```bash
python main.py --reindex --ingest-only
```

### "Voglio cambiare il modello di chat"

Modifica `agent.py`, riga con `DeepSeek(id="deepseek-chat")`.
Agno supporta anche: OpenAI GPT-4, Anthropic Claude, Google Gemini, ecc.

### "Come aggiungo Excel o Word?"

Bisogna aggiungere un nuovo estrattore in `ingestion/`. Per Excel con `openpyxl`:
- Crea `ingestion/excel_extractor.py`
- Estendi il glob in `pipeline.py` da `*.pdf` a `*.pdf` + `*.xlsx`

---

## Riepilogo dei comandi

```bash
# Prima installazione
pip install -r rag_preventivi/requirements.txt

# Indicizzare i PDF (prima volta o nuovi PDF)
python rag_preventivi/main.py --ingest-only

# Re-indicizzare tutto da zero
python rag_preventivi/main.py --reindex --ingest-only

# Avviare la chat
python rag_preventivi/main.py

# Eseguire i test automatici
cd rag_preventivi && python -m pytest tests/ -v
```

---

---

## Roadmap

| Priorità | Feature | Note |
|----------|---------|------|
| 🔜 | **Integrazione database SQL** | Collegare l'agente a un DB relazionale (es. storico ordini, anagrafica fornitori). L'agente potrà rispondere a domande che combinano i PDF con dati strutturati. |
| 🔜 | **Supporto Excel (.xlsx)** | Aggiungere `excel_extractor.py` con `openpyxl` per indicizzare anche i fogli di calcolo. |
| 💡 | **Supporto Word (.docx)** | Estendere la pipeline con `python-docx`. |
| 💡 | **Interfaccia web** | Sostituire la CLI con una UI (es. Gradio o Streamlit) per utenti non tecnici. |
| 💡 | **Multimodal embedding diretto** | Embeddare le immagini delle pagine direttamente con `gemini-embedding-2-preview` senza passare per la descrizione testuale, per retrieval ancora più accurato. |

---

*Stack: Python · Agno · DeepSeek · Gemini · ChromaDB · pymupdf*
