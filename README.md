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
7. [Configurazione](#7-configurazione)
8. [Indicizzare i PDF](#8-indicizzare-i-pdf)
9. [Fare domande all'agente](#9-fare-domande-allagente)
10. [Aggiungere nuovi documenti](#10-aggiungere-nuovi-documenti)
11. [Adattare il sistema a un nuovo progetto](#11-adattare-il-sistema-a-un-nuovo-progetto)
12. [Domande frequenti](#12-domande-frequenti)

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
├── scheda_prodotto.pdf ──────────────────────────────────────────────────┐
├── offerta_facciata.pdf ─────────────────────────────────────────────── │
├── preventivo_fornitore.pdf ─────────────────────────────────────────── │
└── ... altri PDF ...                                                      │
                                                                           ▼
                                            ┌────────────────────────────────┐
                                            │      PIPELINE INGESTION        │
                                            │                                │
                                            │  Passaggio 1 — TESTO           │
                                            │  pymupdf estrae il testo       │
                                            │  grezzo da ogni pagina         │
                                            │  → chunk separator-aware       │
                                            │    (paragrafo › riga › parola) │
                                            │                                │
                                            │  Passaggio 2 — VISIONE         │
                                            │  Ogni pagina viene             │
                                            │  "fotografata" e mandata al    │
                                            │  vision provider configurato   │
                                            │  che la descrive in Markdown   │
                                            │  → chunk separator-aware       │
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
| **Chunking** | Divide il testo rispettando paragrafi, righe e parole | separator-aware (`\n\n` › `\n` › ` `) |
| **Vision provider** | "Guarda" le pagine e le descrive in Markdown strutturato | configurabile: LM Studio, Gemini, OpenAI (vedi §7) |
| **Embedding** | Trasforma testi in numeri | `gemini-embedding-2-preview` (3072 dim.) |
| **Database vettoriale** | Archivia e cerca per similarità | `ChromaDB` (locale, nessun server) |
| **Knowledge base** | Collega embedding e ricerca | `Agno` framework |
| **Modello di chat** | Genera la risposta finale | `DeepSeek Chat` |
| **Interfaccia web** | Chat + gestione documenti nel browser | `Streamlit` |
| **Ricerca web** | Trova fornitori e alternative online | `DuckDuckGo` via `ddgs` (no API key) |
| **CLI** | Interfaccia alternativa a riga di comando | Python `argparse` + `input()` |
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
│   ├── config.py                ← Impostazioni (modelli, soglie, path, vision provider, prompt)
│   ├── knowledge.py             ← Configura ChromaDB + GeminiEmbedder
│   ├── agent.py                 ← Crea l'agente DeepSeek + WebSearchTools
│   ├── chat_app.py              ← Interfaccia web Streamlit (avvia con streamlit run)
│   ├── admin_tab.py             ← Tab "Gestione": lista, upload, indicizza, elimina
│   ├── main.py                  ← CLI alternativa (argparse + input())
│   │
│   ├── ingestion\               ← Pipeline di indicizzazione
│   │   ├── text_extractor.py    ← Estrae testo con pymupdf + chunking separator-aware
│   │   ├── image_extractor.py   ← Visione pagine con provider configurabile (LM Studio / Gemini / OpenAI)
│   │   └── pipeline.py          ← Orchestrazione + deduplicazione + streaming log
│   │
│   └── tests\                   ← Test automatici (23 test)
│       ├── conftest.py
│       ├── test_text_extractor.py
│       ├── test_image_extractor.py
│       ├── test_pipeline.py
│       ├── test_agent.py
│       └── test_admin_tab.py
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
- Connessione internet (per le API di embedding e chat)
- Le chiavi API necessarie in base al vision provider scelto (vedi §7)

### Passo 1 — Installa le dipendenze

```bash
pip install -r rag_preventivi/requirements.txt
```

Installa: agno, chromadb, pymupdf, google-generativeai, openai, python-dotenv, Pillow, pytest, streamlit, ddgs.

### Passo 2 — Ottieni le chiavi API

Hai sempre bisogno di queste due:

**Google API Key** (per l'embedding):
1. Vai su [aistudio.google.com](https://aistudio.google.com)
2. Clicca su "Get API Key" e copia la chiave (inizia con `AIza...`)

**DeepSeek API Key** (per il modello di chat):
1. Vai su [platform.deepseek.com](https://platform.deepseek.com/api_keys)
2. Crea un account e genera una chiave API

In base al **vision provider** scelto (vedi §7), potrebbero servire chiavi aggiuntive:

| Provider | Chiave aggiuntiva |
|----------|-------------------|
| `lmstudio` | Nessuna — gira in locale |
| `gemini` | `GOOGLE_API_KEY` (già usata per l'embedding) |
| `openai` | `OPENAI_API_KEY` |

### Passo 3 — Crea il file .env

Nella cartella `C:\Progetti Pilota\EsploraPreventivi\` crea un file `.env`:

```
GOOGLE_API_KEY=AIzaSy...la_tua_chiave...
DEEPSEEK_API_KEY=sk-...la_tua_chiave...

# Solo se usi VISION_PROVIDER = "openai"
# OPENAI_API_KEY=sk-...la_tua_chiave...
```

> **Importante**: non condividere mai questo file. È già protetto da `.gitignore`.

### Passo 4 — (Solo per `lmstudio`) Configura LM Studio

1. Scarica e installa [LM Studio](https://lmstudio.ai)
2. Scarica il modello `qwen/qwen3.5-9b` dalla scheda "Discover"
3. Avvia il server locale: vai in "Developer" → "Start Server"
4. Il server gira su `http://localhost:1234`

### Passo 5 — Verifica l'installazione

```bash
cd rag_preventivi
python -c "from knowledge import build_knowledge; kb, vdb = build_knowledge(); print('OK!')"
```

Se stampa `OK!` senza errori, sei pronto.

---

## 7. Configurazione

Tutto si configura nel file `rag_preventivi/config.py`. Non è mai necessario toccare altri file.

### Parametri principali

```python
# ── Progetto ───────────────────────────────────────────────────────────────
PROJECT_CONTEXT = "preventivi edilizi del Centro Commerciale Leonardo di Imola"
CHROMA_COLLECTION = "preventivi_leonardo_v2"  # nome univoco per questo progetto

# ── Vision provider ────────────────────────────────────────────────────────
# "lmstudio"  — locale, gratis, privacy totale (richiede LM Studio in esecuzione)
# "gemini"    — API Google, qualità alta, richiede GOOGLE_API_KEY
# "openai"    — API OpenAI, richiede OPENAI_API_KEY
VISION_PROVIDER = "lmstudio"

# ── Vision prompt ──────────────────────────────────────────────────────────
# Il testo inviato al modello vision per descrivere ogni pagina.
# Personalizzalo per il tipo di documenti che indicizzi.
VISION_PROMPT = """Analizza questa pagina di documento commerciale.
Restituisci SOLO il contenuto in Markdown strutturato:
..."""

# ── Chunking ───────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1000   # caratteri massimi per chunk
CHUNK_OVERLAP = 200    # caratteri di sovrapposizione tra chunk adiacenti
```

### Vision provider — dettaglio

| Provider | Costo | Privacy | Qualità | Requisiti |
|----------|-------|---------|---------|-----------|
| `lmstudio` | Gratis | Locale | Alta (dipende dal modello) | LM Studio + GPU/RAM |
| `gemini` | Basso | Dati a Google | Ottima | `GOOGLE_API_KEY` |
| `openai` | Medio | Dati a OpenAI | Ottima | `OPENAI_API_KEY` |

Modelli consigliati per LM Studio:

| Modello | VRAM | Note |
|---------|------|------|
| `qwen/qwen3.5-9b` | ~8 GB | Ottimo per testi tecnici e tabelle, multilingue |
| `llava-v1.6` | ~6 GB | Buono per pagine con grafica |
| `minicpm-v` | ~4 GB | Leggero, per GPU con poca VRAM |

### Chunking — come funziona

Il sistema divide il testo in chunk cercando il confine più naturale disponibile:

```
1° tentativo: taglia su \n\n  (fine paragrafo)   ← preferito
2° tentativo: taglia su \n    (fine riga)
3° tentativo: taglia su spazio (fine parola)
4° tentativo: taglia sui caratteri               ← ultimo resort
```

Questo garantisce che una riga di tabella tipo `| P001 | Porta legno | 3 | €400 |`
non venga mai spezzata a metà.

---

## 8. Indicizzare i PDF

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
  → 4 chunk visione
  ✓ scheda_prodotto.pdf indicizzato

[INGEST] preventivo_fornitore.pdf
  → 20 chunk testo
  → 8 chunk visione
  ✓ preventivo_fornitore.pdf indicizzato

[SKIP] offerta_insegne.pdf già indicizzato    ← PDF non modificato, viene saltato
...
Ingestion completata.
```

**Quanto ci vuole?**
- Con `lmstudio`: ~2-5 sec/pagina (dipende dalla GPU), nessun rate limit
- Con `gemini`: ~1 pagina/secondo (rate limit integrato)
- Con `openai`: veloce, dipende dalla rete

### Re-indicizzare tutto da zero

Se vuoi rielaborare tutti i PDF (es. dopo aver cambiato il vision provider o il prompt):

```bash
python main.py --reindex --ingest-only
```

> **Attenzione**: `--reindex` cancella e ricostruisce tutti gli embedding.
> I PDF non vengono toccati, solo il database vettoriale.

### Cosa analizza il sistema per ogni pagina

Per ogni pagina di ogni PDF, il sistema fa **due passaggi**:

1. **Testo**: estrae il testo grezzo con `pymupdf`. Veloce, gratuito, funziona bene
   per PDF con testo selezionabile. Il testo viene diviso in chunk rispettando
   i confini naturali (paragrafi, righe).

2. **Visione**: rasterizza la pagina come immagine (150 DPI) e la invia al
   vision provider configurato, che la "guarda" e produce una descrizione Markdown
   strutturata. Questo recupera informazioni da tabelle, schemi, loghi, elementi
   grafici che il testo grezzo non cattura. Anche la descrizione viene chunckata
   rispettando i confini del Markdown.

> **Se un PDF è solo immagine** (scansionato, senza testo selezionabile),
> il sistema salta il passaggio testo e usa solo la visione.

---

## 9. Fare domande all'agente

Hai due modalità: **interfaccia web** (raccomandato) e **CLI** (terminale).

---

### Interfaccia web — Streamlit (raccomandato)

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
streamlit run chat_app.py
```

Si apre automaticamente il browser su `http://localhost:8501`. Trovi due tab:

**Tab "💬 Chat"** — scrivi le domande nella casella in basso e ottieni risposte in streaming:
- Le fonti RAG appaiono nell'expander **📄 Fonti documenti**
- Se hai chiesto una ricerca web, gli URL appaiono nell'expander **🌐 Fonti web**
- La conversazione ha memoria multi-turno (puoi fare domande di seguito)

**Tab "🗂 Gestione"** — gestisci i PDF senza toccare il filesystem:
- Lista documenti con stato (✅ Indicizzato / ⏳ Non indicizzato / ⚠️ Corrotto)
- Upload di nuovi PDF tramite drag & drop
- Bottone "▶️ Indicizza nuovi" con log in tempo reale
- Bottone "🔄 Re-indicizza tutto"
- Pulsante 🗑️ per eliminare un documento

---

### Ricerca web su richiesta

L'agente può cercare sul web quando glielo chiedi esplicitamente. Usa parole come:
- "Cercami sul web fornitori di serramenti in PVC"
- "Trova alternative online per questo prodotto"
- "Quali aziende vendono lo stesso articolo?"

Per domande sui preventivi, usa sempre il knowledge base (non va su internet da solo).

---

### CLI — riga di comando (alternativa)

```bash
cd "C:\Progetti Pilota\EsploraPreventivi\rag_preventivi"
python main.py
```

```
=== Agente RAG Preventivi ===
Digita 'exit' per uscire.

Tu: _
```

Digita la tua domanda in italiano e premi Invio. Digita `exit` o `quit` per uscire.

---

### Esempi di domande

**Prezzi e quantità:**
```
Qual è il prezzo del prodotto X?
Qual è il totale del preventivo del fornitore Y?
Elenca tutti i prodotti con il loro prezzo
```

**Fornitori:**
```
Chi sono i fornitori del progetto?
Chi fornisce le insegne luminose?
Quali sono i contatti del fornitore X?
```

**Elementi tecnici:**
```
Che sistema di facciata continua è previsto?
Dimensioni del prodotto X dalla scheda tecnica
```

**Ricerca web:**
```
Trovami fornitori alternativi per questo tipo di infissi
Cerca sul web il prezzo medio del calcestruzzo C25/30
```

### Come leggere la risposta

L'agente cita sempre la fonte:

```
Il prodotto X ha un prezzo di **€ XXX,XX IVA esclusa**.

Fonte: Fornitore A, preventivo_fornitore_a.pdf

Sono disponibili anche le taglie:
- Taglia S: dimensioni, peso → € [prezzo]
(da analisi immagine)
```

> La dicitura **"(da analisi immagine)"** indica che l'informazione viene
> da un chunk visione — il modello ha visto la pagina come immagine, non come testo.

---

## 10. Aggiungere nuovi documenti

### Metodo 1 — Interfaccia web (più semplice)

1. Apri l'app Streamlit (`streamlit run chat_app.py`)
2. Vai nella tab "🗂 Gestione"
3. Trascina il PDF nel campo upload — viene copiato automaticamente in `Preventivi\`
4. Clicca "▶️ Indicizza nuovi" — il log mostra il progresso in tempo reale

### Metodo 2 — CLI

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
| `.pdf` scansionato (solo immagine) | ✅ | Solo visione |
| `.pdf` con encoding corrotto | ✅ | Salta testo, usa solo visione |
| `.xlsx` / `.xls` (Excel) | ❌ | Non ancora supportato |
| `.docx` (Word) | ❌ | Non ancora supportato |

---

## 11. Adattare il sistema a un nuovo progetto

Il sistema è progettato per funzionare con qualsiasi tipo di preventivo o documento
commerciale. Per adattarlo, modifica **solo `config.py`**:

```python
# 1. Dai un nome al progetto e alla sua collection ChromaDB
PROJECT_CONTEXT  = "preventivi forniture hardware e software"
CHROMA_COLLECTION = "preventivi_informatica"

# 2. Scegli il vision provider più adatto
VISION_PROVIDER = "lmstudio"   # o "gemini" o "openai"

# 3. Personalizza il prompt per il tipo di documento
VISION_PROMPT = """Analizza questa pagina di offerta commerciale IT.
Restituisci SOLO il contenuto in Markdown strutturato:
- Usa tabelle Markdown (| Part Number | Descrizione | Qt | Prezzo unitario | Totale |)
- Usa ## per sezioni (hardware, software, servizi, licenze)
- Riporta: part number, SKU, versioni software, canoni annui, sconti
Non aggiungere testo non presente. Solo estrarre."""
```

Poi cancella `chroma_db/` e `indexed.json` (appartengono al progetto precedente)
e ri-indicizza i nuovi PDF.

**Esempi di prompt per altri domini:**

```python
# Forniture medicali
VISION_PROMPT = """Analizza questa pagina di offerta per forniture sanitarie.
Restituisci SOLO il contenuto in Markdown strutturato:
- Tabelle con (| Codice CND | Descrizione | Fabbricante | Qt | Prezzo |)
- ## per sezioni (dispositivi, farmaci, consumabili, servizi)
- Riporta: codici CND/RDM, fabbricante, numero di riferimento
Non aggiungere testo non presente. Solo estrarre."""

# Lavori edili generici
VISION_PROMPT = """Analizza questa pagina di computo metrico o preventivo edile.
Restituisci SOLO il contenuto in Markdown strutturato:
- Tabelle con (| Voce | Unità | Quantità | Prezzo unit. | Importo |)
- ## per categorie di lavoro (opere murarie, impianti, finiture...)
- Riporta: codici voce, unità di misura, prezzi unitari, totali parziali
Non aggiungere testo non presente. Solo estrarre."""
```

---

## 12. Domande frequenti

### "L'agente ha risposto una cosa sbagliata"

Può succedere se l'informazione non è nei documenti indicizzati, o se è in una
parte del documento non estratta correttamente. Prova a:
- Riformulare la domanda con termini più vicini a quelli nel documento
- Verificare manualmente nel PDF di origine
- Cambiare il vision provider o migliorare il `VISION_PROMPT` in `config.py`

### "Ho ricevuto un errore 429"

Significa che hai superato il limite di chiamate all'API Gemini.
Il sistema ha già un rate limiting interno per il provider Gemini.
Se persiste, attendi qualche minuto e riprova. Considera di passare a `lmstudio`
per eliminare il problema alla radice.

### "LM Studio non risponde"

Verifica che LM Studio sia in esecuzione e che il server locale sia avviato
("Developer" → "Start Server"). Il modello deve essere caricato prima di avviare
l'indicizzazione. Verifica che `LMSTUDIO_BASE_URL` in `config.py` corrisponda
alla porta mostrata da LM Studio (default: `http://localhost:1234/v1`).

### "Il modello in LM Studio ha un nome diverso"

Apri un terminale e lancia:
```bash
curl http://localhost:1234/v1/models
```
Copia il campo `id` del modello caricato e incollalo in `config.py` come `LMSTUDIO_VISION_MODEL`.

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

# Avviare l'interfaccia web (raccomandato)
streamlit run rag_preventivi/chat_app.py

# Indicizzare i PDF via CLI (prima volta o nuovi PDF)
python rag_preventivi/main.py --ingest-only

# Re-indicizzare tutto da zero via CLI
python rag_preventivi/main.py --reindex --ingest-only

# Avviare la chat CLI (alternativa alla web)
python rag_preventivi/main.py

# Eseguire i test automatici
cd rag_preventivi && python -m pytest tests/ -v

# Verificare il modello caricato in LM Studio
curl http://localhost:1234/v1/models
```

---

## Roadmap

| Stato | Feature | Note |
|-------|---------|------|
| ✅ | **Interfaccia web Streamlit** | Chat streaming + tab Gestione documenti |
| ✅ | **Ricerca web su richiesta** | DuckDuckGo via `ddgs`, solo su richiesta esplicita |
| ✅ | **Vision provider configurabile** | LM Studio (locale) / Gemini / OpenAI — si cambia una riga in `config.py` |
| ✅ | **Chunking separator-aware** | Rispetta paragrafi, righe di tabella e parole — nessun taglio a metà riga |
| ✅ | **Vision prompt parametrizzabile** | Personalizzabile per dominio in `config.py` |
| 🔜 | **MCP SQL — confronto Ordini Fornitori** | Collegare l'agente a un DB relazionale tramite MCP server. L'agente potrà confrontare i prezzi dei preventivi PDF con gli ordini fornitori già emessi, rilevare scostamenti e rispondere a domande che combinano documenti e dati strutturati. |
| 🔜 | **Supporto Excel (.xlsx)** | Aggiungere `excel_extractor.py` con `openpyxl` per indicizzare anche i fogli di calcolo. |
| 💡 | **Supporto Word (.docx)** | Estendere la pipeline con `python-docx`. |
| 💡 | **Embedding locale** | Sostituire Gemini embedding con FastEmbed `bge-m3` per privacy totale e zero costi. |

---

*Stack: Python · Agno · DeepSeek · Gemini Embedding · ChromaDB · pymupdf · Streamlit · DuckDuckGo · LM Studio (Qwen3.5)*
