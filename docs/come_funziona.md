# Come funziona il sistema — spiegazione per tutti

> Questo documento spiega come funziona il sistema dall'inizio alla fine,
> con esempi concreti. Non è necessario sapere programmare per capirlo.

---

## Il problema di partenza

Immagina di avere sul tuo desktop questa situazione:

```
Preventivi\
├── preventivo_facciata_nord.pdf       (42 pagine)
├── offerta_insegne_luminose.pdf       (18 pagine)
├── preventivo_verde_giardino.pdf      (11 pagine)
├── scheda_tecnica_serramenti.pdf      (27 pagine)
├── offerta_pavimentazione.pdf         (33 pagine)
└── preventivo_impianto_elettrico.pdf  (55 pagine)
```

Il tuo responsabile ti chiama e chiede:
> *"Quanto costano in totale le insegne? E chi le fornisce?"*

Senza il sistema: apri ogni PDF, scorri le pagine, cerchi i numeri, sommi a mano.
Con i preventivi sopra: **almeno 20-30 minuti**.

Con il sistema: scrivi la domanda, leggi la risposta. **30 secondi.**

---

## L'analogia della biblioteca

Prima di spiegare il sistema, usiamo un'analogia.

Immagina una **biblioteca specializzata** con un assistente molto preparato:

1. **Ogni libro** della biblioteca è uno dei tuoi PDF
2. **Il bibliotecario** ha letto tutto, parola per parola
3. **Il catalogo** è un registro speciale che sa dove trovare ogni concetto
4. Quando fai una domanda, il bibliotecario **consulta il catalogo**, trova le pagine
   giuste, le rilegge, e ti dà una risposta precisa citando il libro e la pagina

Il nostro sistema funziona esattamente così — solo che lo fa in pochi secondi
e non dimentica mai niente.

---

## Le due fasi del sistema

Il sistema lavora in due momenti distinti:

```
┌─────────────────────────────────────────────────────────┐
│  FASE 1 — STUDIO (si fa una volta sola)                 │
│  Il sistema legge tutti i PDF e costruisce il catalogo  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  FASE 2 — RISPOSTA (ogni volta che fai una domanda)     │
│  Il sistema consulta il catalogo e risponde             │
└─────────────────────────────────────────────────────────┘
```

---

## FASE 1 — Come il sistema "studia" i tuoi PDF

### Passo 1 — Aprire il PDF e leggere il testo

Il sistema apre ogni PDF e legge il testo selezionabile, esattamente come faresti
tu selezionando il testo con il mouse.

**Esempio concreto:**

Dal file `offerta_insegne_luminose.pdf`, pagina 3, il sistema legge:

```
INSEGNA LUMINOSA FRONTE PRINCIPALE
Tipo: LED RGB, profilo alluminio anodizzato
Dimensioni: 8.400 x 600 mm
Colore: Pantone 485 (rosso)
Prezzo unitario: € 4.200,00 IVA esclusa
Quantità: 1
Totale: € 4.200,00
```

> Questo funziona bene per PDF "normali" dove il testo è selezionabile.
> Ma molti preventivi hanno **tabelle grafiche**, **loghi**, **schemi** —
> il testo puro non basta.

---

### Passo 2 — "Fotografare" ogni pagina e farla descrivere

Per ogni pagina, il sistema fa uno screenshot (come se premessi Stamp su quella pagina)
e lo manda a un modello di intelligenza artificiale con "occhi" — il **vision provider**.

Il modello guarda l'immagine e produce una descrizione strutturata in Markdown.

**Esempio concreto:**

La pagina 5 di `offerta_insegne_luminose.pdf` contiene una tabella grafica.
Il sistema la "fotografa" e la manda al modello vision, che risponde:

```markdown
## Riepilogo offerta insegne

| Codice | Descrizione | Qt | Prezzo unit. | Totale |
|--------|-------------|-----|--------------|--------|
| INS-001 | Insegna LED fronte principale 8.4m | 1 | € 4.200,00 | € 4.200,00 |
| INS-002 | Insegna LED ingresso secondario 3.2m | 2 | € 1.800,00 | € 3.600,00 |
| INS-003 | Totem segnaletica parcheggio h=3m | 4 | € 950,00 | € 3.800,00 |

**Totale offerta: € 11.600,00 IVA esclusa**
**Fornitore: Luminex Srl — info@luminex.it — Tel. 051 123456**
```

Questa descrizione contiene molto più di quello che si poteva leggere dal testo grezzo.

> **Quale "occhio" usa il sistema?**
> Si può scegliere in `config.py`:
> - **LM Studio** — un modello AI che gira sul tuo PC, gratis, privato
> - **Gemini** — il modello Google, via internet, qualità eccellente
> - **OpenAI** — il modello di ChatGPT, via internet

