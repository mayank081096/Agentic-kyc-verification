
# 🏦 Agentic KYC Platform

> An AI-powered, multi-agent Corporate KYC (Know Your Customer) verification pipeline built with **Claude AI**, **LangGraph**, and **FastAPI** — automated end-to-end via **GitHub Actions CI/CD**.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agents](#agents)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the Pipeline](#running-the-pipeline)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Environment Variables](#environment-variables)
- [Sample Output](#sample-output)
- [Contributing](#contributing)

---

## Overview

Traditional KYC processes are slow, manual, and error-prone. This platform automates corporate KYC verification using a chain of specialized AI agents that handle document extraction, verification, and risk scoring — delivering a final compliance decision in seconds.

**Key capabilities:**
- 📄 Reads and extracts data from uploaded KYC documents (PDFs, images) using Claude Vision
- ✅ Validates completeness, consistency, and document authenticity
- ⚖️ Scores risk across jurisdiction, PEP exposure, sanctions, and ownership complexity
- 🔀 Conditional routing — failed verifications are rejected before risk scoring
- 📋 Produces a structured JSON report with a final compliance decision

---

## Architecture

```
INPUT (Company + Docs)
        │
        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    AGENT 1      │────▶│    AGENT 2        │────▶│    AGENT 3      │
│ Doc Extractor   │     │  Verification     │     │  Risk Scoring   │
│                 │     │                   │     │                 │
│ • Base64 encode │     │ • Completeness    │     │ • Jurisdiction  │
│ • Claude Vision │     │ • Consistency     │     │ • PEP exposure  │
│ • Field extract │     │ • Doc validity    │     │ • Sanctions     │
│ • Confidence    │     │ • PASS/FAIL/REVIEW│     │ • Ownership     │
└─────────────────┘     └────────┬──────────┘     └────────┬────────┘
                                 │                          │
                          ┌──────▼──────┐                  ▼
                          │   GATEWAY   │          ┌───────────────┐
                          │  FAIL → ❌  │          │    OUTPUT     │
                          │  PASS → ✅  │          │  JSON Report  │
                          └─────────────┘          │  API Response │
                                                    │  Audit Trail  │
                                                    └───────────────┘
```

**Risk Tier Bands:**
| Score | Tier | Action |
|-------|------|--------|
| 0–25 | 🟢 LOW | APPROVE |
| 26–50 | 🟡 MEDIUM | APPROVE WITH EDD |
| 51–75 | 🔴 HIGH | ESCALATE |
| 76–100 | 🚨 CRITICAL | REJECT |

---

## Agents

### Agent 1 — Document Extractor
- Accepts JPG, PNG, and PDF documents
- Base64-encodes files and passes them to Claude Vision API
- Extracts: company name, registration number, directors, shareholders, expiry, issuing authority
- Returns a confidence score: `high | medium | low`

### Agent 2 — Verification Agent
- Checks completeness (score 0–100) against required KYC fields
- Cross-validates field consistency (dates, nationality, address logic)
- Flags expired or suspicious documents
- Routes to **risk scoring** (PASS/REQUIRES_REVIEW) or **reject** (FAIL)

### Agent 3 — Risk Scoring Agent
- Jurisdiction risk via FATF grey/black list assessment
- PEP (Politically Exposed Person) proximity check
- Sanctions screening against OFAC, UN, EU, UK HMT lists
- Ownership complexity scoring
- Outputs an overall risk score (0–100) and final decision

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Anthropic Claude (claude-sonnet-4-20250514) |
| Agent Orchestration | LangGraph |
| API Framework | FastAPI |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Language | Python 3.11 |

---

## Project Structure

```
Agentic-kyc-platform/
├── agents/
│   ├── agent1_document_extractor.py
│   ├── agent2_verification.py
│   └── agent3_risk_scoring.py
├── workflows/
│   └── kyc_pipeline.py
├── tests/
│   └── test_agents.py
├── .github/
│   └── workflows/
│       └── kyc_pipeline.yml
├── app.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker (optional)
- Anthropic API key → [Get one here](https://console.anthropic.com/)

### 1. Clone the repo

```bash
git clone https://github.com/mayank081096/Agentic-kyc-platform.git
cd Agentic-kyc-platform
git checkout Feature
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## Running the Pipeline

### Run all 3 agents locally

```bash
python workflows/kyc_pipeline.py
```

### Run individual agents

```bash
python agents/agent1_document_extractor.py
python agents/agent2_verification.py
python agents/agent3_risk_scoring.py
```

### Run with Docker

```bash
docker build -t agentic-kyc-platform .
docker run --rm -e ANTHROPIC_API_KEY=your_key_here agentic-kyc-platform
```

---

## GitHub Actions CI/CD

Every push to `main` or `Feature` branch automatically triggers a 3-job pipeline:

| Job | What it does |
|-----|-------------|
| **Lint & Test** | Runs flake8 linting + pytest unit tests |
| **Build** | Builds Docker image and runs a smoke test |
| **Run Pipeline** | Executes all 3 agents sequentially with sample data |

### Setting up the secret

1. Go to your repo → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY` | Value: your Anthropic API key

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Yes |

Create a `.env.example` file:

```
ANTHROPIC_API_KEY=your_key_here
```

> ⚠️ Never commit your actual `.env` file. Add it to `.gitignore`.

---

## Sample Output

```json
{
  "company": "Acme Technologies Ltd",
  "decision": "APPROVE_WITH_EDD",
  "risk_tier": "MEDIUM",
  "risk_score": 42,
  "verification": "PASS",
  "agent1_ok": true,
  "agent2_ok": true,
  "agent3_ok": true
}
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request against `main`

---

> Built with ❤️ using [Anthropic Claude](https://anthropic.com) · [LangGraph](https://langchain-ai.github.io/langgraph/) · [FastAPI](https://fastapi.tiangolo.com/)
