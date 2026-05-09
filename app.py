import os
import time
import shutil
from datetime import datetime
import streamlit as st
import smtplib
from email.message import EmailMessage
import json
from pathlib import Path

# ═════════════════ CONFIGURATION ═════════════════
APP_VERSION = "AILY OS v30000 — GREEN EMERALD CORE"
RECEIVER_EMAIL = "garryboypepito2004@gmail.com"
RECEIVER_AILYN = "ailyn_peps0678@yahoo.com"
SENDER_EMAIL = "garryboypepito71@gmail.com"
SENDER_PASSWORD = "fhyv cimp gync wjmj"

# Data persistence files and backup
DATA_FILE = Path(__file__).resolve().parent / "aily_data.json"
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
MAX_BACKUPS = 30

# ═════════════════ PAGE CONFIG ═════════════════
st.set_page_config(
    page_title="Ailyn Construction Management",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════ SESSION STATE ═════════════════
if "records" not in st.session_state:
    st.session_state.records = []  # Material/Expense records

if "labor_records" not in st.session_state:
    st.session_state.labor_records = []  # Labor records

if "payroll_expenses" not in st.session_state:
    st.session_state.payroll_expenses = []  # Payroll expense records

if "budget" not in st.session_state:
    st.session_state.budget = 0.0

if "remaining_money" not in st.session_state:
    st.session_state.remaining_money = 0.0

if "view" not in st.session_state:
    st.session_state.view = "home"

if "mode" not in st.session_state:
    st.session_state.mode = "offline"  # offline or online

if "inventory" not in st.session_state:
    st.session_state.inventory = {}  # Track bag/piece counts

if "attendance" not in st.session_state:
    st.session_state.attendance = {}  # Daily attendance log

if "receipts" not in st.session_state:
    st.session_state.receipts = {}  # Receipt data storage

# ═════════════════ DATA PERSISTENCE ═════════════════
def ensure_storage():
    """Ensure the data directory and backup folder exist."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def archive_backup():
    """Archive the current data file before writing a new version."""
    if DATA_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"aily_data_backup_{timestamp}.json"
        shutil.copy2(DATA_FILE, backup_path)

        backups = sorted(
            BACKUP_DIR.glob("aily_data_backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink(missing_ok=True)
        return backup_path
    return None


def get_backups():
    """Return a sorted list of available backup paths."""
    ensure_storage()
    backups = sorted(
        BACKUP_DIR.glob("aily_data_backup_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return backups


def restore_backup(backup_path):
    """Restore data from a selected backup file."""
    if backup_path.exists():
        with open(backup_path, 'r') as f:
            data = json.load(f)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        load_data()
        return True
    return False


def save_data():
    """Save all data to persistent JSON file and archive the previous version."""
    ensure_storage()
    archive_backup()

    data = {
        "records": st.session_state.records,
        "labor_records": st.session_state.labor_records,
        "payroll_expenses": st.session_state.payroll_expenses,
        "budget": st.session_state.budget,
        "remaining_money": st.session_state.remaining_money,
        "mode": st.session_state.mode,
        "inventory": st.session_state.inventory,
        "attendance": st.session_state.attendance,
        "receipts": st.session_state.receipts
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_data():
    """Load all data from persistent JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        st.session_state.records = data.get("records", [])
        st.session_state.labor_records = data.get("labor_records", [])
        st.session_state.payroll_expenses = data.get("payroll_expenses", [])
        st.session_state.budget = data.get("budget", 0.0)
        st.session_state.remaining_money = data.get("remaining_money", 0.0)
        st.session_state.mode = data.get("mode", "offline")
        st.session_state.inventory = data.get("inventory", {})
        st.session_state.attendance = data.get("attendance", {})
        st.session_state.receipts = data.get("receipts", {})

# Load data on app start
load_data()

# ═════════════════ CORE LOGIC (MATERIAL/EXPENSE) ═════════════════
def set_view(v):
    st.session_state.view = v
    st.rerun()

def total_materials():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "material")

def total_expenses():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "expense")

def total_excess():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "excess")

def get_total():
    return total_materials() + total_expenses()

def get_balance():
    return float(st.session_state.budget) + total_excess() - get_total()

def clear_all():
    st.session_state.records = []
    st.session_state.labor_records = []
    st.session_state.payroll_expenses = []
    st.session_state.budget = 0.0
    st.session_state.remaining_money = 0.0
    st.session_state.inventory = {}
    st.session_state.attendance = {}
    st.session_state.receipts = {}
    save_data()

def add_tx(name, price, qty, delivery, ttype, sender, receipt_data=None):
    if float(price) <= 0 or int(qty) <= 0:
        return False

    amount = (float(price) * int(qty)) + float(delivery) if ttype == "material" else float(price)

    tx_id = str(time.time())
    st.session_state.records.append({
        "id": tx_id,
        "date": datetime.now().strftime("%b %d, %Y"),
        "name": name.upper(),
        "price": float(price),
        "qty": int(qty),
        "delivery": float(delivery),
        "amount": float(amount),
        "type": ttype,
        "sender": sender,
        "receipt": receipt_data
    })
    
    # Update inventory for materials
    if ttype == "material":
        if name.upper() not in st.session_state.inventory:
            st.session_state.inventory[name.upper()] = 0
        st.session_state.inventory[name.upper()] += int(qty)
    
    save_data()
    return True

