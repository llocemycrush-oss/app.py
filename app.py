import streamlit as st
import smtplib
import pandas as pd
from datetime import datetime
from email.message import EmailMessage

# ═════════════════ CONFIGURATION ═════════════════
SENDER_EMAIL = "garryboypepito71@gmail.com"
SENDER_PASSWORD = "fhyv cimp gync wjmj"
RECEIVER_EMAILS = ["garryboypepito2004@gmail.com"] 
# ═════════════════════════════════════════════════

st.set_page_config(page_title="AILYN TERMINAL", layout="centered")

# Custom Terminal Styling
st.markdown("""
    <style>
    .terminal-box {
        font-family: 'Courier New', Courier, monospace;
        background-color: #1e1e1e;
        color: #cccccc;
        padding: 20px;
        border: 2px solid #444;
        border-radius: 5px;
        line-height: 1.2;
    }
    .terminal-header {
        text-align: center;
        border-bottom: 1px solid #444;
        margin-bottom: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'records' not in st.session_state:
    st.session_state.records = []
if 'budget' not in st.session_state:
    st.session_state.budget = 0.0

def send_email_report(records, budget, balance):
    msg = EmailMessage()
    msg["Subject"] = f"AILYN CONSTRUCTION - INVENTORY RECEIPT - {datetime.now().strftime('%b %d, %Y')}"
    msg["From"] = f"AILYN SYSTEM <{SENDER_EMAIL}>"
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    # Logic to categorize items for the email
    budget_rows = f"<tr><td style='padding:8px;'>{datetime.now().strftime('%b %d, %Y')}</td><td style='padding:8px;'>INITIAL PROJECT BUDGET ALLOCATION</td><td style='padding:8px; text-align:right;'>PHP {budget:,.2f}</td></tr>"
    
    expense_rows, deduction_rows = "", ""
    material_total, deduction_total = 0, 0

    for r in records:
        if any(word in r['What'].upper() for word in ["SOBRE", "DEDUCT", "LEFTOVER", "LESS"]):
            deduction_total += r['Amount']
            deduction_rows += f"<tr><td style='padding:8px; border-bottom:1px solid #1b5e20;'>{r['Date']}</td><td style='padding:8px; border-bottom:1px solid #1b5e20;'>{r['What']}</td><td style='padding:8px; border-bottom:1px solid #1b5e20; text-align:right; color: #d32f2f;'>- PHP {r['Amount']:,.2f}</td></tr>"
        else:
            material_total += r['Amount']
            expense_rows += f"<tr><td style='padding:8px; border-bottom:1px solid #1b5e20;'>{r['Date']}</td><td style='padding:8px; border-bottom:1px solid #1b5e20;'>1</td><td style='padding:8px; border-bottom:1px solid #1b5e20;'>{r['What']}</td><td style='padding:8px; border-bottom:1px solid #1b5e20; text-align:right;'>{r['Amount']:,.2f}</td><td style='padding:8px; border-bottom:1px solid #1b5e20; text-align:right;'>PHP {r['Amount']:,.2f}</td></tr>"

    html_body = f"""
    <html><body style="font-family: sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 800px; margin: auto; background: white; padding: 20px; border: 1px solid #ddd;">
            <p>Good Day!</p>
            <div style="background-color: #1b5e20; color: white; padding: 20px;">
                <h1 style="margin: 0;">AILYN CONSTRUCTION<span style="font-weight: normal;"> INVENTORY RECEIPT</span></h1>
            </div>
            <h4 style="color: #1b5e20; background: #f2f2f2; padding: 5px; margin-top: 20px;">BUDGET SUMMARY</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">{budget_rows}</table>
            <h4 style="color: #1b5e20; background: #f2f2f2; padding: 5px; margin-top: 20px;">DEDUCTIONS & LEFTOVERS</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">{deduction_rows if deduction_rows else "<tr><td>No deductions</td></tr>"}</table>
            <h4 style="color: #1b5e20; background: #f2f2f2; padding: 5px; margin-top: 20px;">MATERIALS & EXPENSES</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">{expense_rows}</table>
            <div style="background-color: #1b5e20; color: white; padding: 20px; border-radius: 10px; margin-top: 30px; width: 60%;">
                <p>Material Total: PHP {material_total:,.2f}</p>
                <p>Deduction: PHP {deduction_total:,.2f}</p>
                <p>Budget: PHP {budget:,.2f}</p>
                <h2 style="border-top: 1px dashed white; padding-top: 10px;">FINAL BALANCE: PHP {balance:,.2f}</h2>
            </div>
        </div>
    </body></html>
    """
    msg.add_alternative(html_body, subtype='html')
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        st.success("✅ SYSTEM: DATA EXPORTED SUCCESSFULLY")
    except Exception as e:
        st.error(f"❌ SYSTEM ERROR: {e}")

# --- TERMINAL UI ---
now = datetime.now()
mat_total = sum(r['Amount'] for r in st.session_state.records)
balance = st.session_state.budget - mat_total

st.markdown(f"""
    <div class="terminal-box">
        <div class="terminal-header">👷 WELCOME TO AILYN CONSTRUCTION</div>
        <div style="text-align: center; margin-bottom: 10px;">{now.strftime('%b %d, %Y  |  %I:%M %p')}</div>
        <div style="border-top: 1px solid #444; padding-top: 10px;">
            BUDGET: PHP {st.session_state.budget:>10,.2f}  |  BALANCE: PHP {balance:>10,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("[1] SET BUDGET"): st.session_state.trigger = "budget"
    if st.button("[3] DEDUCT LEFTOVER"): st.session_state.trigger = "deduct"
    if st.button("[5] EXPORT & SEND"): send_email_report(st.session_state.records, st.session_state.budget, balance)
with col2:
    if st.button("[2] NEW MATERIAL ENTRY"): st.session_state.trigger = "entry"
    if st.button("[4] OTHER EXPENSES"): st.session_state.trigger = "other"
    if st.button("[6] RESET LIST"): 
        st.session_state.records = []
        st.rerun()

active_mode = st.session_state.get("trigger", "entry")
if active_mode == "budget":
    new_b = st.number_input("ENTER NEW BUDGET:", value=st.session_state.budget)
    if st.button("UPDATE BUDGET"):
        st.session_state.budget = new_b
        st.rerun()
else:
    with st.form("cmd_form", clear_on_submit=True):
        st.write(f"MODE: {active_mode.upper()}")
        who = st.text_input("WHO (Person/Store)").upper()
        what = st.text_input("WHAT (Item/Reason)").upper()
        amt = st.number_input("AMOUNT", min_value=0.0)
        if st.form_submit_button("EXECUTE ENTRY"):
            if who and what and amt > 0:
                st.session_state.records.append({"Date": now.strftime("%Y-%m-%d"), "Who": who, "What": what, "Amount": amt})
                st.rerun()

if st.session_state.records:
    st.table(pd.DataFrame(st.session_state.records))