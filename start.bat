@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  EsploraPreventivi — Avvio servizi
echo ============================================================
echo.

REM ── MCP Server (finestra separata, background) ──────────────
echo [1/2] Avvio MCP Preventivi server...
start "MCP Preventivi" cmd /k "cd /d "%~dp0mcp_preventivi" && python server.py"

REM Breve pausa per lasciare avviare il server
timeout /t 2 /nobreak >nul

REM ── Streamlit App ───────────────────────────────────────────
echo [2/2] Avvio interfaccia chat (Streamlit)...
echo.
echo  Apri il browser su:  http://localhost:8501
echo.
echo  Per fermare tutto: chiudi questa finestra e quella "MCP Preventivi"
echo ============================================================
echo.

cd /d "%~dp0rag_preventivi"
streamlit run chat_app.py

endlocal
