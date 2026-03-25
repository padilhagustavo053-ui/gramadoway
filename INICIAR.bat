@echo off
cd /d "%~dp0"
echo ========================================
echo   GRAMADOWAY - Sistema de Pedidos
echo ========================================
echo.
echo Iniciando... Abra o navegador em http://localhost:8501
echo.
python -m streamlit run app.py --server.headless true
pause
