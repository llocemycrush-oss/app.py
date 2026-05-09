# Ailyn Construction Management App

This app is a Streamlit-based construction and payroll management dashboard with offline backup support.

## Features

- Online mode: all features available, including email report sending
- Offline mode: local save, inventory tracking, attendance recording, receipt capture, and automatic backups
- Automatic backup before every save
- Manual restore from backup through the sidebar
- Local persistence via `aily_data.json`

## Installation

1. Create a Python 3.10+ environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install requirements

```bash
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

Then open the browser at:

```text
http://localhost:8501
```

Do not add `/app.py` to the URL, or the page may return a 404 error.

## Notes

- `backups/` will be created automatically when the app saves data
- Use the sidebar mode switch to select `Online` or `Offline`
- In offline mode, email sending is disabled, but local backup and save works without mobile data
- If you want a published installable app, you can deploy this to any Streamlit hosting provider or package it with a Python installer tool