# ═════════════════ ATTENDANCE & INVENTORY MANAGEMENT ═════════════════
def add_attendance(worker_name, status, date_str=None):
    """Add daily check-in record for worker (Present or Half Day)"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    key = f"{date_str}_{worker_name.upper()}"
    st.session_state.attendance[key] = {
        "worker": worker_name.upper(),
        "date": date_str,
        "status": status,  # "Present" or "Half Day"
        "timestamp": datetime.now().isoformat()
    }
    save_data()

def get_attendance_by_date(date_str):
    """Get all attendance records for a specific date"""
    return [v for k, v in st.session_state.attendance.items() if v["date"] == date_str]

def update_inventory(item_name, quantity_change):
    """Update inventory count (add or subtract)"""
    item_upper = item_name.upper()
    if item_upper not in st.session_state.inventory:
        st.session_state.inventory[item_upper] = 0
    st.session_state.inventory[item_upper] += quantity_change
    save_data()

# ═════════════════ REPORT MANAGER (MATERIAL) ═════════════════
def build_html_report(records, budget):
    material_total = total_materials()
    expense_total = total_expenses()
    excess_total = total_excess()
    remaining_balance = get_balance()
    date_now = datetime.now().strftime("%B %d, %Y")

    sobra_amount = 0.0
    kulang_amount = 0.0

    if remaining_balance > 0:
        sobra_amount = remaining_balance
    elif remaining_balance < 0:
        kulang_amount = abs(remaining_balance)

    if budget <= 0:
        balance_color = "#ffffff"
    else:
        balance_color = "#e57373" if remaining_balance < 0 else "#a5d6a7"

    html = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; background-color: #f0f4f0; margin: 0; padding: 20px; color: #333; }}
            .receipt-container {{ max-width: 1000px; margin: auto; background: #fff; padding: 30px; border-radius: 4px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-top: 10px solid #1b5e20; }}
            .header {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }}
            .company-info h1 {{ color: #1b5e20; margin: 0; font-size: 24px; letter-spacing: -1px; }}
            .company-info p {{ margin: 4px 0; font-size: 12px; color: #666; }}
            .receipt-meta {{ text-align: left; margin-top: 10px; }}
            @media (min-width: 768px) {{ .receipt-meta {{ text-align: right; margin-top: 0; }} }}
            .receipt-meta h2 {{ margin: 0; font-size: 16px; text-transform: uppercase; color: #1b5e20; }}
            .receipt-meta p {{ margin: 4px 0; font-size: 12px; font-weight: bold; }}

            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 12px; }}
            th {{ background-color: #1b5e20; color: #ffffff; text-align: left; padding: 10px; text-transform: uppercase; letter-spacing: 1px; }}
            td {{ padding: 10px 8px; border-bottom: 1px solid #f0f0f0; }}
            .qty-col, .desccol, .pricecol, .deliverycol, .totalcol {{ text-align: left; }}
            .desccol {{ font-weight: 700; color: #1b5e20; }}

            .summary-container {{ display: flex; justify-content: flex-end; }}
            .summary-table {{ width: 100%; }}
            @media (min-width: 768px) {{ .summary-table {{ width: 420px; }} }}
            .grand-total {{ background: #1b5e20; color: white; padding: 20px; border-radius: 4px; margin-top: 15px; }}

            .balance-info {{ font-size: 13px; line-height: 1.8; }}
            .balance-row {{ display: flex; justify-content: space-between; }}
            .material-row {{ font-size: 18px; font-weight: bold; }}
            .final-balance-row {{ display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.4); margin-top: 8px; padding-top: 8px; font-size: 18px; font-weight: bold; }}

            .footer {{ margin-top: 30px; text-align: center; font-size: 9px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="receipt-container">
            <div class="header">
                <div class="company-info">
                    <h1>AILYN HOUSE PROJECT</h1>
                    <p>Official Material & Expense Inventory</p>
                    <p>Management System {APP_VERSION}</p>
                    <p>Backup Receiver: <i>{RECEIVER_AILYN}</i></p>
                </div>
                <div class="receipt-meta">
                    <h2>Inventory Receipt</h2>
                    <p>Date: {date_now}</p>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th class="qty-col">Qty</th>
                        <th class="desccol">Description</th>
                        <th class="pricecol">Unit Price</th>
                        <th class="deliverycol">Delivery</th>
                        <th class="totalcol">Total</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in records:
        html += f"""
                    <tr>
                        <td>{r['date']}</td>
                        <td class="qty-col">{r['qty']}</td>
                        <td class="desccol">{r['name']}</td>
                        <td class="pricecol">{float(r.get('price', r['amount'])):,.2f}</td>
                        <td class="deliverycol">{float(r['delivery']):,.2f}</td>
                        <td class="totalcol">PHP {float(r['amount']):,.2f}</td>
                    </tr>
        """

    html += f"""
                </tbody>
            </table>

            <div class="summary-container">
                <div class="summary-table">
                    <div class="grand-total">
                        <div class="balance-info">
                            <div class="balance-row material-row">
                                <span>Material/Expense Total:</span>
                                <span>PHP {material_total + expense_total:,.2f}</span>
                            </div>
                            <div class="balance-row" style="font-size: 13px;">
                                <span>Excess Money Total:</span>
                                <span>PHP {excess_total:,.2f}</span>
                            </div>
                            <div class="balance-row" style="font-size: 13px;">
                                <span>Total Budget:</span>
                                <span>PHP {budget:,.2f}</span>
                            </div>
    """

    if sobra_amount > 0:
        html += f"""
                            <div class="final-balance-row">
                                <span>EXCESS</span>
                                <span style="color: #a5d6a7;">PHP {sobra_amount:,.2f}</span>
                            </div>
        """

    if kulang_amount > 0:
        html += f"""
                            <div class="final-balance-row">
                                <span>SHORTAGE</span>
                                <span style="color: #e57373;">PHP {kulang_amount:,.2f}</span>
                            </div>
        """

    html += f"""
                            <div class="final-balance-row">
                                <span>FINAL BALANCE</span>
                                <span style="color: {balance_color};">PHP {remaining_balance:,.2f}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                This document was electronically generated and is valid without signature.
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ═════════════════ REPORT MANAGER (PAYROLL) ═════════════════
def generate_payroll_html(labor_records, expense_records, remaining_money=0.0):
    date_str = datetime.now().strftime("%B %d, %Y | %I:%M %p")
    total_labor = sum(r['net'] for r in labor_records)
    total_expenses = sum(e['price'] for e in expense_records)
    
    sub_total = total_labor + total_expenses
    grand_total = sub_total - remaining_money

    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', sans-serif; background-color: #f4f7f6; padding: 40px;">
    <div style="max-width: 900px; margin: auto; background: white; border-top: 10px solid #1b5e20; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr>
                <td>
                    <h1 style="color: #1b5e20; margin: 0; text-transform: uppercase;">Ailyn Construction</h1>
                    <p style="color: #555; margin: 5px 0 0 0;">Official Labor & Payroll Inventory</p>
                    <p style="color: #777; font-size: 14px; margin: 0;">Management System v3.6 Enterprise</p>
                </td>
                <td style="text-align: right;">
                    <h3 style="color: #1b5e20; margin: 0;">INVENTORY RECEIPT</h3>
                    <p style="color: #555; font-size: 14px; margin: 5px 0 0 0;">Date: {date_str}</p>
                    <p style="color: #777; font-size: 12px; margin: 5px 0 0 0;">Account: {RECEIVER_EMAIL}</p>
                </td>
            </tr>
        </table>

        <div style="border-bottom: 2px solid #eee; margin-bottom: 30px;"></div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: #1b5e20; color: white; text-transform: uppercase; font-size: 14px;">
                    <th style="padding: 12px; text-align: left;">Worker Name</th>
                    <th style="padding: 12px; text-align: center;">Days</th>
                    <th style="padding: 12px; text-align: right;">Rate</th>
                    <th style="padding: 12px; text-align: right;">C.A.</th>
                    <th style="padding: 12px; text-align: right;">Net Pay</th>
                </tr>
            </thead>
            <tbody>
    """

    for r in labor_records:
        html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; font-weight: bold;">{r['name']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{r['days']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">{r['rate']:,.2f}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right; color: #d32f2f;">({r['ca']:,.2f})</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right; font-weight: bold; color: #1b5e20;">{r['net']:,.2f}</td>
                </tr>
        """

    if expense_records:
        html += """
                <tr>
                    <td colspan="5" style="padding: 12px 0;"></td>
                </tr>
                <tr style="background-color: #388e3c; color: white; text-transform: uppercase; font-size: 14px;">
                    <th colspan="4" style="padding: 10px; text-align: left;">Expense Description</th>
                    <th style="padding: 10px; text-align: right;">Amount</th>
                </tr>
        """
        for e in expense_records:
            html += f"""
                <tr>
                    <td colspan="4" style="padding: 10px; border-bottom: 1px solid #ddd;">{e['item']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-weight: bold;">{e['price']:,.2f}</td>
                </tr>
            """

    html += f"""
            </tbody>
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px;">
            <tr style="border-top: 2px solid #bbb;">
                <td style="padding: 12px; font-weight: bold; text-align: right; font-size: 15px;">Subtotal Expenses:</td>
                <td style="padding: 12px; width: 180px; text-align: right; font-weight: bold; font-size: 15px; color: #333;">PHP {sub_total:,.2f}</td>
            </tr>
    """

    if remaining_money > 0:
        html += f"""
            <tr style="border-bottom: 2px solid #bbb;">
                <td style="padding: 12px; font-weight: bold; text-align: right; color: #d32f2f; font-size: 15px;">Remaining/Leftover Money:</td>
                <td style="padding: 12px; width: 180px; text-align: right; font-weight: bold; color: #d32f2f; font-size: 15px;">-PHP {remaining_money:,.2f}</td>
            </tr>
        """

    html += f"""
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr>
                <td></td>
                <td style="width: 350px; background: #1b5e20; color: white; padding: 20px; border-radius: 8px; text-align: right;">
                    <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Final Output Amount</span><br>
                    <span style="font-size: 32px; font-weight: bold; margin-top: 5px; display: inline-block;">PHP {grand_total:,.2f}</span>
                </td>
            </tr>
        </table>

        <div style="text-align: center; margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="color: #999; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;">
                THIS DOCUMENT WAS ELECTRONICALLY GENERATED AND IS VALID WITHOUT SIGNATURE.
            </p>
        </div>

    </div>
    </body>
    </html>
    """
    return html, grand_total

