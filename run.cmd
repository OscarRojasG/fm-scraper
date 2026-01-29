@echo off
cd /d "C:\Users\oscar\OneDrive\Desktop\fm-scraper" || echo "No se encontró el directorio"
"C:\Users\oscar\OneDrive\Desktop\fm-scraper\.venv\Scripts\python.exe" "radio_api.py" || echo "No se encontró python.exe o radio_api.py"
echo Script terminado
pause