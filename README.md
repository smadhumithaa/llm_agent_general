# 🤖 Aria — General Purpose LLM Agent

> A production-grade ReAct agent powered by **Google Gemini 1.5 Pro** and **LangChain** that autonomously reasons, selects tools, and executes multi-step tasks.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-green?logo=chainlink)
![Gemini](https://img.shields.io/badge/Gemini-1.5_Pro-orange?logo=google)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-teal?logo=fastapi)
![React](https://img.shields.io/badge/React-18+-blue?logo=react)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🧠 Problem Statement

Large Language Models are powerful but limited to static knowledge — they cannot browse the web, run calculations, check live data, or read your files out of the box. A single prompt is not enough for complex, multi-step tasks that require reasoning across different information sources.

**Aria** solves this with a ReAct (Reasoning + Acting) agent loop that:
- Thinks step-by-step before choosing any tool
- Chains multiple tools together when needed
- Maintains conversation memory across turns
- Exposes its full reasoning chain transparently in the UI

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔍 **Web Search** | Real-time DuckDuckGo search — no API key required |
| 🌤️ **Weather** | Live weather via OpenWeatherMap for any city |
| 📰 **News** | Latest headlines on any topic via NewsAPI |
| 🐍 **Code Execution** | Sandboxed Python runner for math, stats, and data tasks |
| 📄 **Doc Summarizer** | Upload PDF/DOCX and get a structured summary via Gemini |
| 🧠 **ReAct Loop** | Thought → Action → Observation chain with up to 8 iterations |
| 💬 **Session Memory** | Per-user conversation history with sliding window |
| 🔎 **Reasoning Viewer** | Frontend shows every tool call and result — full transparency |
| 🐳 **Dockerized** | One command to run the full stack |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│     Chat UI · File Upload · Reasoning Chain Viewer  │
└───────────────────────┬─────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────┐
│                  FastAPI Backend                     │
│          /ask  /upload  /tools  /session            │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│               ReAct Agent (LangChain)                │
│                                                     │
│   Thought → Action → Observation → ... → Answer     │
│                                                     │
│   ┌──────────┐  ┌─────────┐  ┌──────────────────┐  │
│   │web_search│  │ weather │  │      news        │  │
│   └──────────┘  └─────────┘  └──────────────────┘  │
│   ┌──────────────────┐  ┌──────────────────────┐   │
│   │  execute_python  │  │  summarize_document  │   │
│   └──────────────────┘  └──────────────────────┘   │
│                                                     │
│         Gemini 1.5 Pro · ConversationMemory         │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

**Backend**
- `LangChain` — ReAct agent orchestration and tool management
- `Google Gemini 1.5 Pro` — reasoning and generation backbone
- `FastAPI` — REST API with async support
- `DuckDuckGo Search` — free, no-key-required web search
- `RestrictedPython` — sandboxed code execution (blocks file I/O, network, os)
- `httpx` — async HTTP for weather and news APIs

**Frontend**
- `React 18` + `TypeScript`
- `TailwindCSS` — styling
- Collapsible reasoning chain per message

**DevOps**
- `Docker` + `Docker Compose`
- `GitHub Actions` — CI/CD

---

## 📁 Project Structure

```
llm-agent/
├── backend/
│   ├── app/
│   │   ├── core/config.py          # Pydantic settings
│   │   ├── tools/
│   │   │   ├── web_search.py       # DuckDuckGo tool
│   │   │   ├── api_tools.py        # Weather + News tools
│   │   │   ├── code_executor.py    # Sandboxed Python runner
│   │   │   └── doc_summarizer.py   # PDF/DOCX summarizer
│   │   ├── agent/react_agent.py    # ReAct loop + memory
│   │   └── main.py                 # FastAPI routes
│   └── tests/test_agent.py
├── frontend/src/App.tsx            # Chat UI + reasoning viewer
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Cloud API key with Gemini access
- Docker (recommended)

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/llm-agent.git
cd llm-agent
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
# Optionally add OPENWEATHER_API_KEY and NEWS_API_KEY
```

### 2. Run with Docker

```bash
docker-compose up --build
```

Frontend → `http://localhost:3000`  
API Docs → `http://localhost:8000/docs`

### 3. Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev
```

---

## 🔑 API Keys

| Key | Required | Free Tier | Get It |
|-----|----------|-----------|--------|
| `GOOGLE_API_KEY` | ✅ Yes | Yes (Gemini) | [aistudio.google.com](https://aistudio.google.com) |
| `OPENWEATHER_API_KEY` | ❌ Optional | Yes (1000 calls/day) | [openweathermap.org](https://openweathermap.org/api) |
| `NEWS_API_KEY` | ❌ Optional | Yes (100 calls/day) | [newsapi.org](https://newsapi.org) |

> Web search works out of the box with no API key via DuckDuckGo.

---

## 💬 Example Interactions

**Multi-tool reasoning:**
> User: "What's the weather in Tokyo and any recent news about it?"

```
Thought: I need weather data and news for Tokyo — two separate tools.
Action: get_weather("Tokyo")
Observation: 28°C, Partly Cloudy, Humidity: 72%
Action: get_news("Tokyo")
Observation: [5 headlines about Tokyo]
Final Answer: It's currently 28°C and partly cloudy in Tokyo...
```

**Code execution:**
> User: "Calculate the monthly EMI for a ₹50 lakh home loan at 8.5% for 20 years"

```
Action: execute_python("""
  P, r, n = 5000000, 8.5/12/100, 240
  emi = P * r * (1+r)**n / ((1+r)**n - 1)
  print(f'Monthly EMI: ₹{emi:,.0f}')
""")
Observation: Monthly EMI: ₹43,391
```

---

## 🗺️ Roadmap

- [x] ReAct agent with 5 tools
- [x] Sandboxed code execution
- [x] Per-session conversation memory
- [x] Reasoning chain viewer in UI
- [x] Docker + CI/CD
- [ ] Streaming responses (SSE)
- [ ] Tool usage analytics dashboard
- [ ] Custom tool plugin system
- [ ] Voice input support

---

## 🤝 Contributing

PRs welcome! Open an issue first for major changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📬 Contact

Built by [Your Name](https://linkedin.com/in/yourprofile) · [your.email@gmail.com](mailto:your.email@gmail.com)