# ═════════════════ CSS & 3D GREEN INTERFACE ═════════════════
st.markdown("""
<style>
:root {
    --surface: rgba(8, 18, 16, 0.82);
    --surface-strong: rgba(12, 24, 21, 0.95);
    --surface-light: rgba(255, 255, 255, 0.08);
    --border: rgba(142, 244, 138, 0.30);
    --accent: #9efb7c;
    --accent-strong: #4be157;
    --text-light: #e6ffe4;
    --text-muted: #c3ffd4;
    --shadow: rgba(0, 0, 0, 0.35);
}

body {
    color: var(--text-light) !important;
}

@media (max-width: 768px) {
    .block-container {
        padding: 18px !important;
    }
    h1, h2, h3 {
        font-size: 22px !important;
        text-align: center;
    }
    button {
        width: 100% !important;
        margin-bottom: 10px !important;
        font-size: 15px !important;
        padding: 16px !important;
    }
    input, select, textarea {
        font-size: 16px !important;
    }
    .stColumns {
        flex-direction: column !important;
    }
}

@media (min-width: 1920px) {
    .block-container {
        padding: 40px !important;
    }
    h1, h2, h3 {
        font-size: 3.3rem !important;
    }
    button {
        font-size: 20px !important;
        padding: 22px !important;
        min-height: 64px;
    }
    input, select {
        font-size: 20px !important;
        min-height: 56px;
    }
}

.stApp {
    background: radial-gradient(circle at top, rgba(10, 15, 20, 0.9), transparent 35%),
                linear-gradient(180deg, rgba(5, 10, 15, 0.95) 0%, rgba(8, 12, 18, 0.98) 50%, rgba(3, 6, 10, 1) 100%),
                url("https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1400&q=80") no-repeat center center fixed;
    background-size: cover;
    background-blend-mode: multiply;
    position: relative;
}

.stApp::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 40%, rgba(255, 255, 150, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 70% 60%, rgba(255, 200, 100, 0.2) 0%, transparent 40%),
                linear-gradient(to bottom, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.3) 50%, rgba(0, 0, 0, 0.8) 100%);
    pointer-events: none;
    z-index: -1;
}

.block-container {
    background: rgba(20, 40, 34, 0.85) !important;
    backdrop-filter: saturate(150%) blur(22px);
    border-radius: 28px;
    border: 1px solid rgba(158, 251, 124, 0.16);
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.30), inset 0 1px 1px rgba(255, 255, 255, 0.08);
    padding: 34px;
    transform-style: preserve-3d;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.block-container:hover {
    transform: translateY(-5px);
    box-shadow: 0 34px 78px rgba(0, 0, 0, 0.32), inset 0 1px 2px rgba(255, 255, 255, 0.08);
    border-color: rgba(158, 251, 124, 0.30);
}

section[data-testid="stSidebar"] {
    background: rgba(18, 30, 26, 0.92) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(158, 251, 124, 0.16);
    box-shadow: inset -2px 0 18px rgba(0, 0, 0, 0.24);
}

button {
    background: linear-gradient(145deg, rgba(28, 40, 36, 0.95), rgba(50, 66, 58, 0.95)) !important;
    color: #f8ffef !important;
    border-radius: 22px !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    border: 1px solid rgba(155, 245, 120, 0.28) !important;
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.20) !important;
    font-weight: 800;
    font-family: 'Segoe UI', sans-serif;
    min-height: 52px;
    letter-spacing: 0.4px;
}

button:hover {
    transform: scale(1.03) translateY(-1px);
    box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24) !important;
    background: linear-gradient(145deg, rgba(44, 66, 58, 0.98), rgba(95, 187, 104, 0.20)) !important;
    border-color: rgba(155, 245, 120, 0.55) !important;
}

button:active {
    transform: scale(0.98);
}

input, textarea, select {
    background: rgba(255, 255, 255, 0.10) !important;
    border: 1.5px solid rgba(158, 251, 124, 0.20) !important;
    color: var(--text-light) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(16px);
    font-size: 17px !important;
    font-family: 'Segoe UI', sans-serif;
    min-height: 50px;
    padding: 16px 18px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

input:focus, textarea:focus, select:focus {
    border-color: rgba(158, 251, 124, 0.68) !important;
    box-shadow: 0 0 26px rgba(79, 232, 119, 0.34) !important;
    background: rgba(255, 255, 255, 0.16) !important;
}

.stTextInput>div>div>input,
.stTextInput>div>div>textarea,
.stSelectbox>div>div>div>select {
    color: var(--text-light) !important;
}

h1, h2, h3 {
    color: #dbffe3 !important;
    text-shadow: 0 0 18px rgba(138, 238, 136, 0.30);
    letter-spacing: 1.1px;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 800;
}

.stMarkdown {
    color: var(--text-light) !important;
}

[data-testid="stMetric"] {
    background: rgba(18, 34, 28, 0.92) !important;
    border-radius: 24px;
    padding: 22px;
    border: 1px solid rgba(158, 251, 124, 0.22);
    margin-bottom: 20px;
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.28);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    border-color: #9efb7c;
    box-shadow: 0 24px 44px rgba(0, 0, 0, 0.28);
}

[data-testid="stMetric"] label {
    color: #d6ffd3 !important;
    font-weight: 700;
    font-family: 'Segoe UI', sans-serif;
    font-size: 15px;
    letter-spacing: 0.55px;
}

[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 900;
}

.stButton>button {
    box-shadow: 0 20px 36px rgba(0, 0, 0, 0.24) !important;
}

.intro {
    text-align: center;
    padding: 34px;
    color: #f6ffe8;
    background: linear-gradient(145deg, rgba(28, 52, 41, 0.88), rgba(8, 18, 14, 0.92));
    border-radius: 30px;
    border: 1px solid rgba(158, 251, 124, 0.18);
    margin-bottom: 26px;
    box-shadow: inset 0 0 32px rgba(158, 251, 124, 0.12);
}

.intro h1 {
    font-size: 3.2rem;
    font-weight: 900;
    color: #e6ffe5;
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    margin-bottom: 12px;
    text-shadow: 0 6px 24px rgba(139, 248, 158, 0.24);
}

.intro p {
    font-size: 17px;
    color: #dfffe0;
    opacity: 0.98;
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 0.8px;
}

.main-dashboard {
    font-family: 'Segoe UI', sans-serif;
    font-weight: 900;
    font-size: 2.05rem;
    letter-spacing: 1px;
    color: #befec5;
    text-transform: uppercase;
    text-shadow: 0 2px 16px rgba(139, 248, 158, 0.16);
}

.stDivider {
    border-color: rgba(158, 251, 124, 0.16) !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="intro">
    <h1>🏗️ AILYN HOUSE PROJECT & PAYROLL</h1>
    <p>Professional Construction Management System v30000</p>
</div>
""", unsafe_allow_html=True)