---

### Passo 3 — Tagliare il testo in pezzi (chunk)

Il testo estratto (sia quello letto che quello descritto dal modello vision)
viene tagliato in **pezzi di circa 1.000 caratteri**.

Perché? Perché il sistema non può lavorare con documenti enormi tutti insieme —
è come cercare una parola in un libro intero vs cercarla in singoli capitoli.

**Il trucco importante:** il sistema non taglia mai nel mezzo di una riga.
Cerca sempre il punto di taglio più naturale:

```
1° scelta: taglia tra un paragrafo e l'altro   ← preferito
2° scelta: taglia tra una riga e l'altra
3° scelta: taglia tra una parola e l'altra
4° scelta: taglia sui caratteri               ← solo se non c'è alternativa
```

**Esempio concreto — cosa succede a una tabella:**

```
Testo originale (1.800 caratteri):

## Offerta serramenti
| Codice | Descrizione        | Qt | Prezzo  |
| S-001  | Porta ingresso     |  2 | 1.200   |
| S-002  | Finestra 100x140   | 12 |   380   |
| S-003  | Finestra 60x90     |  8 |   220   |
| S-004  | Portafinestra      |  4 |   890   |
**Totale: € 12.560,00**

## Note tecniche
Profilo PVC serie 70 con doppio vetro 4-16-4.
Colore: RAL 9016 bianco traffico.
```

Il sistema taglia tra i due paragrafi (dopo `€ 12.560,00`), producendo:

```
Chunk 1:
## Offerta serramenti
| Codice | Descrizione        | Qt | Prezzo  |
| S-001  | Porta ingresso     |  2 | 1.200   |
| S-002  | Finestra 100x140   | 12 |   380   |
| S-003  | Finestra 60x90     |  8 |   220   |
| S-004  | Portafinestra      |  4 |   890   |
**Totale: € 12.560,00**

Chunk 2:
## Note tecniche
Profilo PVC serie 70 con doppio vetro 4-16-4.
Colore: RAL 9016 bianco traffico.
```

La riga `| S-002 | Finestra 100x140 | 12 | 380 |` rimane **sempre intera**,
mai tagliata nel mezzo.

---

### Passo 4 — Trasformare ogni pezzo in coordinate (embedding)

Qui arriva la parte più magica. Ogni pezzo di testo viene trasformato in
una lista di **3.072 numeri** — una specie di coordinata GPS del suo significato.

**Perché numeri?** Perché il computer non capisce le parole, ma capisce i numeri
e sa calcolare distanze tra numeri.

L'idea fondamentale è questa:

```
"Insegna LED fronte principale"  →  [0.23, -0.87, 0.44, 0.12, ...]
"Cartello luminoso facciata"     →  [0.21, -0.85, 0.47, 0.10, ...]  ← vicini!
"Preventivo verde giardino"      →  [-0.91, 0.33, -0.55, 0.78, ...] ← lontani
```

Testi con **significato simile** producono numeri **simili**.
Testi con **significato diverso** producono numeri **diversi**.

Questo è il segreto per cui il sistema capisce che "insegna" e "cartello luminoso"
parlano della stessa cosa, anche se usano parole diverse.

**Chi fa questa trasformazione?**
Il modello `gemini-embedding-2-preview` di Google — specializzato proprio
in questo compito, funziona in tutte le lingue.

---

### Passo 5 — Salvare tutto nel database

Ogni pezzo (chunk) viene salvato in un database speciale chiamato **ChromaDB**,
che vive sul tuo PC nella cartella `chroma_db\`.

Ogni riga del database contiene:
- Il testo originale del chunk
- I 3.072 numeri (la sua "coordinata GPS")
- Da quale file viene
- Da quale pagina viene
- Se è testo o descrizione di immagine

**Esempio di come appare il database internamente:**

```
ID  │ Testo                              │ Numeri GPS    │ File                    │ Pag │ Tipo
────┼────────────────────────────────────┼───────────────┼─────────────────────────┼─────┼──────
 1  │ "Insegna LED fronte 8.4m €4.200"  │ [0.23,-0.87…] │ offerta_insegne.pdf     │  3  │ testo
 2  │ "| INS-001 | Insegna... | 4.200"  │ [0.21,-0.85…] │ offerta_insegne.pdf     │  5  │ vision
 3  │ "Totale offerta: €11.600,00"       │ [0.19,-0.82…] │ offerta_insegne.pdf     │  5  │ vision
 4  │ "Fornitore: Luminex Srl..."        │ [0.44, 0.12…] │ offerta_insegne.pdf     │  6  │ testo
