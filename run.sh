#!/bin/bash
# Run the Streamlit app from the correct application path
cd "$(dirname "$0")"
python3 -m streamlit run app.py
