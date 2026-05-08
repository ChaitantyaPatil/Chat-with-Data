# 💬 Chat with Data

> **AI-powered data analysis** — Upload CSV/Excel files and interact with your data using natural language queries, auto-generated charts, and intelligent insights.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.4+-1C3C3C?style=flat-square)
![Plotly](https://img.shields.io/badge/Plotly-6.0+-3F4F75?style=flat-square&logo=plotly&logoColor=white)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 **File Upload** | CSV & Excel (.xlsx/.xls) with encoding detection |
| 🧹 **Auto-Cleaning** | Duplicates, missing values, currency symbols, date parsing |
| 🔍 **Schema Detection** | Automatic column classification (numerical, categorical, datetime, ID, currency) |
| 📊 **Smart Charts** | AI-suggested Plotly charts based on query intent |
| 🤖 **Natural Language Queries** | Ask questions like "Top 10 customers by revenue" |
| 💡 **AI Insights** | Business-friendly insights powered by LLM |
| 🧠 **Conversational Memory** | Follow-up queries with context retention |
| 📥 **Export** | Download cleaned data (CSV/Excel), charts (PNG), insights (Markdown) |
| 🔐 **Safe Execution** | Sandboxed code execution with blocked dangerous patterns |

---

## 🏗️ Architecture

```
chat-with-data/
│
├── app/                          # Streamlit Frontend
│   ├── main.py                   # Entry point & page routing
│   ├── components/
│   │   ├── uploader.py           # File upload widget
│   │   ├── sidebar.py            # Navigation & dataset info
│   │   ├── chatbox.py            # Conversational chat UI
│   │   ├── charts.py             # Interactive chart component
│   │   └── summary_cards.py      # KPI metric cards
│   └── pages/
│       ├── dashboard.py          # Main overview dashboard
│       ├── insights.py           # AI-generated insights
│       └── data_preview.py       # DataFrame explorer
│
├── backend/                      # Business Logic
│   ├── data_loader.py            # CSV/Excel loading
│   ├── data_cleaner.py           # Auto-cleaning pipeline
│   ├── schema_detector.py        # Column classification
│   ├── query_engine.py           # LangGraph query pipeline
│   ├── chart_engine.py           # Plotly chart rendering
│   ├── insight_engine.py         # AI insights generation
│   ├── memory.py                 # Conversational memory
│   └── export_engine.py          # Data/chart/insight export
│
├── llm/                          # LLM / AI Layer
│   ├── llm_client.py             # LangChain ChatOpenAI client
│   ├── prompt_templates.py       # Prompt engineering
│   └── code_executor.py          # Safe code sandbox
│
├── utils/                        # Utilities
│   ├── config.py                 # Environment configuration
│   ├── logger.py                 # Structured logging
│   └── validators.py             # File & data validation
│
├── data/uploads/                 # Uploaded files (gitignored)
├── tests/                        # Unit tests
├── .env.example                  # Environment template
├── requirements.txt              # Dependencies
└── pyproject.toml                # Project configuration
```

### Query Flow

```
User Query → LLM (LangGraph) → Generate Pandas Code → Validate → Execute Safely → Return (Table / Chart / Insight)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- An API key for the NVIDIA API (or any OpenAI-compatible endpoint)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/chat-with-data.git
cd chat-with-data

# 2. Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Install dependencies (with uv)
uv sync

# 4. Run the application
uv run streamlit run app/main.py
```

### Alternative (pip)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```

---

## ⚙️ Configuration

All settings are managed via the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your API key |
| `OPENAI_BASE_URL` | `https://integrate.api.nvidia.com/v1` | API endpoint |
| `OPENAI_MODEL` | `openai/gpt-oss-120b` | Model identifier |
| `MAX_UPLOAD_SIZE_MB` | `200` | Maximum upload file size |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CHUNK_SIZE` | `50000` | Rows per chunk for large files |

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_data_cleaner.py -v
```

---

## 📸 Screenshots

> *Screenshots will be added after initial deployment.*

---

## 🚢 Deployment

### Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set `app/main.py` as the main file
5. Add environment secrets in the Streamlit dashboard

### Render

1. Create a new Web Service on [render.com](https://render.com)
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run app/main.py --server.port $PORT --server.headless true`
4. Add environment variables in Render dashboard

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.headless", "true"]
```

---

## 🔮 Future Improvements

- [ ] Multi-file support and cross-dataset queries
- [ ] SQL database connections
- [ ] User authentication and session persistence
- [ ] Custom dashboard builder (drag & drop)
- [ ] Advanced anomaly detection with ML models
- [ ] Collaborative sharing and annotations
- [ ] Webhook / API mode for programmatic access
- [ ] PDF report generation

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p>Built with ❤️ using Streamlit, LangChain, LangGraph & Plotly</p>
</div>
