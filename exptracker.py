import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
import json
import random
import io
import re
import builtins
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

GenerativeModel = None
GEMINI_AVAILABLE = False
GEMINI_SDK_TYPE = None

try:
    from google import genai as google_genai
    GEMINI_AVAILABLE = True
    GEMINI_SDK_TYPE = "new"
except (ImportError, AttributeError, Exception):
    try:
        import google.generativeai as genai
        GenerativeModel = getattr(genai, "GenerativeModel", None)
        GEMINI_AVAILABLE = True
        GEMINI_SDK_TYPE = "legacy"
    except (ImportError, AttributeError, Exception):
        GEMINI_AVAILABLE = False
        GEMINI_SDK_TYPE = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except builtins.ImportError:
    OPENAI_AVAILABLE = False

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #f0f9ff;
    color: #0f172a;
}
.stApp { background: #f0f9ff; }

[data-testid="stSidebar"] {
    background: #e0f2fe !important;
    border-right: 1px solid #bae6fd;
}
[data-testid="stSidebar"] * { color: #0f172a !important; }

.metric-card {
    background: #ffffff;
    border: 1px solid #bae6fd;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 14px;
    transition: border-color .2s;
    box-shadow: 0 2px 10px rgba(186, 230, 253, 0.4);
}
.metric-card:hover { border-color: #22c55e; }
.metric-label { font-size: 13px; color: #64748b; font-weight: 500; letter-spacing: .05em; text-transform: uppercase; }
.metric-value { font-size: 36px; font-weight: 800; margin: 4px 0 2px; color: #0f172a; }
.metric-sub   { font-size: 13px; color: #475569; }

.green  { color: #16a34a; }
.red    { color: #dc2626; }
.blue   { color: #2563eb; }
.amber  { color: #d97706; }
.purple { color: #9333ea; }
.teal   { color: #0d9488; }

.section-title {
    font-size: 20px; font-weight: 700;
    border-left: 4px solid #22c55e;
    padding-left: 12px; margin: 28px 0 16px;
    color: #0f172a;
}

.stProgress > div > div > div { background: linear-gradient(90deg, #22c55e, #4ade80) !important; }

.stButton > button {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 10px 22px;
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    transition: all .2s;
    box-shadow: 0 2px 4px rgba(186, 230, 253, 0.4);
}
.stButton > button:hover { background: #f0fdf4; border-color: #22c55e; color: #15803d; }

.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #bae6fd !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
}

.ai-bubble {
    background: linear-gradient(135deg, #dcfce7, #bbf7d0);
    border: 1px solid #86efac;
    border-radius: 18px;
    padding: 18px 22px;
    margin: 8px 0;
    position: relative;
    color: #064e3b;
}
.ai-bubble::before {
    content:'🤖 AI Advisor';
    display:block;
    font-size:11px;
    color:#166534;
    font-weight:700;
    letter-spacing:.1em;
    margin-bottom:8px;
    text-transform:uppercase;
}
.user-bubble {
    background: #e0f2fe;
    border: 1px solid #bae6fd;
    border-radius: 18px;
    padding: 14px 18px;
    margin: 6px 0;
    text-align:right;
    color: #0c4a6e;
}

/* ── Split Bill Cards ── */
.split-card {
    background: #ffffff;
    border: 1px solid #bae6fd;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(186,230,253,0.3);
}
.split-card-title {
    font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 6px;
}
.split-owe {
    background: #fef2f2; border: 1px solid #fecaca;
    border-radius: 10px; padding: 8px 14px; margin: 4px 0;
    font-size: 13px; color: #991b1b; font-weight: 600;
}
.split-get {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; padding: 8px 14px; margin: 4px 0;
    font-size: 13px; color: #166534; font-weight: 600;
}
.split-settled {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 8px 14px; margin: 4px 0;
    font-size: 13px; color: #64748b; font-weight: 600;
}

.badge {
    display:inline-block;
    padding: 4px 14px;
    border-radius: 99px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px;
}
.badge-gold   { background:#fef3c7; color:#b45309; border:1px solid #fde68a; }
.badge-green  { background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }

.notif-warn {
    background: linear-gradient(90deg,#fffbeb,#fef3c7);
    border-left: 4px solid #f59e0b;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px; margin: 10px 0;
    font-size: 14px; color: #92400e;
}
.notif-danger {
    background: linear-gradient(90deg,#fef2f2,#fee2e2);
    border-left: 4px solid #ef4444;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px; margin: 10px 0;
    font-size: 14px; color: #991b1b;
}
.notif-success {
    background: linear-gradient(90deg,#f0fdf4,#dcfce7);
    border-left: 4px solid #22c55e;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px; margin: 10px 0;
    font-size: 14px; color: #166534;
}

::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#e0f2fe; }
::-webkit-scrollbar-thumb { background:#7dd3fc; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#22c55e; }

.stTabs [data-baseweb="tab-list"] { background:#e0f2fe; border-radius:12px; padding:4px; }
.stTabs [data-baseweb="tab"] { color:#64748b; border-radius:10px; }
.stTabs [aria-selected="true"] { background:#ffffff !important; color:#22c55e !important; box-shadow: 0 2px 4px rgba(186,230,253,0.4); }
</style>
""", unsafe_allow_html=True)

# ── DATABASE SETUP ────────────────────────────────────────────
DB_PATH = "smart_expense_tracker.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, amount REAL NOT NULL,
        category TEXT NOT NULL, description TEXT,
        mood TEXT DEFAULT 'Neutral', payment TEXT DEFAULT 'Cash',
        receipt_img TEXT, created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE NOT NULL, amount REAL NOT NULL, month TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS savings_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_name TEXT NOT NULL, target REAL NOT NULL,
        saved REAL DEFAULT 0, deadline TEXT, created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        badge_name TEXT NOT NULL, description TEXT, earned_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL, amount REAL NOT NULL)""")

    # ── Split Bill Tables ──────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS split_groups (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name  TEXT NOT NULL,
        members     TEXT NOT NULL,          -- JSON list of member names
        created_at  TEXT DEFAULT (datetime('now')))""")

    c.execute("""CREATE TABLE IF NOT EXISTS split_expenses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id    INTEGER NOT NULL,
        description TEXT NOT NULL,
        total_amount REAL NOT NULL,
        paid_by     TEXT NOT NULL,          -- member name who paid
        split_type  TEXT DEFAULT 'equal',   -- equal | custom | percentage
        split_data  TEXT,                   -- JSON: {member: share_amount}
        date        TEXT DEFAULT (date('now')),
        settled     INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(group_id) REFERENCES split_groups(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS split_settlements (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id    INTEGER NOT NULL,
        paid_by     TEXT NOT NULL,
        paid_to     TEXT NOT NULL,
        amount      REAL NOT NULL,
        settled_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(group_id) REFERENCES split_groups(id))""")

    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM expenses")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    today = date.today()
    categories = ["Food","Health","Bills","Travel","Entertainment","Learning","Assets"]
    moods = ["Happy","Stressed","Neutral","Sad","Excited"]
    payments = ["UPI","Cash","Card","Net Banking"]
    sample = [(str(today - timedelta(days=i)), round(random.uniform(50, 2000), 2),
               random.choice(categories), "Sample expense",
               random.choice(moods), random.choice(payments)) for i in range(60)]
    c.executemany("INSERT INTO expenses(date,amount,category,description,mood,payment) VALUES(?,?,?,?,?,?)", sample)
    month_str = today.strftime("%Y-%m")
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO budgets(category,amount,month) VALUES(?,?,?)",
                  (cat, random.choice([3000,4000,5000,6000,8000,10000]), month_str))
    c.execute("INSERT OR IGNORE INTO income(month,amount) VALUES(?,?)", (month_str, 50000))
    c.execute("INSERT OR IGNORE INTO savings_goals(goal_name,target,saved,deadline) VALUES(?,?,?,?)",
              ("Emergency Fund", 100000, 35000, str(today + timedelta(days=180))))

    # Demo split group
    members = json.dumps(["Alice", "Bob", "Charlie"])
    c.execute("INSERT INTO split_groups(group_name,members) VALUES(?,?)", ("Trip to Goa 🏖️", members))
    gid = c.lastrowid
    split_items = [
        ("Hotel booking", 9000, "Alice", json.dumps({"Alice": 3000, "Bob": 3000, "Charlie": 3000})),
        ("Dinner at Thalassa", 2400, "Bob",  json.dumps({"Alice": 800,  "Bob": 800,  "Charlie": 800})),
        ("Cab from airport",   1500, "Charlie", json.dumps({"Alice": 500,  "Bob": 500,  "Charlie": 500})),
    ]
    for desc, amt, paid, data in split_items:
        c.execute("INSERT INTO split_expenses(group_id,description,total_amount,paid_by,split_data,date) VALUES(?,?,?,?,?,?)",
                  (gid, desc, amt, paid, data, str(today - timedelta(days=random.randint(1,10)))))

    conn.commit()
    conn.close()

init_db()
seed_demo_data()

# ── CONSTANTS ─────────────────────────────────────────────────
CATEGORIES = ["Food","Health","Bills","Travel","Entertainment","Learning","Assets","Other"]
MOODS      = ["Happy 😊","Excited 🤩","Neutral 😐","Stressed 😤","Sad 😢","Anxious 😰","Bored 😑"]
PAYMENTS   = ["UPI","Cash","Card","Net Banking","Wallet"]
CAT_COLORS = {"Food":"#f87171","Health":"#34d399","Bills":"#fdc844","Travel":"#60a5fa",
              "Entertainment":"#a78bfa","Learning":"#2dd4bf","Assets":"#fb923c","Other":"#94a3b8"}
MOOD_COLORS= {"Happy":"#4ade80","Excited":"#f59e0b","Neutral":"#66a4fc",
              "Stressed":"#f87171","Sad":"#60a5fa","Anxious":"#c084fc","Bored":"#6b7280"}

def plotly_theme():
    return dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0f172a", family="Outfit"))

# ── HELPERS ───────────────────────────────────────────────────
def load_expenses(days=None):
    conn = get_conn()
    if days:
        since = str(date.today() - timedelta(days=days))
        df = pd.read_sql("SELECT * FROM expenses WHERE date >= ? ORDER BY date DESC", conn, params=(since,))
    else:
        df = pd.read_sql("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['mood_clean'] = df['mood'].apply(lambda x: x.split()[0] if isinstance(x, str) and x.strip() else "Neutral")
    return df

def load_budgets(month=None):
    conn = get_conn()
    month = month or date.today().strftime("%Y-%m")
    df = pd.read_sql("SELECT * FROM budgets WHERE month=?", conn, params=(month,))
    conn.close()
    return df

def current_month_spend():
    conn = get_conn()
    month = date.today().strftime("%Y-%m")
    df = pd.read_sql("SELECT category, SUM(amount) as spent FROM expenses WHERE strftime('%Y-%m',date)=? GROUP BY category",
                     conn, params=(month,))
    conn.close()
    return df

def get_income(month=None):
    conn = get_conn()
    month = month or date.today().strftime("%Y-%m")
    row = conn.execute("SELECT amount FROM income WHERE month=?", (month,)).fetchone()
    conn.close()
    return row[0] if row else 0

def add_expense(date_val, amount, category, description, mood, payment, receipt_b64=None):
    conn = get_conn()
    conn.execute("INSERT INTO expenses(date,amount,category,description,mood,payment,receipt_img) VALUES(?,?,?,?,?,?,?)",
                 (str(date_val), amount, category, description, mood, payment, receipt_b64))
    conn.commit()
    conn.close()
    check_and_award_badges()

def check_budget_alerts():
    alerts = []
    month = date.today().strftime("%Y-%m")
    budgets = load_budgets(month)
    spend = current_month_spend()
    if budgets.empty:
        return alerts
    if spend.empty:
        merged = budgets.copy()
        merged['spent'] = 0.0
    else:
        merged = budgets.merge(spend, on="category", how="left")
        merged['spent'] = merged['spent'].fillna(0.0)

    for _, row in merged.iterrows():
        pct = (row['spent'] / row['amount']) * 100 if row['amount'] > 0 else 0
        if pct >= 100:
            alerts.append(("danger", f"🚨 {row['category']} budget EXCEEDED! ₹{row['spent']:,.0f} / ₹{row['amount']:,.0f}"))
        elif pct >= 80:
            alerts.append(("warn", f"⚠️ {row['category']} at {pct:.0f}% (₹{row['spent']:,.0f} / ₹{row['amount']:,.0f})"))
    return alerts

def check_and_award_badges():
    conn = get_conn()
    df = load_expenses(30)
    if df.empty:
        conn.close()
        return
    total = df['amount'].sum()
    existing = [r[0] for r in conn.execute("SELECT badge_name FROM rewards").fetchall()]
    badges = []
    if total < 10000 and "Saver of the Month 🥇" not in existing:
        badges.append(("Saver of the Month 🥇", "Spent under ₹10,000 in 30 days"))
    if len(df) >= 30 and "Consistent Tracker 📊" not in existing:
        badges.append(("Consistent Tracker 📊", "Logged 30+ expenses"))
    if "Learning" in df['category'].values and "Knowledge Investor 📚" not in existing:
        badges.append(("Knowledge Investor 📚", "Invested in learning"))
    if "Assets" in df['category'].values and "Asset Builder 🏗️" not in existing:
        badges.append(("Asset Builder 🏗️", "Added an asset expense"))
    for name, desc in badges:
        conn.execute("INSERT INTO rewards(badge_name,description) VALUES(?,?)", (name, desc))
    conn.commit()
    conn.close()

def generate_pdf_report(df, month_label):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=.6*inch, rightMargin=.6*inch,
                            topMargin=.6*inch, bottomMargin=.6*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T2', parent=styles['Title'], fontSize=22,
                                 textColor=rl_colors.HexColor("#16a34a"), spaceAfter=6, alignment=TA_CENTER)
    sub_style   = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                                 textColor=rl_colors.HexColor("#0284c7"), spaceAfter=16, alignment=TA_CENTER)
    elems = [Paragraph("Smart Expense Tracker", title_style),
             Paragraph(f"Monthly Report — {month_label}", sub_style),
             HRFlowable(width="100%", thickness=1, color=rl_colors.HexColor('#bae6fd')),
             Spacer(1, 12)]
    if not df.empty:
        cat_sum = df.groupby('category')['amount'].sum().reset_index()
        cat_sum.columns = ['Category','Total (Rs.)']
        cat_sum['Total (Rs.)'] = cat_sum['Total (Rs.)'].apply(lambda x: f"Rs. {x:,.2f}")
        td = [['Category','Total Spent']] + cat_sum.values.tolist()
        t = Table(td, colWidths=[3*inch,3*inch])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor('#e0f2fe')),
                                ('TEXTCOLOR',(0,0),(-1,0),rl_colors.HexColor('#0f172a')),
                                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                                ('ROWBACKGROUNDS',(0,1),(-1,-1),[rl_colors.HexColor('#ffffff'),rl_colors.HexColor('#f8fafc')]),
                                ('TEXTCOLOR',(0,1),(-1,-1),rl_colors.HexColor('#334155')),
                                ('GRID',(0,0),(-1,-1),.4,rl_colors.HexColor('#bae6fd')),
                                ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        total_spent = df['amount'].sum()
        income = get_income()
        s2 = Table([['Total Income',f"Rs. {income:,.2f}"],['Total Spent',f"Rs. {total_spent:,.2f}"],
                    ['Net Savings',f"Rs. {income-total_spent:,.2f}"]], colWidths=[3*inch,3*inch])
        s2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),rl_colors.HexColor('#f0fdf4')),
                                 ('TEXTCOLOR',(0,0),(0,-1),rl_colors.HexColor('#475569')),
                                 ('TEXTCOLOR',(1,0),(1,-1),rl_colors.HexColor('#16a34a')),
                                 ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
                                 ('GRID',(0,0),(-1,-1),.4,rl_colors.HexColor('#bbf7d0')),
                                 ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        elems += [Paragraph("Spending by Category",styles['Heading2']),Spacer(1,8),t,Spacer(1,18),
                   Paragraph("Summary",styles['Heading2']),Spacer(1,8),s2]
    doc.build(elems)
    buf.seek(0)
    return buf.read()

def get_ai_response(user_msg, df):
    context = ""
    if not df.empty:
        top_cat   = df.groupby('category')['amount'].sum().idxmax()
        total     = df['amount'].sum()
        avg_daily = total / max(1, df['date'].nunique())
        context = f"User spent ₹{total:,.0f} this month. Top category: {top_cat}. Avg daily: ₹{avg_daily:,.0f}. "
    system = ("You are an empathetic AI Financial Advisor for Smart Expense Tracker, an Indian personal finance app. "
              "Help users save money and achieve savings goals. Be concise (3-5 sentences), warm, practical. Use ₹. " + context)
    gk = st.session_state.get("gemini_key","")
    if GEMINI_AVAILABLE and gk:
        try:
            if GEMINI_SDK_TYPE == "new":
                client = google_genai.Client(api_key=gk)
                resp = client.models.generate_content(model="gemini-2.0-flash", contents=f"{system}\n\nUser: {user_msg}")
                return resp.text
            else:
                genai.configure(api_key=gk)
                model = GenerativeModel("gemini-2.0-flash")
                return model.generate_content(f"{system}\n\nUser: {user_msg}").text
        except Exception:
            try:
                if GEMINI_SDK_TYPE == "legacy":
                    genai.configure(api_key=gk)
                    model = GenerativeModel("gemini-1.5-flash")
                    return model.generate_content(f"{system}\n\nUser: {user_msg}").text
            except Exception: pass
    ok = st.session_state.get("openai_key","")
    if OPENAI_AVAILABLE and ok:
        try:
            client = OpenAI(api_key=ok)
            resp = client.chat.completions.create(model="gpt-4o-mini",
                messages=[{"role":"system","content":system},{"role":"user","content":user_msg}], max_tokens=300)
            return resp.choices[0].message.content
        except Exception: pass
    msg = user_msg.lower()
    if any(w in msg for w in ["save","saving","goal"]):
        return "Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings. Automate a transfer on payday!"
    elif any(w in msg for w in ["food","eat","restaurant"]):
        return "Meal prepping 3 days a week can cut food costs by 30-40%. Set a weekly food budget!"
    elif any(w in msg for w in ["split","group","friend"]):
        return "Great use of the split feature! Settling bills promptly avoids awkward follow-ups. Track group trips to spot shared spending patterns."
    else:
        return "Focus on your top 2 spending categories and set firm weekly limits. Small consistent cuts add up!"

# ── SPLIT BILL HELPERS ────────────────────────────────────────
def get_all_groups():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM split_groups ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_group_expenses(group_id):
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM split_expenses WHERE group_id=? ORDER BY date DESC", conn, params=(group_id,))
    conn.close()
    if not df.empty:
        df['split_data'] = df['split_data'].apply(lambda x: json.loads(x) if x else {})
    return df

def get_group_settlements(group_id):
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM split_settlements WHERE group_id=? ORDER BY settled_at DESC", conn, params=(group_id,))
    conn.close()
    return df

def compute_balances(group_id):
    """
    Returns dict: {member: net_balance}
    Positive = others owe them; Negative = they owe others.
    """
    conn = get_conn()
    grp = conn.execute("SELECT members FROM split_groups WHERE id=?", (group_id,)).fetchone()
    conn.close()
    if not grp:
        return {}
    members = json.loads(grp[0])
    balances = {m: 0.0 for m in members}

    expenses = get_group_expenses(group_id)
    for _, exp in expenses.iterrows():
        paid_by = exp['paid_by']
        split   = exp['split_data']
        if paid_by in balances:
            balances[paid_by] += float(exp['total_amount'])
        for member, share in split.items():
            if member in balances:
                balances[member] -= float(share)
    # Apply settlements
    settlements = get_group_settlements(group_id)
    for _, s in settlements.iterrows():
        if s['paid_by'] in balances: balances[s['paid_by']] -= float(s['amount'])
        if s['paid_to'] in balances: balances[s['paid_to']] += float(s['amount'])
    return balances

def simplify_debts(balances):
    """
    Returns list of (debtor, creditor, amount) to minimise transactions.
    """
    creditors = sorted([(v, k) for k, v in balances.items() if v > 0.01], reverse=True)
    debtors   = sorted([(-v, k) for k, v in balances.items() if v < -0.01], reverse=True)
    transactions = []
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        credit_amt, creditor = creditors[i]
        debt_amt,   debtor   = debtors[j]
        settle = min(credit_amt, debt_amt)
        transactions.append((debtor, creditor, round(settle, 2)))
        creditors[i] = (credit_amt - settle, creditor)
        debtors[j]   = (debt_amt   - settle, debtor)
        if creditors[i][0] < 0.01: i += 1
        if debtors[j][0]   < 0.01: j += 1
    return transactions

# ── SESSION STATE ─────────────────────────────────────────────
for key, val in [("chat_history",[]),("gemini_key",""),("openai_key","")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 10px'>
      <div style='font-size:36px'>💸</div>
      <div style='font-size:18px;font-weight:800;color:#0f172a;letter-spacing:.05em'>Smart Expense</div>
      <div style='font-size:12px;color:#16a34a;font-weight:600;letter-spacing:.15em;text-transform:uppercase'>Tracker</div>
    </div>
    <hr style='border-color:#bae6fd;margin:10px 0 20px'>
    """, unsafe_allow_html=True)

    menu_items = {
        "🏠 Dashboard":       "Dashboard",
        "➕ Expense Entry":   "Expense Entry",
        "📊 View Analysis":   "View Analysis",
        "🧾 Receipt Scanner": "Receipt Scanner",
        "🎯 Set Budget":      "Set Budget Limit",
        "🤝 Split Bills":     "Split Bills",
        "📜 History":         "History",
    }
    page = st.radio("", list(menu_items.keys()), label_visibility="collapsed")
    page = menu_items[page]

    st.markdown("<hr style='border-color:#bae6fd;margin:20px 0 14px'>", unsafe_allow_html=True)

    df_all   = load_expenses(30)
    total_30 = df_all['amount'].sum() if not df_all.empty else 0
    income   = get_income()
    net      = income - total_30

    st.markdown(f"""
    <div class='metric-card' style='padding:14px;margin-bottom:8px'>
      <div class='metric-label'>30-Day Spend</div>
      <div class='metric-value red' style='font-size:22px'>₹{total_30:,.0f}</div>
    </div>
    <div class='metric-card' style='padding:14px;margin-bottom:8px'>
      <div class='metric-label'>Monthly Income</div>
      <div class='metric-value green' style='font-size:22px'>₹{income:,.0f}</div>
    </div>
    <div class='metric-card' style='padding:14px'>
      <div class='metric-label'>Net Savings</div>
      <div class='metric-value {"green" if net>=0 else "red"}' style='font-size:22px'>₹{net:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#bae6fd;margin:14px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;color:#64748b;text-align:center'>AI API Keys (optional)</div>", unsafe_allow_html=True)
    st.session_state.gemini_key = st.text_input("Gemini API Key", type="password",
                                                  value=st.session_state.gemini_key, placeholder="AIza...")
    st.session_state.openai_key = st.text_input("OpenAI API Key", type="password",
                                                  value=st.session_state.openai_key, placeholder="sk-...")

# ═════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("<h1 style='font-size:28px;font-weight:800;margin-bottom:4px'>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#64748b;font-size:14px;margin-bottom:24px'>{date.today().strftime('%A, %d %B %Y')}</div>", unsafe_allow_html=True)

    for level, msg in check_budget_alerts():
        cls = "notif-danger" if level=="danger" else "notif-warn"
        st.markdown(f"<div class='{cls}'>{msg}</div>", unsafe_allow_html=True)

    df_month = load_expenses(30)
    income   = get_income()
    total_sp = df_month['amount'].sum() if not df_month.empty else 0
    savings  = income - total_sp
    today_sp = df_month[df_month['date'].dt.date == date.today()]['amount'].sum() if not df_month.empty else 0
    txn_cnt  = len(df_month)
    sav_pct  = (savings/income*100) if income>0 else 0

    c1,c2,c3,c4 = st.columns(4)
    for col, label, val, color, sub in [
        (c1,"Monthly Spend",  f"₹{total_sp:,.0f}", "red",   f"of ₹{income:,.0f} income"),
        (c2,"Net Savings",    f"₹{savings:,.0f}",  "green" if savings>=0 else "red", f"{sav_pct:.1f}% saved"),
        (c3,"Today's Spend",  f"₹{today_sp:,.0f}", "amber", "transactions today"),
        (c4,"Transactions",   str(txn_cnt),         "blue",  "last 30 days"),
    ]:
        with col:
            st.markdown(f"""<div class='metric-card'>
              <div class='metric-label'>{label}</div>
              <div class='metric-value {color}'>{val}</div>
              <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Spending vs Savings</div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3,2])
    with col_left:
        if not df_month.empty:
            daily = df_month.groupby(df_month['date'].dt.date)['amount'].sum().reset_index()
            daily.columns = ['date','spent']
            daily['date'] = pd.to_datetime(daily['date'])
            if not daily.empty and pd.notna(daily['date'].min()) and pd.notna(daily['date'].max()):
                dr = pd.date_range(daily['date'].min(), daily['date'].max())
                daily = daily.set_index('date').reindex(dr, fill_value=0).reset_index()
                daily.columns = ['date','spent']
            daily['cumulative'] = daily['spent'].cumsum()
            daily['savings_line'] = (income/30)*(daily.index+1) - daily['cumulative']
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily['date'],y=daily['spent'],name='Daily Spend',marker_color='#f87171',opacity=.85))
            fig.add_trace(go.Scatter(x=daily['date'],y=daily['savings_line'].clip(0),name='Savings Trend',
                                     line=dict(color='#22c55e',width=2.5),fill='tozeroy',fillcolor='rgba(34,197,94,.08)'))
            fig.update_layout(**plotly_theme(),height=280,legend=dict(orientation="h",y=1.12,bgcolor="rgba(0,0,0,0)"),
                              xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="#e2e8f0"),
                              margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with col_right:
        if not df_month.empty:
            cat_sum = df_month.groupby('category')['amount'].sum()
            colors  = [CAT_COLORS.get(c,"#94a3b8") for c in cat_sum.index]
            fig2 = go.Figure(go.Pie(labels=cat_sum.index,values=cat_sum.values,hole=.62,
                                    marker_colors=colors,textinfo='label+percent',textfont_size=11,
                                    hovertemplate="%{label}<br>₹%{value:,.0f}<extra></extra>"))
            fig2.update_layout(**plotly_theme(),height=280,showlegend=False,
                               margin=dict(l=0,r=0,t=10,b=0),
                               annotations=[dict(text=f"₹{total_sp:,.0f}",x=.5,y=.5,
                                                 font_size=16,font_color="#0f172a",showarrow=False)])
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})

    # Savings goals
    st.markdown("<div class='section-title'>Savings Goals</div>", unsafe_allow_html=True)
    conn  = get_conn()
    goals = pd.read_sql("SELECT * FROM savings_goals", conn)
    conn.close()
    for _, g in goals.iterrows():
        pct = min((g['saved']/g['target'])*100, 100) if g['target'] > 0 else 0
        st.markdown(f"""<div class='metric-card'>
          <div style='display:flex;justify-content:space-between'>
            <span style='font-weight:700'>{g['goal_name']}</span>
            <span class='amber'>₹{g['saved']:,.0f} / ₹{g['target']:,.0f}</span>
          </div>""", unsafe_allow_html=True)
        st.progress(int(pct)/100, text=f"{pct:.1f}% achieved")
        st.markdown("</div>", unsafe_allow_html=True)

    # Rewards
    conn = get_conn()
    rewards = pd.read_sql("SELECT * FROM rewards ORDER BY earned_at DESC", conn)
    conn.close()
    if not rewards.empty:
        st.markdown("<div class='section-title'>🏆 Your Rewards</div>", unsafe_allow_html=True)
        badge_html = "".join(f"<span class='badge badge-gold'>{r['badge_name']}</span> " for _, r in rewards.iterrows())
        st.markdown(f"<div>{badge_html}</div>", unsafe_allow_html=True)

    # AI Advisor
    st.markdown("<div class='section-title'>🤖 AI Spending Advisor</div>", unsafe_allow_html=True)
    st.markdown("<div style='background:#f8fafc;border:1px solid #bae6fd;border-radius:18px;padding:18px;'>", unsafe_allow_html=True)
    for msg in st.session_state.chat_history[-4:]:
        cls = 'user-bubble' if msg['role']=='user' else 'ai-bubble'
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    q_cols = st.columns(2)
    for i, q in enumerate(["How can I save more?","Spending too much on food?","Tips for savings goal","Analyse entertainment"]):
        with q_cols[i%2]:
            if st.button(q, key=f"quick_{i}"):
                st.session_state.chat_history.append({"role":"user","content":q})
                st.session_state.chat_history.append({"role":"assistant","content":get_ai_response(q,df_month)})
                st.rerun()
    user_input = st.text_input("Ask your AI advisor…", key="ai_input", placeholder="e.g. Where am I wasting money?")
    if st.button("Send 💬", key="send_ai") and user_input.strip():
        st.session_state.chat_history.append({"role":"user","content":user_input})
        st.session_state.chat_history.append({"role":"assistant","content":get_ai_response(user_input,df_month)})
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
# PAGE: EXPENSE ENTRY
# ═════════════════════════════════════════════════════════════
elif page == "Expense Entry":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>➕ Add Expense</h1>", unsafe_allow_html=True)
    with st.form("expense_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            exp_date    = st.date_input("📅 Date", value=date.today())
            amount      = st.number_input("💰 Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            category    = st.selectbox("🏷️ Category", CATEGORIES)
        with c2:
            description = st.text_input("📝 Description", placeholder="e.g. Dinner at cafe")
            mood        = st.selectbox("😊 Your Mood", MOODS)
            payment     = st.selectbox("💳 Payment Method", PAYMENTS)
        submitted = st.form_submit_button("Add Expense ✅", use_container_width=True)
    if submitted:
        if amount > 0:
            mood_clean = mood.split()[0]
            add_expense(exp_date, amount, category, description, mood_clean, payment)
            st.markdown(f"<div class='notif-success'>✅ Added ₹{amount:,.2f} in <b>{category}</b></div>", unsafe_allow_html=True)
            tip = get_ai_response(f"I just spent ₹{amount:.0f} on {category}. Any quick advice?", load_expenses(30))
            st.markdown(f"<div class='ai-bubble'>{tip}</div>", unsafe_allow_html=True)
        else:
            st.warning("Please enter an amount > 0.")

    st.markdown("<div class='section-title'>Recent Expenses</div>", unsafe_allow_html=True)
    df_recent = load_expenses(7)
    if not df_recent.empty:
        disp = df_recent[['date','amount','category','description','mood','payment']].head(15).copy()
        disp['date']   = disp['date'].dt.strftime('%d %b')
        disp['amount'] = disp['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(disp, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════
# PAGE: VIEW ANALYSIS
# ═════════════════════════════════════════════════════════════
elif page == "View Analysis":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>📊 View Analysis</h1>", unsafe_allow_html=True)
    period   = st.selectbox("Time Period", ["Last 30 Days","Last 7 Days","Last 90 Days"])
    days_map = {"Last 30 Days":30,"Last 7 Days":7,"Last 90 Days":90}
    df = load_expenses(days_map[period])
    if df.empty:
        st.info("No expenses found. Add some first!")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["🥧 Category","😊 Mood","📈 Trend","📄 Export"])

    with tab1:
        cat_sum = df.groupby('category')['amount'].sum().reset_index()
        cat_sum.columns = ['Category','Amount']
        cat_colors = [CAT_COLORS.get(c,"#94a3b8") for c in cat_sum['Category']]
        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Pie(labels=cat_sum['Category'],values=cat_sum['Amount'],hole=.55,
                                   marker_colors=cat_colors,textinfo='label+percent'))
            fig.update_layout(**plotly_theme(),height=360,margin=dict(l=0,r=0,t=10,b=0),
                              title=dict(text="Spend Distribution",font_size=14))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        with col2:
            fig2 = go.Figure(go.Bar(x=cat_sum['Amount'],y=cat_sum['Category'],orientation='h',
                                    marker_color=cat_colors,text=cat_sum['Amount'].apply(lambda x:f"₹{x:,.0f}"),textposition='outside'))
            fig2.update_layout(**plotly_theme(),height=360,margin=dict(l=0,r=80,t=10,b=0),
                               title=dict(text="Category Bar",font_size=14))
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})

        budgets = load_budgets()
        if not budgets.empty:
            st.markdown("<div class='section-title'>Budget Utilisation</div>", unsafe_allow_html=True)
            merged = cat_sum.merge(budgets[['category','amount']].rename(columns={'amount':'budget','category':'Category'}),
                                   on='Category',how='left').fillna({'budget':5000})
            cols = st.columns(max(1, min(len(merged), 4)))
            for i,(_, row) in enumerate(merged.iterrows()):
                pct = min((row['Amount']/row['budget'])*100,100) if row['budget']>0 else 0
                color = "#4ade80" if pct<70 else "#fbbf24" if pct<90 else "#f87171"
                with cols[i%4]:
                    st.markdown(f"""<div class='metric-card' style='text-align:center'>
                      <div class='metric-label'>{row['Category']}</div>
                      <div class='metric-value' style='font-size:24px;color:{color}'>{pct:.0f}%</div>
                      <div class='metric-sub'>₹{row['Amount']:,.0f} / ₹{row['budget']:,.0f}</div>
                    </div>""", unsafe_allow_html=True)

    with tab2:
        mood_sum = df.groupby('mood_clean')['amount'].agg(['sum','count']).reset_index()
        mood_sum.columns = ['Mood','Total','Count']
        mood_colors = [MOOD_COLORS.get(m,"#94a3b8") for m in mood_sum['Mood']]
        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Bar(x=mood_sum['Mood'],y=mood_sum['Total'],marker_color=mood_colors,
                                   text=mood_sum['Total'].apply(lambda x:f"₹{x:,.0f}"),textposition='outside'))
            fig.update_layout(**plotly_theme(),height=320,title=dict(text="Spend per Mood",font_size=14),margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        with col2:
            fig2 = go.Figure(go.Bar(x=mood_sum['Mood'],y=mood_sum['Count'],marker_color=mood_colors,
                                    text=mood_sum['Count'],textposition='outside'))
            fig2.update_layout(**plotly_theme(),height=320,title=dict(text="Transactions per Mood",font_size=14),margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        pivot = df.groupby(['category','mood_clean'])['amount'].sum().unstack(fill_value=0)
        fig3 = go.Figure(go.Heatmap(z=pivot.values,x=pivot.columns,y=pivot.index,
                                    colorscale=[[0,"#f0f9ff"],[0.5,"#bae6fd"],[1,"#22c55e"]],
                                    hovertemplate="%{y}|%{x}<br>₹%{z:,.0f}<extra></extra>",
                                    text=pivot.values.astype(int),texttemplate="₹%{text:,}"))
        fig3.update_layout(
            **plotly_theme(),
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})

    with tab3:
        daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        daily.columns = ['date','spent']
        daily['date'] = pd.to_datetime(daily['date'])
        if not daily.empty and pd.notna(daily['date'].min()) and pd.notna(daily['date'].max()):
            dr = pd.date_range(daily['date'].min(),daily['date'].max())
            daily = daily.set_index('date').reindex(dr,fill_value=0).reset_index()
            daily.columns = ['date','spent']
        inc = get_income()
        daily['savings'] = (inc/30 - daily['spent']).cumsum()
        daily['cum_spend'] = daily['spent'].cumsum()
        daily['7d_avg'] = daily['spent'].rolling(7,min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=daily['date'],y=daily['spent'],name='Daily Spend',marker_color='#f87171',opacity=.7))
        fig.add_trace(go.Scatter(x=daily['date'],y=daily['7d_avg'],name='7-Day Avg',line=dict(color='#fbbf24',width=2,dash='dot')))
        fig.add_trace(go.Scatter(x=daily['date'],y=daily['cum_spend'],name='Cumul. Spend',line=dict(color='#f87171',width=2),yaxis='y2'))
        fig.add_trace(go.Scatter(x=daily['date'],y=daily['savings'].clip(0),name='Cumul. Savings',
                                 line=dict(color='#22c55e',width=2),fill='tozeroy',fillcolor='rgba(34,197,94,.07)',yaxis='y2'))
        fig.update_layout(**plotly_theme(),height=380,
                          yaxis=dict(title="Daily ₹",showgrid=True,gridcolor='#e2e8f0'),
                          yaxis2=dict(title="Cumulative ₹",overlaying='y',side='right',showgrid=False),
                          legend=dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)"),margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with tab4:
        month_label = date.today().strftime("%B %Y")
        st.markdown("<div class='section-title'>Export Monthly Data</div>", unsafe_allow_html=True)
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            pdf_bytes = generate_pdf_report(df, month_label)
            st.download_button("📄 Download PDF Report", data=pdf_bytes,
                               file_name=f"expense_report_{date.today().strftime('%Y_%m')}.pdf",
                               mime="application/pdf", use_container_width=True)
        with exp_col2:
            csv = df.drop(columns=['receipt_img'], errors='ignore').to_csv(index=False)
            st.download_button("📊 Download CSV Data", data=csv,
                               file_name=f"expenses_{date.today()}.csv",
                               mime="text/csv", use_container_width=True)

# ═════════════════════════════════════════════════════════════
# PAGE: RECEIPT SCANNER
# ═════════════════════════════════════════════════════════════
elif page == "Receipt Scanner":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>🧾 Receipt Scanner</h1>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Receipt (JPG / PNG)", type=["jpg","jpeg","png"])
    if uploaded:
        img_bytes = uploaded.read()
        b64_img   = base64.b64encode(img_bytes).decode()
        col1,col2 = st.columns([1,2])
        with col1:
            st.image(img_bytes, caption="Uploaded Receipt", use_container_width=True)
        with col2:
            extracted = None
            gk = st.session_state.get("gemini_key","")
            if GEMINI_AVAILABLE and gk:
                try:
                    import PIL.Image
                    from io import BytesIO as BIO
                    img_pil = PIL.Image.open(BIO(img_bytes))
                    prompt = ('Extract total amount, category (Food/Health/Bills/Travel/Entertainment/Learning/Assets/Other), '
                              'date (YYYY-MM-DD), description. Reply ONLY valid JSON: {"amount":100.0,"category":"Food","date":"2026-09-02","description":"Dinner"}')
                    if GEMINI_SDK_TYPE == "new":
                        client = google_genai.Client(api_key=gk)
                        resp = client.models.generate_content(model="gemini-2.0-flash", contents=[img_pil, prompt])
                        raw_text = resp.text
                    else:
                        genai.configure(api_key=gk)
                        model = GenerativeModel("gemini-2.0-flash")
                        resp = model.generate_content([prompt, img_pil])
                        raw_text = resp.text
                    clean_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_text.strip(), flags=re.IGNORECASE).strip()
                    extracted = json.loads(clean_json)
                except Exception: pass
            if extracted:
                st.success("✅ Receipt scanned!")
                with st.form("receipt_form"):
                    r_amount = st.number_input("Amount (₹)", value=float(extracted.get('amount',0)), step=1.0)
                    r_cat    = st.selectbox("Category", CATEGORIES,
                                            index=CATEGORIES.index(extracted.get('category','Other').strip().title()) if extracted.get('category','Other').strip().title() in CATEGORIES else 0)
                    r_date   = st.date_input("Date", value=date.today())
                    r_desc   = st.text_input("Description", value=extracted.get('description','Receipt scan'))
                    r_mood   = st.selectbox("Mood", MOODS)
                    if st.form_submit_button("💾 Save from Receipt", use_container_width=True):
                        add_expense(r_date,r_amount,r_cat,r_desc,r_mood.split()[0],"Receipt",b64_img)
                        st.success("Saved!")
            else:
                st.info("Fill details manually:")
                with st.form("manual_receipt_form"):
                    r_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
                    r_cat    = st.selectbox("Category", CATEGORIES)
                    r_date   = st.date_input("Date", value=date.today())
                    r_desc   = st.text_input("Description")
                    r_mood   = st.selectbox("Mood", MOODS)
                    if st.form_submit_button("💾 Save", use_container_width=True):
                        if r_amount > 0:
                            add_expense(r_date,r_amount,r_cat,r_desc,r_mood.split()[0],"Receipt",b64_img)
                            st.success("Saved!")

# ═════════════════════════════════════════════════════════════
# PAGE: SET BUDGET LIMIT
# ═════════════════════════════════════════════════════════════
elif page == "Set Budget Limit":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>🎯 Set Budget Limit</h1>", unsafe_allow_html=True)
    month_str = date.today().strftime("%Y-%m")
    income    = get_income(month_str)
    with st.expander("💼 Set Monthly Income", expanded=income==0):
        new_income = st.number_input("Monthly Income (₹)", value=float(income), step=1000.0, min_value=0.0)
        if st.button("Save Income"):
            conn = get_conn()
            conn.execute("DELETE FROM income WHERE month=?", (month_str,))
            conn.execute("INSERT INTO income(month,amount) VALUES(?,?)", (month_str,new_income))
            conn.commit(); conn.close()
            st.success(f"Income set to ₹{new_income:,.0f}"); st.rerun()

    budgets  = load_budgets(month_str)
    existing = dict(zip(budgets['category'],budgets['amount'])) if not budgets.empty else {}
    with st.form("budget_form"):
        cols = st.columns(2)
        new_budgets = {}
        for i,cat in enumerate(CATEGORIES):
            with cols[i%2]:
                new_budgets[cat] = st.number_input(cat, value=float(existing.get(cat,3000)), step=500.0, min_value=0.0, key=f"b_{cat}")
        if st.form_submit_button("💾 Save Budgets", use_container_width=True):
            conn = get_conn()
            for cat,amt in new_budgets.items():
                conn.execute("INSERT OR REPLACE INTO budgets(category,amount,month) VALUES(?,?,?)", (cat,amt,month_str))
            conn.commit(); conn.close()
            st.success("Budgets saved!"); st.rerun()

    alerts = check_budget_alerts()
    if alerts:
        for level,msg in alerts:
            st.markdown(f"<div class='{'notif-danger' if level=='danger' else 'notif-warn'}'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='notif-success'>✅ All budgets healthy!</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🌱 Savings Goals</div>", unsafe_allow_html=True)
    conn  = get_conn()
    goals = pd.read_sql("SELECT * FROM savings_goals", conn)
    conn.close()
    with st.form("goal_form"):
        g1,g2,g3,g4 = st.columns(4)
        with g1: g_name   = st.text_input("Goal Name", placeholder="Emergency Fund")
        with g2: g_target = st.number_input("Target (₹)", min_value=0.0, step=1000.0)
        with g3: g_saved  = st.number_input("Already Saved (₹)", min_value=0.0, step=100.0)
        with g4: g_dead   = st.date_input("Deadline")
        if st.form_submit_button("Add Goal ➕", use_container_width=True):
            conn = get_conn()
            conn.execute("INSERT INTO savings_goals(goal_name,target,saved,deadline) VALUES(?,?,?,?)",
                         (g_name,g_target,g_saved,str(g_dead)))
            conn.commit(); conn.close()
            st.success("Goal added!"); st.rerun()

    for _, g in goals.iterrows():
        pct   = min((g['saved']/g['target'])*100,100) if g['target']>0 else 0
        color = "#4ade80" if pct>=75 else "#fbbf24" if pct>=40 else "#f87171"
        st.markdown(f"""<div class='metric-card'>
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <span style='font-weight:700'>{g['goal_name']}</span>
            <span style='color:{color};font-weight:700'>{pct:.1f}%</span>
          </div>
          <div style='color:#64748b;font-size:13px;margin:4px 0 8px'>
            ₹{g['saved']:,.0f} saved of ₹{g['target']:,.0f} · Due: {g['deadline'] or 'No deadline'}
          </div>""", unsafe_allow_html=True)
        st.progress(int(pct)/100)
        if g['target'] > g['saved'] and g['deadline']:
            try:
                days_left = (date.fromisoformat(str(g['deadline'])) - date.today()).days
                if days_left > 0:
                    st.markdown(f"<div style='font-size:12px;color:#64748b'>Save ₹{(g['target']-g['saved'])/days_left:,.0f}/day to meet deadline</div>", unsafe_allow_html=True)
            except Exception: pass
        st.markdown("</div>", unsafe_allow_html=True)

    if not goals.empty:
        with st.expander("🗑️ Delete Goal"):
            del_options = {f"{r['goal_name']} (Target: ₹{r['target']:,.0f})": r['id'] for _, r in goals.iterrows()}
            del_choice  = st.selectbox("Select goal to delete", list(del_options.keys()))
            if st.button("Delete Goal", type="primary"):
                gid = del_options[del_choice]
                conn = get_conn()
                conn.execute("DELETE FROM savings_goals WHERE id=?", (gid,))
                conn.commit(); conn.close()
                st.success("Goal deleted!"); st.rerun()

# ═════════════════════════════════════════════════════════════
# PAGE: SPLIT BILLS
# ═════════════════════════════════════════════════════════════
elif page == "Split Bills":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>🤝 Split Bills</h1>", unsafe_allow_html=True)
    st.markdown("<div style='color:#64748b;margin-bottom:24px'>Split shared expenses with friends & groups — like Splitwise!</div>", unsafe_allow_html=True)

    tab_groups, tab_add_exp, tab_settle, tab_analytics = st.tabs(
        ["👥 Groups", "➕ Add Split Expense", "💰 Settle Up", "📊 Analytics"])

    # ── TAB 1: Groups ──────────────────────────────────────────
    with tab_groups:
        col_list, col_create = st.columns([2, 1])

        with col_create:
            st.markdown("<div class='section-title'>Create New Group</div>", unsafe_allow_html=True)
            with st.form("create_group_form"):
                g_name = st.text_input("Group Name", placeholder="Trip to Goa 🏖️")
                members_input = st.text_area("Members (one per line)", placeholder="Alice\nBob\nCharlie", height=120)
                if st.form_submit_button("Create Group ✅", use_container_width=True):
                    members = [m.strip() for m in members_input.strip().split("\n") if m.strip()]
                    if g_name and len(members) >= 2:
                        conn = get_conn()
                        conn.execute("INSERT INTO split_groups(group_name,members) VALUES(?,?)",
                                     (g_name, json.dumps(members)))
                        conn.commit(); conn.close()
                        st.success(f"Group '{g_name}' created with {len(members)} members!")
                        st.rerun()
                    else:
                        st.warning("Enter a group name and at least 2 members.")

        with col_list:
            st.markdown("<div class='section-title'>Your Groups</div>", unsafe_allow_html=True)
            groups = get_all_groups()
            if groups.empty:
                st.info("No groups yet. Create one →")
            else:
                for _, grp in groups.iterrows():
                    members = json.loads(grp['members'])
                    exps    = get_group_expenses(grp['id'])
                    total   = exps['total_amount'].sum() if not exps.empty else 0
                    balances = compute_balances(grp['id'])
                    pending  = sum(1 for v in balances.values() if abs(v) > 0.5)

                    status_color = "#f87171" if pending > 0 else "#4ade80"
                    status_text  = f"⚡ {pending} pending settlements" if pending > 0 else "✅ All settled"

                    st.markdown(f"""
                    <div class='split-card'>
                      <div class='split-card-title'>📌 {grp['group_name']}</div>
                      <div style='font-size:13px;color:#64748b;margin-bottom:8px'>
                        👥 {', '.join(members)} &nbsp;|&nbsp; {len(exps)} expenses &nbsp;|&nbsp; Total: ₹{total:,.0f}
                      </div>
                      <span style='font-size:12px;font-weight:600;color:{status_color}'>{status_text}</span>
                    </div>""", unsafe_allow_html=True)

                    with st.expander(f"View balances — {grp['group_name']}"):
                        balances = compute_balances(grp['id'])
                        debts    = simplify_debts(balances)

                        bcol1, bcol2 = st.columns(2)
                        with bcol1:
                            st.markdown("**Net Balances**")
                            for member, bal in balances.items():
                                if bal > 0.5:
                                    st.markdown(f"<div class='split-get'>💚 {member} gets back ₹{bal:,.2f}</div>", unsafe_allow_html=True)
                                elif bal < -0.5:
                                    st.markdown(f"<div class='split-owe'>❤️ {member} owes ₹{abs(bal):,.2f}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div class='split-settled'>✔️ {member} is settled</div>", unsafe_allow_html=True)
                        with bcol2:
                            st.markdown("**Simplified Payments**")
                            if debts:
                                for debtor, creditor, amount in debts:
                                    st.markdown(f"<div class='split-owe'>💸 {debtor} → {creditor}: ₹{amount:,.2f}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div class='split-settled'>✔️ No payments needed!</div>", unsafe_allow_html=True)

                        st.markdown("**Expense List**")
                        if not exps.empty:
                            for _, e in exps.iterrows():
                                shares = e['split_data']
                                share_str = " | ".join(f"{k}: ₹{v:,.0f}" for k,v in shares.items())
                                st.markdown(f"""
                                <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin:4px 0;font-size:13px'>
                                  <b>{e['description']}</b> &nbsp;·&nbsp; ₹{e['total_amount']:,.0f}
                                  &nbsp;·&nbsp; Paid by <b>{e['paid_by']}</b> &nbsp;·&nbsp; {e['date']}<br>
                                  <span style='color:#64748b'>{share_str}</span>
                                </div>""", unsafe_allow_html=True)

                # Delete a group
                st.markdown("---")
                with st.expander("🗑️ Delete a Group"):
                    del_options = {f"{r['group_name']} (id:{r['id']})": r['id'] for _,r in groups.iterrows()}
                    del_choice  = st.selectbox("Select group to delete", list(del_options.keys()))
                    if st.button("Delete Group", type="primary"):
                        gid = del_options[del_choice]
                        conn = get_conn()
                        conn.execute("DELETE FROM split_expenses WHERE group_id=?", (gid,))
                        conn.execute("DELETE FROM split_settlements WHERE group_id=?", (gid,))
                        conn.execute("DELETE FROM split_groups WHERE id=?", (gid,))
                        conn.commit(); conn.close()
                        st.success("Group deleted."); st.rerun()

    # ── TAB 2: Add Split Expense ───────────────────────────────
    with tab_add_exp:
        st.markdown("<div class='section-title'>Add a Split Expense</div>", unsafe_allow_html=True)
        groups = get_all_groups()
        if groups.empty:
            st.info("Create a group first in the Groups tab.")
        else:
            group_options = {r['group_name']: r['id'] for _,r in groups.iterrows()}
            selected_group_name = st.selectbox("Select Group", list(group_options.keys()))
            selected_group_id   = group_options[selected_group_name]

            selected_group_row = groups[groups['id'] == selected_group_id].iloc[0]
            members = json.loads(selected_group_row['members'])

            with st.form("add_split_expense_form"):
                c1, c2 = st.columns(2)
                with c1:
                    s_desc    = st.text_input("📝 Description", placeholder="Hotel booking, Dinner, Taxi…")
                    s_amount  = st.number_input("💰 Total Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
                    s_paid_by = st.selectbox("💳 Paid By", members)
                    s_date    = st.date_input("📅 Date", value=date.today())
                with c2:
                    s_split_type = st.radio("Split Type", ["Equal", "Custom Amount", "Percentage"],
                                            help="Equal: divide equally | Custom: enter each person's share | Percentage: enter % each")

                    st.markdown("**Member Shares**")
                    shares = {}
                    if s_split_type == "Equal":
                        per_person = round(s_amount / len(members), 2) if len(members) > 0 else 0
                        for m in members:
                            shares[m] = per_person
                            st.markdown(f"<div style='font-size:13px;padding:4px 0'>{m}: <b>₹{per_person:,.2f}</b></div>", unsafe_allow_html=True)
                    elif s_split_type == "Custom Amount":
                        for m in members:
                            shares[m] = st.number_input(f"{m} (₹)", min_value=0.0, step=10.0, format="%.2f", key=f"cust_{m}")
                    else:  # Percentage
                        pcts = {}
                        for m in members:
                            pcts[m] = st.number_input(f"{m} (%)", min_value=0.0, max_value=100.0, step=5.0, key=f"pct_{m}")
                        for m in members:
                            shares[m] = round(s_amount * pcts[m] / 100, 2)

                submitted_split = st.form_submit_button("Add Split Expense ✅", use_container_width=True)

            if submitted_split:
                if s_amount > 0 and s_desc.strip():
                    total_shares = sum(shares.values())
                    if s_split_type != "Equal" and abs(total_shares - s_amount) > 1:
                        st.error(f"Shares total ₹{total_shares:,.2f} but expense is ₹{s_amount:,.2f}. Please fix.")
                    else:
                        if s_split_type == "Equal" and len(members) > 0:
                            diff = round(s_amount - sum(shares.values()), 2)
                            shares[members[0]] = round(shares[members[0]] + diff, 2)
                        conn = get_conn()
                        conn.execute(
                            "INSERT INTO split_expenses(group_id,description,total_amount,paid_by,split_type,split_data,date) VALUES(?,?,?,?,?,?,?)",
                            (selected_group_id, s_desc, s_amount, s_paid_by,
                             s_split_type.lower(), json.dumps(shares), str(s_date)))
                        conn.commit(); conn.close()
                        st.markdown(f"<div class='notif-success'>✅ ₹{s_amount:,.2f} split among {len(members)} members added!</div>", unsafe_allow_html=True)

                        st.markdown("**Split Summary:**")
                        for m, amt in shares.items():
                            icon = "💚" if m == s_paid_by else "❤️"
                            action = "paid & gets back" if m == s_paid_by else "owes"
                            net = s_amount - amt if m == s_paid_by else amt
                            st.markdown(f"<div class='{'split-get' if m==s_paid_by else 'split-owe'}'>{icon} {m} {action} ₹{net:,.2f}</div>",
                                        unsafe_allow_html=True)
                else:
                    st.warning("Please enter a description and amount > 0.")

    # ── TAB 3: Settle Up ───────────────────────────────────────
    with tab_settle:
        st.markdown("<div class='section-title'>💰 Record a Settlement</div>", unsafe_allow_html=True)
        groups = get_all_groups()
        if groups.empty:
            st.info("No groups yet.")
        else:
            group_options = {r['group_name']: r['id'] for _,r in groups.iterrows()}
            sel_grp_name  = st.selectbox("Select Group", list(group_options.keys()), key="settle_grp")
            sel_grp_id    = group_options[sel_grp_name]
            grp_row       = groups[groups['id']==sel_grp_id].iloc[0]
            members       = json.loads(grp_row['members'])

            balances = compute_balances(sel_grp_id)
            debts    = simplify_debts(balances)
            if debts:
                st.markdown("**Suggested Payments:**")
                for debtor, creditor, amount in debts:
                    st.markdown(f"<div class='split-owe'>💸 {debtor} should pay {creditor}: ₹{amount:,.2f}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='notif-success'>✅ Everyone is settled in this group!</div>", unsafe_allow_html=True)

            st.markdown("---")
            with st.form("settlement_form"):
                sc1, sc2, sc3 = st.columns(3)
                with sc1: s_from   = st.selectbox("From (who pays)", members)
                with sc2: s_to     = st.selectbox("To (who receives)", members)
                with sc3: s_amt    = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
                if st.form_submit_button("✅ Record Settlement", use_container_width=True):
                    if s_from == s_to:
                        st.error("From and To cannot be the same person.")
                    elif s_amt <= 0:
                        st.error("Amount must be > 0.")
                    else:
                        conn = get_conn()
                        conn.execute("INSERT INTO split_settlements(group_id,paid_by,paid_to,amount) VALUES(?,?,?,?)",
                                     (sel_grp_id, s_from, s_to, s_amt))
                        conn.commit(); conn.close()
                        st.markdown(f"<div class='notif-success'>✅ {s_from} paid {s_to} ₹{s_amt:,.2f}. Recorded!</div>", unsafe_allow_html=True)
                        st.rerun()

            settlements = get_group_settlements(sel_grp_id)
            if not settlements.empty:
                st.markdown("<div class='section-title'>Settlement History</div>", unsafe_allow_html=True)
                for _, s in settlements.iterrows():
                    st.markdown(f"""
                    <div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:10px 14px;margin:4px 0;font-size:13px'>
                      ✅ <b>{s['paid_by']}</b> paid <b>{s['paid_to']}</b> ₹{s['amount']:,.2f}
                      &nbsp;·&nbsp; <span style='color:#64748b'>{str(s['settled_at'])[:10]}</span>
                    </div>""", unsafe_allow_html=True)

    # ── TAB 4: Analytics ───────────────────────────────────────
    with tab_analytics:
        st.markdown("<div class='section-title'>Split Bill Analytics</div>", unsafe_allow_html=True)
        groups = get_all_groups()
        if groups.empty:
            st.info("No groups yet.")
        else:
            group_options = {r['group_name']: r['id'] for _,r in groups.iterrows()}
            sel_grp_name  = st.selectbox("Select Group", list(group_options.keys()), key="analytics_grp")
            sel_grp_id    = group_options[sel_grp_name]
            grp_row       = groups[groups['id']==sel_grp_id].iloc[0]
            members       = json.loads(grp_row['members'])
            exps          = get_group_expenses(sel_grp_id)

            if exps.empty:
                st.info("No expenses in this group yet.")
            else:
                total_group = exps['total_amount'].sum()
                avg_exp     = exps['total_amount'].mean()

                mc1,mc2,mc3 = st.columns(3)
                for col, label, val, color in [
                    (mc1,"Total Group Spend",  f"₹{total_group:,.0f}", "blue"),
                    (mc2,"Number of Expenses", str(len(exps)),          "purple"),
                    (mc3,"Avg per Expense",    f"₹{avg_exp:,.0f}",     "amber"),
                ]:
                    with col:
                        st.markdown(f"""<div class='metric-card' style='padding:14px'>
                          <div class='metric-label'>{label}</div>
                          <div class='metric-value {color}' style='font-size:24px'>{val}</div>
                        </div>""", unsafe_allow_html=True)

                acol1, acol2 = st.columns(2)

                # Who paid the most
                with acol1:
                    paid_by_sum = exps.groupby('paid_by')['total_amount'].sum().reset_index()
                    paid_by_sum.columns = ['Member','Paid']
                    colors = ['#22c55e','#3b82f6','#f59e0b','#f87171','#a78bfa'][:len(paid_by_sum)]
                    fig = go.Figure(go.Bar(x=paid_by_sum['Member'], y=paid_by_sum['Paid'],
                                          marker_color=colors,
                                          text=paid_by_sum['Paid'].apply(lambda x:f"₹{x:,.0f}"),
                                          textposition='outside'))
                    fig.update_layout(**plotly_theme(), height=300,
                                      title=dict(text="Who Paid the Most?",font_size=14),
                                      margin=dict(l=0,r=0,t=40,b=0))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

                # Each member's share burden
                with acol2:
                    member_burden = {m: 0.0 for m in members}
                    for _, e in exps.iterrows():
                        for m, share in e['split_data'].items():
                            if m in member_burden:
                                member_burden[m] += float(share)
                    burden_df = pd.DataFrame(list(member_burden.items()), columns=['Member','Share'])
                    fig2 = go.Figure(go.Pie(labels=burden_df['Member'], values=burden_df['Share'],
                                            hole=.5,
                                            marker_colors=['#22c55e','#3b82f6','#f59e0b','#f87171','#a78bfa'][:len(burden_df)],
                                            textinfo='label+percent'))
                    fig2.update_layout(**plotly_theme(), height=300,
                                       title=dict(text="Expense Share Burden",font_size=14),
                                       margin=dict(l=0,r=0,t=40,b=0))
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

                # Timeline
                exps['date'] = pd.to_datetime(exps['date'])
                timeline = exps.groupby('date')['total_amount'].sum().reset_index()
                fig3 = go.Figure(go.Scatter(x=timeline['date'], y=timeline['total_amount'],
                                            mode='lines+markers',
                                            line=dict(color='#22c55e',width=2.5),
                                            marker=dict(size=8,color='#16a34a'),
                                            fill='tozeroy', fillcolor='rgba(34,197,94,.08)'))
                fig3.update_layout(**plotly_theme(), height=260,
                                   title=dict(text="Group Spending Timeline",font_size=14),
                                   margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

                # Balance bar
                st.markdown("<div class='section-title'>Final Balance Chart</div>", unsafe_allow_html=True)
                balances = compute_balances(sel_grp_id)
                bal_df   = pd.DataFrame(list(balances.items()), columns=['Member','Balance'])
                bar_colors = ['#4ade80' if b>=0 else '#f87171' for b in bal_df['Balance']]
                fig4 = go.Figure(go.Bar(x=bal_df['Member'], y=bal_df['Balance'],
                                        marker_color=bar_colors,
                                        text=bal_df['Balance'].apply(lambda x:f"₹{x:+,.0f}"),
                                        textposition='outside'))
                fig4.add_hline(y=0, line_dash="dot", line_color="#64748b")
                fig4.update_layout(**plotly_theme(), height=280,
                                   yaxis=dict(title="₹ (positive = gets back, negative = owes)"),
                                   margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})

# ═════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═════════════════════════════════════════════════════════════
elif page == "History":
    st.markdown("<h1 style='font-size:28px;font-weight:800'>📜 Expense History</h1>", unsafe_allow_html=True)
    df = load_expenses()
    if df.empty:
        st.info("No expenses yet."); st.stop()

    col1,col2,col3 = st.columns(3)
    with col1: cat_filter  = st.multiselect("Category", CATEGORIES, default=[])
    with col2: mood_filter = st.multiselect("Mood", [m.split()[0] for m in MOODS], default=[])
    with col3: date_range  = st.date_input("Date Range",
                                            value=(date.today()-timedelta(days=30), date.today()),
                                            max_value=date.today())

    filtered = df.copy()
    if cat_filter:  filtered = filtered[filtered['category'].isin(cat_filter)]
    if mood_filter: filtered = filtered[filtered['mood_clean'].isin(mood_filter)]
    if isinstance(date_range, (tuple, list)):
        if len(date_range) == 2:
            filtered = filtered[(filtered['date'].dt.date>=date_range[0]) & (filtered['date'].dt.date<=date_range[1])]
        elif len(date_range) == 1:
            filtered = filtered[filtered['date'].dt.date>=date_range[0]]
    elif isinstance(date_range, date):
        filtered = filtered[filtered['date'].dt.date==date_range]

    c1,c2,c3 = st.columns(3)
    avg = filtered['amount'].mean() if not filtered.empty else 0
    for col, label, val, color in [
        (c1,"Total",       f"₹{filtered['amount'].sum():,.0f}", "red"),
        (c2,"Transactions",str(len(filtered)),                  "blue"),
        (c3,"Avg per Txn", f"₹{avg:,.0f}",                     "amber"),
    ]:
        with col:
            st.markdown(f"""<div class='metric-card' style='padding:14px'>
              <div class='metric-label'>{label}</div>
              <div class='metric-value {color}' style='font-size:22px'>{val}</div>
            </div>""", unsafe_allow_html=True)

    display = filtered[['date','amount','category','description','mood','payment']].copy()
    display['date']   = display['date'].dt.strftime('%d %b %Y')
    display['amount'] = display['amount'].apply(lambda x: f"₹{x:,.2f}")
    st.dataframe(display.head(200), use_container_width=True, hide_index=True)

    with st.expander("🗑️ Delete an Expense"):
        del_id = st.number_input("Expense ID to delete", min_value=1, step=1)
        if st.button("Delete", type="primary"):
            conn = get_conn()
            conn.execute("DELETE FROM expenses WHERE id=?", (int(del_id),))
            conn.commit(); conn.close()
            st.success(f"Deleted expense #{del_id}"); st.rerun()

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("""
<hr style='border-color:#bae6fd;margin:40px 0 10px'>
<div style='text-align:center;color:#64748b;font-size:12px;padding-bottom:20px'>
  Smart Expense Tracker · Built with Streamlit · Now with Splitwise-style Bill Splitting 🤝
</div>
""", unsafe_allow_html=True)
