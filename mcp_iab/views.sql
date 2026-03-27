-- ============================================================
-- MCP IAB Search — SQL Views
-- DB: IAB (codditt = 'IAB')
-- Scopo: esporre dati puliti per il server MCP di ricerca
--        articoli, fornitori, clienti e prezzi.
-- ============================================================

-- ------------------------------------------------------------
-- 1. v_articoli
--    Articoli con barcode aggregati.
--    Permette ricerca per codice, descrizione o EAN.
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.v_articoli AS
SELECT
    a.ar_codart                                         AS codart,
    RTRIM(a.ar_descr)                                   AS descrizione,
    RTRIM(ISNULL(a.ar_desint, ''))                      AS descrizione_interna,
    RTRIM(a.ar_unmis)                                   AS unita_misura,
    a.ar_blocco                                         AS bloccato,
    a.ar_inesaur                                        AS esaurito,
    a.ar_datini                                         AS data_inizio,
    a.ar_datfin                                         AS data_fine,
    STRING_AGG(RTRIM(b.bc_code), ', ')
        WITHIN GROUP (ORDER BY b.bc_code)               AS barcodes
FROM dbo.artico a
LEFT JOIN dbo.barcode b
    ON  a.codditt   = b.codditt
    AND a.ar_codart = b.bc_codart
WHERE a.codditt = 'IAB'
GROUP BY
    a.ar_codart,
    a.ar_descr,
    a.ar_desint,
    a.ar_unmis,
    a.ar_blocco,
    a.ar_inesaur,
    a.ar_datini,
    a.ar_datfin;
GO


-- ------------------------------------------------------------
-- 2. v_fornitori
--    Anagrafica fornitori (an_tipo = 'F').
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.v_fornitori AS
SELECT
    a.an_conto                      AS conto,
    RTRIM(a.an_descr1)              AS ragione_sociale,
    RTRIM(ISNULL(a.an_descr2, ''))  AS ragione_sociale2,
    RTRIM(ISNULL(a.an_pariva, ''))  AS partita_iva,
    RTRIM(ISNULL(a.an_codfis, ''))  AS codice_fiscale,
    RTRIM(ISNULL(a.an_email, ''))   AS email,
    RTRIM(ISNULL(a.an_telef, ''))   AS telefono,
    RTRIM(ISNULL(a.an_indir, ''))   AS indirizzo,
    RTRIM(ISNULL(a.an_citta, ''))   AS citta,
    RTRIM(ISNULL(a.an_prov, ''))    AS provincia
FROM dbo.anagra a
WHERE a.codditt = 'IAB'
  AND a.an_tipo = 'F';
GO


-- ------------------------------------------------------------
-- 3. v_clienti
--    Anagrafica clienti (an_tipo = 'C') con listino assegnato.
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.v_clienti AS
SELECT
    a.an_conto                      AS conto,
    RTRIM(a.an_descr1)              AS ragione_sociale,
    RTRIM(ISNULL(a.an_descr2, ''))  AS ragione_sociale2,
    RTRIM(ISNULL(a.an_pariva, ''))  AS partita_iva,
    RTRIM(ISNULL(a.an_email, ''))   AS email,
    RTRIM(ISNULL(a.an_telef, ''))   AS telefono,
    a.an_listino                    AS codice_listino,
    RTRIM(ISNULL(tl.tb_deslist, '')) AS nome_listino,
    RTRIM(ISNULL(a.an_indir, ''))   AS indirizzo,
    RTRIM(ISNULL(a.an_citta, ''))   AS citta,
    RTRIM(ISNULL(a.an_prov, ''))    AS provincia
FROM dbo.anagra a
LEFT JOIN dbo.tablist tl
    ON  a.codditt    = tl.codditt
    AND a.an_listino = tl.tb_codlist
WHERE a.codditt = 'IAB'
  AND a.an_tipo = 'C';
GO


-- ------------------------------------------------------------
-- 4. v_prezzi_acquisto
--    Prezzi di acquisto per articolo/fornitore validi oggi.
--    lc_conto > 0 = prezzo specifico per fornitore.
--    Validità: lc_datagg <= oggi <= lc_datscad
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.v_prezzi_acquisto AS
SELECT
    l.lc_codart                         AS codart,
    RTRIM(a.ar_descr)                   AS descrizione_articolo,
    l.lc_conto                          AS fornitore_conto,
    RTRIM(n.an_descr1)                  AS fornitore_nome,
    RTRIM(ISNULL(n.an_pariva, ''))      AS fornitore_piva,
    l.lc_prezzo                         AS prezzo,
    l.lc_listino                        AS codice_listino,
    RTRIM(ISNULL(tl.tb_deslist, ''))    AS nome_listino,
    RTRIM(ISNULL(l.lc_unmis, ''))       AS unita_misura,
    l.lc_daquant                        AS quantita_da,
    l.lc_aquant                         AS quantita_a,
    l.lc_netto                          AS prezzo_netto,
    l.lc_datagg                         AS data_inizio,
    l.lc_datscad                        AS data_scadenza
FROM dbo.listini l
JOIN dbo.anagra n
    ON  l.codditt  = n.codditt
    AND l.lc_conto = n.an_conto
    AND n.an_tipo  = 'F'
JOIN dbo.artico a
    ON  l.codditt   = a.codditt
    AND l.lc_codart = a.ar_codart
LEFT JOIN dbo.tablist tl
    ON  l.codditt    = tl.codditt
    AND l.lc_listino = tl.tb_codlist
WHERE l.codditt    = 'IAB'
  AND l.lc_conto   > 0
  AND l.lc_datagg  <= GETDATE()
  AND l.lc_datscad >= GETDATE();
GO


-- ------------------------------------------------------------
-- 5. v_codici_fornitore
--    Mapping codice articolo IAB <-> codice articolo fornitore.
--    Utile per trovare l'articolo IAB partendo dal codice
--    riportato nel preventivo del fornitore.
-- ------------------------------------------------------------
CREATE OR ALTER VIEW dbo.v_codici_fornitore AS
SELECT
    c.caf_codart                        AS codart,
    RTRIM(a.ar_descr)                   AS descrizione_articolo,
    c.caf_conto                         AS fornitore_conto,
    RTRIM(n.an_descr1)                  AS fornitore_nome,
    RTRIM(ISNULL(n.an_pariva, ''))      AS fornitore_piva,
    RTRIM(c.caf_codarfo)                AS codice_fornitore,
    RTRIM(ISNULL(c.caf_desnote, ''))    AS note
FROM dbo.codarfo c
JOIN dbo.anagra n
    ON  c.codditt  = n.codditt
    AND c.caf_conto = n.an_conto
    AND n.an_tipo  = 'F'
JOIN dbo.artico a
    ON  c.codditt   = a.codditt
    AND c.caf_codart = a.ar_codart
WHERE c.codditt = 'IAB';
GO
