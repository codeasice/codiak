@echo off
echo Activating Virtual Environment
call .\venv\Scripts\activate.bat

echo Launching Codiak Streamlit
streamlit run app.py