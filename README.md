# AI-based-Smart-expense-tracker

A personal finance web app built with **Streamlit** and **SQLite**. Track expenses, set budgets, reach savings goals, split bills with friends (Splitwise-style), and get AI-powered spending advice, all in one place.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-ff4b4b)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

| Module | What it does |
|---|---|
| 🏠 **Dashboard** | Monthly spend, net savings, daily trend vs. savings line, category donut chart, savings-goal progress, reward badges |
| ➕ **Expense Entry** | Log expenses with date, amount, category, description, **mood** and payment method |
| 📊 **View Analysis** | Category, mood and trend analysis (7 / 30 / 90 days), mood-vs-category heatmap, budget utilisation |
| 📄 **Export** | Download a monthly **PDF report** or **CSV** of your data |
| 🧾 **Receipt Scanner** | Upload a receipt image; Gemini extracts amount, category, date and description (manual entry fallback) |
| 🎯 **Budgets & Goals** | Per-category monthly budgets with 80% / 100% alerts, income tracking, savings goals with a "save ₹/day" hint |
| 🤝 **Split Bills** | Groups, equal / custom / percentage splits, simplified settle-up suggestions, settlement history, group analytics |
| 🤖 **AI Advisor** | Chat-style spending advice via Google Gemini or OpenAI, with built-in tips when no API key is set |
| 🏆 **Rewards** | Badges for good habits (e.g. *Saver of the Month*, *Consistent Tracker*) |
| 📜 **History** | Filter by category, mood and date range; delete entries |

## 🧰 Tech Stack

- [Streamlit](https://streamlit.io/): UI
- SQLite: local storage (no setup required)
- pandas / NumPy: data handling
- Plotly: interactive charts
- ReportLab: PDF reports
- Google Gemini (`google-genai`) / OpenAI: optional AI features

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/smart-expense-tracker.git
cd smart-expense-tracker
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at <http://localhost:8501>. On first launch it creates `smart_expense_tracker.db` and **seeds demo data** (60 sample expenses, budgets, a savings goal and a demo split group) so you can explore right away.

## 🔑 AI Features (Optional)

The app works fully without any API key. To enable the AI advisor and receipt scanning, paste a key into the sidebar:

- **Gemini API key**: get one at [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenAI API key**: get one at [platform.openai.com](https://platform.openai.com/api-keys)

Keys are held only in the Streamlit session state and are **not** written to the database or disk. Receipt scanning requires a Gemini key; the AI advisor works with either.

## 🗂️ Project Structure

```
smart-expense-tracker/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Theme and server settings
├── .gitignore
├── .gitattributes
├── LICENSE
└── README.md
```

## 🗄️ Database

All data is stored in a local SQLite file (`smart_expense_tracker.db`), created automatically.

| Table | Purpose |
|---|---|
| `expenses` | Personal expenses (incl. mood, payment, optional receipt image) |
| `budgets` | Monthly per-category budgets |
| `income` | Monthly income |
| `savings_goals` | Savings targets and progress |
| `rewards` | Earned badges |
| `split_groups` | Bill-splitting groups and members |
| `split_expenses` | Shared expenses with per-member shares |
| `split_settlements` | Recorded payments between members |

> ⚠️ The database holds personal financial data and is excluded from Git via `.gitignore`. Delete the `.db` file to reset the app.

## ☁️ Deploying

**Streamlit Community Cloud**

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), click **New app**, and select this repo with `app.py` as the main file.

Note: Community Cloud storage is ephemeral, so the SQLite database resets when the app restarts. For persistent multi-user use, swap SQLite for a hosted database.

## 🛣️ Roadmap

- [ ] User authentication / multi-user support
- [ ] Recurring expenses and reminders
- [ ] Multi-currency support
- [ ] Split `app.py` into modules (`db.py`, `ui/`, `services/`)
- [ ] Unit tests for balance and debt-simplification logic

## 🤝 Contributing

Contributions are welcome! Fork the repo, create a feature branch, and open a pull request.

```bash
git checkout -b feature/my-feature
git commit -m "Add my feature"
git push origin feature/my-feature
```
