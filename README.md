# ⚡ AgentTrace: Production-Grade Agent Observability & Self-Healing Engine
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-Vercel-black?style=for-the-badge&logo=vercel)](https://agent-trace-zeta.vercel.app/)
[![Backend API](https://img.shields.io/badge/Collector%20API-Render-46E3B7?style=for-the-badge&logo=render)](https://agenttrace-api-cdav.onrender.com/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](https://opensource.org/licenses/MIT)

> **Live Production Demo:**
> * 🖥️ **Interactive Web Dashboard:** [https://agent-trace-zeta.vercel.app/](https://agent-trace-zeta.vercel.app/)
> * ⚙️ **FastAPI Swagger Docs:** [https://agenttrace-api-cdav.onrender.com/docs](https://agenttrace-api-cdav.onrender.com/docs)

An end-to-end observability SDK and dashboard for autonomous AI agent pipelines. It monitors multi-step tool calls, visualizes latency bottlenecks, and automatically repairs malformed LLM tool arguments at runtime without crashing workflows.

---

## 🎯 The Problem
LLMs frequently hallucinate tool arguments during multi-step runs:
* Passing strings instead of floats (e.g. `"1200 INR"` instead of `1200.0`)
* Inventing key names (e.g. `"user_identifier"` instead of `"user_id"`)
* Omitting required schema fields

Normally, these cause immediate runtime crashes. AgentTrace catches these failures and auto-repairs them at runtime.

---

## 💡 Architecture & Tech Stack
* **Decorator SDK:** Python, Pydantic (Validates schema before tool run)
* **Self-Healing Layer:** Fast inference via Groq to repair payloads on failure
* **Collector Backend:** FastAPI with SQLite persistence (`traces.db`)
* **Live Dashboard:** Next.js, Tailwind CSS with Payload Diff Inspector

---

## 🚀 How to Run Locally

### 1. Start Backend
```bash
# In project root
python -m uvicorn main:app --reload --port 8000