# 🎛 CONTROL HUB
with st.sidebar:
    st.markdown('<h2 class="main-dashboard">📊 MAIN DASHBOARD</h2>', unsafe_allow_html=True)
    
    # MODE SELECTION - OFFLINE / ONLINE
    st.markdown("### 🔌 MODE SELECTION")
    mode_option = st.radio("Select Mode", ["🌐 Online", "📴 Offline"], index=0 if st.session_state.mode == "online" else 1)
    new_mode = "online" if mode_option == "🌐 Online" else "offline"
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        save_data()
    st.info(f"**Current Mode:** {'🌐 Online' if st.session_state.mode == 'online' else '📴 Offline'}")
    if st.session_state.mode == "online":
        st.success("Online mode enabled. All features are available, including email and cloud-style operations.")
    else:
        st.warning("Offline mode enabled. Local data save and backup work without mobile data.")
    st.divider()
    
    budget_input = st.number_input("Set Project Budget (PHP)", min_value=0.0, key="budget_input_sidebar", step=1000.0)
    if st.button("💾 APPLY BUDGET", use_container_width=True):
        if budget_input > 0:
            st.session_state.budget = float(budget_input)
            save_data()
            st.success(f"✅ Budget Set: PHP {float(budget_input):,.2f}")
            st.rerun()
        else:
            st.warning("⚠️ Please enter a valid budget amount")
        
    st.caption(f"{datetime.now().strftime('%I:%M %p | %b %d')}")
    st.divider()
    
    if st.button("🗄️ CREATE BACKUP NOW", use_container_width=True):
        backup_path = archive_backup()
        if backup_path is not None:
            st.success(f"Backup created: {backup_path.name}")
        else:
            st.info("No existing data file to back up yet.")

    backups = get_backups()
    if backups:
        backup_names = [b.name for b in backups]
        selected_index = st.selectbox("Choose a backup to restore", backup_names, index=0)
        if st.button("♻️ RESTORE SELECTED BACKUP", use_container_width=True):
            backup_to_restore = backups[backup_names.index(selected_index)]
            if restore_backup(backup_to_restore):
                st.success(f"Restored from backup: {backup_to_restore.name}")
                st.experimental_rerun()
            else:
                st.error("Backup restore failed. The file may be missing.")
    else:
        st.info("No backups found yet. Create one to enable restore.")

    st.divider()
    if st.session_state.mode == "online":
        st.markdown("**Online-only features:** Email sending, remote-ready export, and full cloud sync support.")
    else:
        st.markdown("**Offline features:** Local ledger, inventory, attendance, receipt uploads, and backup. No mobile data required.")
    st.divider()

    st.subheader("🏠 Navigation")
    if st.button("🏠 Project Summary / Home", use_container_width=True):
        set_view("home")
        
    st.markdown("---")
    st.subheader("🧱 Construction Ledger")
    if st.button("➕ Add Material (NEW)", use_container_width=True):
        set_view("material")
    if st.button("📝 Add Construction Expense", use_container_width=True):
        set_view("expense")
    if st.button("💰 Add Excess Money", use_container_width=True):
        set_view("excess")
    if st.button("📋 View Project Ledger", use_container_width=True):
        set_view("ledger")
    if st.button("📤 Export Construction Report", use_container_width=True):
        set_view("export")
        
    st.markdown("---")
    st.subheader("📦 NEW FEATURES")
    if st.button("📸 Receipt Scanner", use_container_width=True):
        set_view("receipt_scanner")
    if st.button("🏭 Stockroom (Live Inventory)", use_container_width=True):
        set_view("stockroom")
    if st.button("✅ Daily Check-in (Attendance)", use_container_width=True):
        set_view("attendance")
        
    st.markdown("---")
    st.subheader("👷 Payroll System")
    if st.button("➕ Add Labor", use_container_width=True):
        set_view("add_labor")
    if st.button("📝 Add Payroll Expense", use_container_width=True):
        set_view("add_payroll_expense")
    if st.button("➖ Set Remaining/Leftover", use_container_width=True):
        set_view("payroll_remaining")
    if st.button("📋 View Labor Records", use_container_width=True):
        set_view("payroll_ledger")
    if st.button("📤 Export Payroll Report", use_container_width=True):
        set_view("payroll_export")
    
    st.divider()
    
    if st.button("💾 SAVE DATA", use_container_width=True):
        save_data()
        st.success("All data saved permanently!")
        
    if st.button("🔄 RESET SYSTEM", use_container_width=True):
        clear_all()
        set_view("home")