...
```

**Questo si fa una volta sola.** Quando aggiungi un nuovo PDF, il sistema
aggiunge solo le righe relative a quel file — non rilegge tutto da capo.
Sa già quali file ha già visto grazie a un registro chiamato `indexed.json`.

---

## FASE 2 — Come il sistema risponde alle tue domande

### Passo 1 — Trasformare la domanda in numeri

Quando scrivi una domanda, questa viene trasformata negli stessi 3.072 numeri
con lo stesso modello usato durante l'indicizzazione.

```
Tu scrivi: "Quanto costano le insegne luminose?"
                        │
                        ▼
              gemini-embedding
                        │
                        ▼
              [0.20, -0.84, 0.46, ...]
```

---

### Passo 2 — Trovare i pezzi più vicini

Il database confronta i tuoi numeri con tutti i numeri salvati e trova
i **6 chunk più vicini per significato** — come cercare le coordinate GPS
più vicine alla tua posizione.

```
La tua domanda:  [0.20, -0.84, 0.46, ...]

Distanza dal chunk 1 ("Insegna LED fronte €4.200"):  0.03  ✅ molto vicino
Distanza dal chunk 2 ("| INS-001 | Insegna | 4.200"): 0.05  ✅ molto vicino
Distanza dal chunk 3 ("Totale offerta: €11.600"):     0.08  ✅ vicino
Distanza dal chunk 4 ("Fornitore: Luminex Srl"):      0.12  ✅ vicino
...
Distanza dal chunk 38 ("Profilo PVC serramenti"):     1.82  ❌ lontano, scartato
```

Il sistema prende i 6 chunk più vicini e li passa al passaggio successivo.

---

### Passo 3 — DeepSeek legge i pezzi e risponde

I 6 chunk selezionati vengono inviati al modello di chat **DeepSeek** insieme
alla tua domanda. DeepSeek legge il contesto e formula una risposta in italiano.

**Cosa vede DeepSeek:**

```
[CONTESTO DAI DOCUMENTI]

--- Da offerta_insegne_luminose.pdf, pagina 3 ---
INSEGNA LUMINOSA FRONTE PRINCIPALE
Tipo: LED RGB, profilo alluminio anodizzato
Prezzo unitario: € 4.200,00 IVA esclusa. Quantità: 1

--- Da offerta_insegne_luminose.pdf, pagina 5 (analisi immagine) ---
| INS-001 | Insegna LED fronte principale 8.4m | 1 | € 4.200,00 | € 4.200,00 |
| INS-002 | Insegna LED ingresso secondario 3.2m | 2 | € 1.800,00 | € 3.600,00 |
| INS-003 | Totem segnaletica parcheggio h=3m | 4 | € 950,00 | € 3.800,00 |
Totale offerta: € 11.600,00 IVA esclusa

--- Da offerta_insegne_luminose.pdf, pagina 6 ---
Fornitore: Luminex Srl — info@luminex.it — Tel. 051 123456

[DOMANDA]
Quanto costano le insegne luminose?

[ISTRUZIONE]
Rispondi in italiano citando sempre la fonte.
```

**Risposta di DeepSeek:**

```
Le insegne luminose previste nel progetto hanno un costo totale di
**€ 11.600,00 IVA esclusa**, così suddivise:

| Descrizione | Qt | Totale |
|-------------|-----|--------|
| Insegna LED fronte principale (8,4 m) | 1 | € 4.200,00 |
| Insegna LED ingresso secondario (3,2 m) | 2 | € 3.600,00 |
| Totem segnaletica parcheggio (h = 3 m) | 4 | € 3.800,00 |

**Fornitore:** Luminex Srl — info@luminex.it — Tel. 051 123456

Fonte: offerta_insegne_luminose.pdf, pagine 3 e 5
```

---

## Tutto il flusso in una sola immagine

```
                         ╔═══════════════════════════╗
                         ║  I TUOI PDF               ║
                         ║  offerta_insegne.pdf      ║
                         ║  preventivo_facciata.pdf  ║
                         ║  ...                      ║
                         ╚═══════════╤═══════════════╝
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
          ┌──────────────────┐             ┌──────────────────────┐
          │  TESTO           │             │  VISIONE             │
          │  pymupdf legge   │             │  screenshot pagina   │
          │  il testo grezzo │             │  → modello AI        │
          └────────┬─────────┘             │  → Markdown          │
                   │                       └──────────┬───────────┘
                   │                                  │
                   └────────────┬─────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  CHUNKING             │
                    │  taglia rispettando   │
                    │  paragrafi e righe    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  EMBEDDING            │
                    │  ogni chunk diventa   │
                    │  3.072 numeri         │
                    │  (Gemini)             │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  ChromaDB             │
                    │  database sul tuo PC  │
                    │  testo + numeri       │
                    └───────────────────────┘

                           (sopra: fase 1 — una volta sola)