# 🖥 VIEWS
view = st.session_state.view

# 🏠 HOME
if view == "home":
    # PROJECT BUDGET SECTION
    st.markdown("---")
    budget_col1, budget_col2, budget_col3 = st.columns([1, 2, 1])
    with budget_col2:
        st.markdown(f"<h2 style='text-align: center; color: #4ade80; font-size: 2rem;'>💰 PROJECT BUDGET</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; color: #a3e635; font-size: 1.8rem;'>PHP {st.session_state.budget:,.2f}</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("📊 QUICK STATS")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("MATERIALS & EXPENSES", f"PHP {get_total():,.2f}")
    col2.metric("BALANCE REMAINING", f"PHP {get_balance():,.2f}")
    col3.metric("STATUS", "✅ Active" if st.session_state.budget > 0 else "⚠️ No Budget")
    
    st.markdown("---")
    
    st.subheader("📋 MATERIALS LEDGER PREVIEW")
    if not st.session_state.records:
        st.info("No materials yet.")
    else:
        materials = [r for r in st.session_state.records if r["type"] == "material"]
        for r in materials[-5:]:
            st.markdown(f"""
            ---
            🧱 **{r['name']}** 💰 PHP {float(r['amount']):,.2f}  
            👤 {r['sender']}  
            📅 {r['date']}
            """)

# ➕ MATERIAL
elif view == "material":
    st.subheader("➕ MATERIAL (LOOP MODE) - WITH RECEIPT SCANNER")

    with st.form(key="material_form", clear_on_submit=True):
        name = st.text_input("Material Name")
        price = st.number_input("Price (PHP)", min_value=0.01, step=100.0)
        qty = st.number_input("Quantity", min_value=1, step=1)
        delivery = st.number_input("Delivery Cost (PHP)", min_value=0.0, step=50.0)
        sender = st.selectbox("Supplier/Sender", ["Garr", "Aily"])
        
        # NEW: Receipt upload
        st.markdown("**📸 Receipt Scanner (Optional)**")
        receipt_file = st.file_uploader("Upload Receipt Photo", type=["jpg", "jpeg", "png", "pdf"], key="receipt_upload")
        receipt_notes = st.text_input("Receipt Notes (optional)", "")
        
        submitted = st.form_submit_button(label="SAVE MATERIAL")

    if submitted:
        receipt_data = None
        if receipt_file is not None:
            receipt_data = {
                "filename": receipt_file.name,
                "uploaded_at": datetime.now().isoformat(),
                "notes": receipt_notes,
                "file_type": receipt_file.type
            }
        
        ok = add_tx(name, price, qty, delivery, "material", sender, receipt_data)
        if ok:
            st.success("✅ Saved! Ready for next order.")
            if receipt_data:
                st.info(f"📸 Receipt uploaded: {receipt_file.name}")
            st.rerun()
        else:
            st.warning("Invalid data, please check amounts.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 📝 EXPENSE
elif view == "expense":
    st.subheader("📝 EXPENSE (LOOP MODE)")

    with st.form(key="expense_form", clear_on_submit=True):
        name = st.text_input("Expense Description")
        amount = st.number_input("Amount (PHP)", min_value=0.01, step=100.0)
        sender = st.selectbox("Recorded By", ["Garr", "Aily"])
        
        submitted = st.form_submit_button(label="SAVE EXPENSE")

    if submitted:
        if amount > 0:
            add_tx(name, amount, 1, 0, "expense", sender)
            st.success("Expense Added → Ledger Updated")
            st.rerun()
        else:
            st.warning("Amount must be greater than zero.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 💰 EXCESS
elif view == "excess":
    st.subheader("💰 EXCESS (LOOP MODE)")

    with st.form(key="excess_form", clear_on_submit=True):
        name = st.text_input("Reason for Excess")
        amount = st.number_input("Amount (PHP)", min_value=0.01, step=100.0)
        sender = st.selectbox("Reported By", ["Garr", "Aily"])
        
        submitted = st.form_submit_button(label="ADD EXCESS")

    if submitted:
        if amount > 0:
            st.session_state.records.append({
                "id": str(time.time()),
                "date": datetime.now().strftime("%b %d, %Y"),
                "name": name.upper(),
                "price": float(amount),
                "qty": 1,
                "delivery": 0.0,
                "amount": float(amount),
                "type": "excess",
                "sender": sender,
                "receipt": None
            })
            save_data()
            st.success("Excess Added")
            st.rerun()
        else:
            st.warning("Please enter a valid amount.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 📋 LEDGER
elif view == "ledger":
    st.subheader("📋 CONSTRUCTION LEDGER (MOBILE VIEW)")

    if not st.session_state.records:
        st.info("No transaction records found in ledger.")
    else:
        for r in list(st.session_state.records):
            st.markdown(f"""
            ---
            **{r['name']}** 💰 PHP {float(r['amount']):,.2f}  
            👤 {r['sender']}  
            📦 {r['type']}  
            📅 {r['date']}
            """)

            if st.button("❌ DELETE", key=f"del_{r['id']}", use_container_width=True):
                st.session_state.records = [
                    x for x in st.session_state.records if x["id"] != r["id"]
                ]
                save_data()
                st.rerun()

# 📤 EXPORT
elif view == "export":
    st.subheader("📤 EXPORT CONSTRUCTION REPORT")

    html = build_html_report(st.session_state.records, st.session_state.budget)

    st.download_button(
        label="DOWNLOAD CONSTRUCTION REPORT",
        data=html,
        file_name="aily_mobile_report.html",
        mime="text/html",
        use_container_width=True
    )

    st.markdown("📧 **Receivers Enabled:**")
    st.write("Garry ✔")
    st.write("Aily ✔")
    st.write(f"{RECEIVER_AILYN} ✔")

# 👷 Payroll Views
elif view == "add_labor":
    st.subheader("👷 ADD LABOR")
    with st.form(key="labor_form", clear_on_submit=True):
        name = st.text_input("Worker Name")
        days = st.number_input("Days Worked (1 or 0.5 for half-day)", min_value=0.5, step=0.5)
        rate_option = st.radio("Daily Rate (PHP)", ["800", "650", "500"])
        rate = 800 if rate_option == "800" else 650 if rate_option == "650" else 500
        ca = st.number_input("Cash Advance (PHP)", min_value=0.0, step=100.0)
        
        submitted = st.form_submit_button("SAVE LABOR")
        
    if submitted:
        net = (days * rate) - ca
        st.session_state.labor_records.append({
            "name": name.upper(),
            "days": days,
            "rate": rate,
            "ca": ca,
            "net": net
        })
        save_data()
        st.success(f"Record for {name.upper()} added.")
        st.rerun()

elif view == "add_payroll_expense":
    st.subheader("📝 ADD PAYROLL EXPENSE")
    with st.form(key="payroll_expense_form", clear_on_submit=True):
        desc = st.text_input("Expense Description")
        amt = st.number_input("Amount (PHP)", min_value=0.01, step=100.0)
        
        submitted = st.form_submit_button("SAVE EXPENSE")
        
    if submitted:
        st.session_state.payroll_expenses.append({
            "item": desc.upper(),
            "price": amt
        })
        save_data()
        st.success(f"Expense {desc.upper()} added.")
        st.rerun()

elif view == "payroll_remaining":
    st.subheader("➖ SET REMAINING MONEY")
    res = st.number_input("Leftover/Remaining Money (PHP)", min_value=0.0, step=100.0, value=st.session_state.remaining_money)
    if st.button("📊 Apply Remaining Amount", use_container_width=True):
        st.session_state.remaining_money = res
        save_data()
        st.success("Remaining money applied.")
        st.rerun()

elif view == "payroll_ledger":
    st.subheader("📋 LABOR & PAYROLL LEDGER")
    st.markdown("### Labor Records")
    if not st.session_state.labor_records:
        st.info("No labor records.")
    for i, r in enumerate(st.session_state.labor_records):
        st.markdown(f"""
        ---
        **{r['name']}** - Days: {r['days']} | Rate: {r['rate']}  
        - C.A.: PHP {r['ca']:,.2f}  
        - **Net Pay: PHP {r['net']:,.2f}**
        """)
        if st.button("Delete Labor", key=f"del_lab_{i}"):
            st.session_state.labor_records.pop(i)
            save_data()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### Payroll Expenses")
    if not st.session_state.payroll_expenses:
        st.info("No payroll expenses.")
    for i, e in enumerate(st.session_state.payroll_expenses):
        st.markdown(f"""
        - **{e['item']}**: PHP {e['price']:,.2f}
        """)
        if st.button("Delete Payroll Expense", key=f"del_pay_exp_{i}"):
            st.session_state.payroll_expenses.pop(i)
            save_data()
            st.rerun()

elif view == "payroll_export":
    st.subheader("📤 GENERATE PAYROLL REPORT")
    
    html, total = generate_payroll_html(
        st.session_state.labor_records, 
        st.session_state.payroll_expenses, 
        st.session_state.remaining_money
    )
    
    st.download_button(
        label="DOWNLOAD PAYROLL REPORT",
        data=html,
        file_name="payroll_report.html",
        mime="text/html",
        use_container_width=True
    )
    
    if st.session_state.mode == "offline":
        st.info("Email sending is unavailable in offline mode. Switch to Online mode to send reports.")
    else:
        if st.button("📧 Email Report"):
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Construction Report: PHP {total:,.2f} - {datetime.now().strftime('%Y-%m-%d')}"
                msg['From'] = SENDER_EMAIL
                msg['To'] = RECEIVER_EMAIL
                msg.add_alternative(html, subtype='html')
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                    smtp.send_message(msg)
                st.success("🚀 SUCCESS! Emailed report.")
            except Exception as e:
                st.error(f"❌ EMAIL FAILED: {e}")

# 📸 RECEIPT SCANNER
elif view == "receipt_scanner":
    st.subheader("📸 RECEIPT SCANNER & VOUCHER SYSTEM")
    st.markdown("Upload and organize receipt photos for materials purchased.")
    
    st.markdown("### 📤 Upload Receipt")
    receipt_file = st.file_uploader("Choose receipt image", type=["jpg", "jpeg", "png", "pdf"])
    
    if receipt_file is not None:
        receipt_id = str(time.time())
        material_name = st.text_input("Material Name (from receipt)")
        receipt_amount = st.number_input("Amount on Receipt (PHP)", min_value=0.01, step=100.0)
        receipt_date = st.date_input("Receipt Date")
        
        if st.button("📸 SAVE RECEIPT", use_container_width=True):
            st.session_state.receipts[receipt_id] = {
                "id": receipt_id,
                "filename": receipt_file.name,
                "material": material_name.upper(),
                "amount": float(receipt_amount),
                "date": receipt_date.isoformat(),
                "uploaded_at": datetime.now().isoformat(),
                "file_type": receipt_file.type
            }
            save_data()
            st.success(f"✅ Receipt saved! ID: {receipt_id}")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Receipt History")
    if not st.session_state.receipts:
        st.info("No receipts uploaded yet.")
    else:
        for rid, receipt in st.session_state.receipts.items():
            st.markdown(f"""
            ---
            **Material:** {receipt['material']}  
            **Amount:** PHP {receipt['amount']:,.2f}  
            **Date:** {receipt['date']}  
            **File:** {receipt['filename']}  
            **Uploaded:** {receipt['uploaded_at']}
            """)
            if st.button("🗑️ Delete", key=f"del_receipt_{rid}"):
                del st.session_state.receipts[rid]
                save_data()
                st.rerun()

# 🏭 STOCKROOM (LIVE INVENTORY)
elif view == "stockroom":
    st.subheader("🏭 STOCKROOM - LIVE INVENTORY")
    st.markdown("Track exactly how many bags, pieces, or units you have left.")
    
    st.markdown("### 📊 Current Inventory")
    if not st.session_state.inventory:
        st.info("No items in inventory yet. Add materials to start tracking.")
    else:
        # Display inventory in a nice table format
        cols = st.columns([2, 1, 1])
        cols[0].markdown("**Item Name**")
        cols[1].markdown("**Count**")
        cols[2].markdown("**Action**")
        st.divider()
        
        for item_name, count in sorted(st.session_state.inventory.items()):
            cols = st.columns([2, 1, 1])
            cols[0].markdown(f"📦 {item_name}")
            cols[1].metric("Qty", count, delta=None, label_visibility="collapsed")
            if cols[2].button("Edit", key=f"edit_inv_{item_name}"):
                st.session_state.edit_item = item_name
                st.rerun()
    
    st.markdown("---")
    st.markdown("### ➕ Manually Adjust Inventory")
    
    if st.session_state.inventory:
        col1, col2 = st.columns(2)
        
        with col1:
            item_to_adjust = st.selectbox("Select Item", list(st.session_state.inventory.keys()), key="inv_select")
        
        with col2:
            adjustment = st.number_input("Quantity Change (+/-)", min_value=0, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add to Stock", use_container_width=True):
                if adjustment > 0:
                    update_inventory(item_to_adjust, adjustment)
                    st.success(f"✅ Added {adjustment} to {item_to_adjust}")
                    st.rerun()
        
        with col2:
            if st.button("➖ Remove from Stock", use_container_width=True):
                if adjustment > 0:
                    update_inventory(item_to_adjust, -adjustment)
                    st.success(f"✅ Removed {adjustment} from {item_to_adjust}")
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### ➕ Add New Item")
    col1, col2 = st.columns(2)
    with col1:
        new_item = st.text_input("Item Name")
    with col2:
        initial_qty = st.number_input("Initial Quantity", min_value=0, step=1)
    
    if st.button("CREATE NEW ITEM", use_container_width=True):
        if new_item:
            st.session_state.inventory[new_item.upper()] = initial_qty
            save_data()
            st.success(f"✅ Created {new_item.upper()}")
            st.rerun()

# ✅ DAILY CHECK-IN (ATTENDANCE)
elif view == "attendance":
    st.subheader("✅ DAILY CHECK-IN - ATTENDANCE LOG")
    st.markdown("Professional attendance tracking for workers. Click 'Present' or 'Half Day' for each worker.")
    
    st.markdown("---")
    st.markdown(f"### 📅 Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = get_attendance_by_date(today)
    
    # Get unique worker names from labor records
    workers_in_system = set([r["name"] for r in st.session_state.labor_records]) if st.session_state.labor_records else set()
    
    # Add manual worker input
    st.markdown("### ➕ Add Worker for Today")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        worker_name = st.text_input("Worker Name", key="worker_input")
    
    with col2:
        status = st.selectbox("Status", ["Present", "Half Day"], key="status_select")
    
    with col3:
        if st.button("✅ CHECK IN", use_container_width=True):
            if worker_name:
                add_attendance(worker_name, status, today)
                st.success(f"✅ {worker_name.upper()} marked as {status}")
                st.rerun()
    
    st.markdown("---")
    st.markdown(f"### 👥 Today's Check-in Log ({len(today_attendance)} workers)")
    
    if not today_attendance:
        st.info("No check-ins recorded for today yet.")
    else:
        # Display attendance in a nice format
        for att in sorted(today_attendance, key=lambda x: x["timestamp"]):
            status_emoji = "✅" if att["status"] == "Present" else "⏰"
            st.markdown(f"""
            {status_emoji} **{att['worker']}** — {att['status']}  
            ⏱️ {att['timestamp'][:19]}
            """)
    
    st.markdown("---")
    st.markdown("### 📋 Attendance History")
    
    # Show attendance from all dates
    all_dates = sorted(set([v["date"] for v in st.session_state.attendance.values()]))
    
    if all_dates:
        selected_date = st.selectbox("Select Date", all_dates, index=len(all_dates)-1 if len(all_dates) > 0 else 0)
        date_attendance = get_attendance_by_date(selected_date)
        
        st.markdown(f"**{len(date_attendance)} workers for {selected_date}**")
        for att in sorted(date_attendance, key=lambda x: x["timestamp"]):
            status_emoji = "✅" if att["status"] == "Present" else "⏰"
            st.markdown(f"{status_emoji} {att['worker']} — {att['status']}")
    else:
        st.info("No attendance records yet.")
    
    # Export attendance as CSV-style
    st.markdown("---")
    if st.button("📄 Export Attendance Report", use_container_width=True):
        csv_data = "Date,Worker,Status,Timestamp\n"
        for att in sorted(st.session_state.attendance.values(), key=lambda x: x["timestamp"]):
            csv_data += f"{att['date']},{att['worker']},{att['status']},{att['timestamp']}\n"
        
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="attendance_report.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("Welcome to AILY OS. Use the sidebar to navigate.")