══════════════════════════════════════════════════════════════════
                           (sotto: fase 2 — ad ogni domanda)

                    ┌───────────────────────┐
                    │  La tua domanda       │
                    │  "Costo insegne?"     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  EMBEDDING domanda    │
                    │  → 3.072 numeri       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  ChromaDB             │
                    │  trova i 6 chunk      │
                    │  più vicini           │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  DeepSeek Chat        │
                    │  legge i chunk +      │
                    │  la domanda           │
                    │  → risposta italiana  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ╔═══════════════════════╗
                    ║  "Le insegne costano  ║
                    ║  € 11.600,00.         ║
                    ║  Fornitore: Luminex"  ║
                    ╚═══════════════════════╝
```

---

## Perché il sistema non "inventa"

Questa è la domanda più importante.

I modelli AI classici (come ChatGPT usato da solo) rispondono basandosi
su tutto quello che hanno imparato durante il training — miliardi di testi.
Se non sanno qualcosa, **lo inventano in modo convincente**. Questo si chiama
allucinazione.

Il nostro sistema è diverso: **DeepSeek non risponde mai da solo**.
Risponde solo basandosi sui chunk che gli vengono passati.
Se l'informazione non è nei chunk, dice che non la trova.

È come la differenza tra:
- Un testimone che **ricorda** (può sbagliarsi, può inventare)
- Un testimone che **legge dalla carta** (dice solo quello che c'è scritto)

DeepSeek legge dalla carta. La carta sono i tuoi PDF.

---

## Il "modello con gli occhi" — perché serve

Molti preventivi non sono documenti di testo puro. Contengono:

- **Tabelle grafiche** disegnate in Word o InDesign — il testo non è selezionabile
- **Prezzi in celle colorate** — il colore ha significato ma il testo grezzo non lo cattura
- **Schemi tecnici** con quote e misure integrate nell'immagine
- **Loghi e timbri** dei fornitori
- **PDF scansionati** — sono fotografie, non testo

Senza il modello vision, queste informazioni andrebbero perse.
Con il modello vision, ogni pagina viene "guardata" e descritta in parole,
recuperando tutto quello che c'è.

**Quale modello vision scegliere:**

| Situazione | Consiglio |
|------------|-----------|
| Vuoi privacy totale, hai un PC potente | LM Studio con Qwen3.5-9B |
| Vuoi la qualità migliore, non hai GPU | Gemini via API Google |
| Hai già un account OpenAI | OpenAI GPT-4o |

Si cambia una riga in `config.py` — nessun altro file va toccato.

---

## Cosa succede quando aggiungi un nuovo PDF

Il sistema non rilegge tutto da zero. Funziona così:

1. Calcola un'**impronta digitale** (hash SHA-256) del nuovo file — è come
   una firma unica che identifica quel preciso file
2. Controlla se quella firma è già nel registro `indexed.json`
3. Se **non c'è** → indicizza solo quel file e aggiunge la firma al registro
4. Se **c'è già** → salta, il file non è cambiato

Se modifichi un PDF esistente, la sua firma cambia e il sistema lo re-indicizza
automaticamente.

---

## Cosa succede se fai una domanda su qualcosa che non c'è

Se chiedi "Qual è il prezzo del marmo rosa del Portogallo?" e quel materiale
non è in nessun preventivo, il sistema risponde onestamente:

```
Non ho trovato informazioni sul marmo rosa del Portogallo
nei documenti disponibili.

Se vuoi, posso cercare sul web fornitori e prezzi di riferimento.
```

Puoi anche chiedere esplicitamente una ricerca web:
> *"Cercami sul web il prezzo medio del marmo rosa del Portogallo"*

E il sistema userà DuckDuckGo per cercare e riassumere i risultati,
citando le fonti web trovate.

---

## Riepilogo finale

| Domanda | Risposta semplice |
|---------|-------------------|
| **Come "sa" rispondere?** | Ha letto e catalogato tutti i tuoi PDF |
| **Perché non inventa?** | Risponde solo su quello che trova nei documenti |
| **Perché capisce "insegna" e "cartello luminoso"?** | Perché trasforma le parole in numeri e i numeri simili indicano significato simile |
| **Perché "fotografa" le pagine?** | Per leggere tabelle e grafici che il testo grezzo non cattura |
| **Dove si salvano i dati?** | Sul tuo PC, nella cartella `chroma_db\` |
| **I dati escono dal PC?** | Solo per l'embedding (Gemini) e la chat (DeepSeek), mai i PDF interi |
| **Quanto ci vuole per indicizzare?** | ~2-5 minuti per 10 PDF di media lunghezza |
| **Bisogna re-indicizzare ogni volta?** | No, solo quando aggiungi nuovi PDF |
