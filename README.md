# WaiverPro AI Compliance Agent

An autonomous, determinisitic AI orchestration pipeline designed to evaluate dynamic UI/UX and functional compliance for the WaiverPro web application. 

This agent uses Playwright to scrape complex authenticated React states, builds a localized spatial-semantic vector database, and leverages Gemini 2.5 Flash to evaluate 19 strict compliance rules, ultimately generating a comprehensive Markdown report with bounding-box visual evidence of UI violations.

---

## 🧠 Architectural Decisions & Tool Selection Justification

To satisfy the stringent requirements of dynamic content handling, resilience, and deterministic reasoning, the following architectural decisions were made:

* **Playwright over Selenium/Puppeteer:** Chosen for its native auto-waiting capabilities and `networkidle` state detection. WaiverPro is a dynamic React Single Page Application (SPA); traditional scrapers capture blank screens because they fail to wait for asynchronous API calls to populate the DOM. Playwright ensures full React hydration before extraction.
* **Supabase (pgvector) over In-Memory DBs:** To solve LLM context window starvation, the visual DOM is mathematically flattened into semantic strings and embedded using `all-MiniLM-L6-v2`. Supabase handles cosine similarity searches, ensuring the AI agent only reads the UI components directly relevant to the specific rule being tested (e.g., retrieving only `[PAGE: action_items]` chunks for Rule 14).
* **Gemini 2.5 Flash over GPT-4o:** Chosen for its massive 1M+ token context window and strict adherence to `pydantic` JSON schemas (`temperature=0.0`). This guarantees deterministic output formatting and prevents the LLM from hallucinating reasoning steps or breaking the pipeline downstream.
* **Exponential Backoff:** The compliance agent features a custom retry loop targeting HTTP 503/429 errors to survive free-tier API rate limits without crashing the master orchestrator.

---

## ⚙️ System Pipeline Flow

1. **Multi-Route Visual Extraction:** Playwright navigates 8 distinct application states (Landing, Login, Dashboard, User Management, Settings, Facilities, Action Items, and dynamic Modals), extracting both full-page screenshots and deep DOM nodes with precise `x, y, width, height` spatial coordinates.
2. **Semantic Flattening:** DOM trees are translated into localized semantic strings embedding the element's path, attributes, and screen location.
3. **Vector Ingestion:** The strings are tokenized via `SentenceTransformer` and bulk-inserted into a remote Supabase pgvector table.
4. **Deterministic Evaluation:** The `orchestrator.py` loops through the 19 canonical rules. It routes the rule to the correct page context, pulls the top 30 most relevant vector chunks, and prompts the Gemini agent to make a boolean compliance decision.
5. **Evidence Generation:** If a UI element violates a rule, the agent extracts the element's spatial coordinates and uses Pillow to draw a red bounding box on the original screenshot, saving it as verifiable evidence.

---

## 🚀 Setup Guide

### 1. Prerequisites
* Python 3.10+
* A Supabase project with `pgvector` enabled.
* A Google AI Studio API key (Gemini).

### 2. Installation
Clone the repository and install the required dependencies:
```
git clone [https://github.com/anandhupl/waiverpro-agent.git](https://github.com/anandhupl/waiverpro-agent.git)
cd waiverpro-agent
pip install -r requirements.txt
playwright install chromium

```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```
SUPABASE_URL="your_supabase_project_url"
SUPABASE_KEY="your_supabase_service_role_key"
GEMINI_API_KEY="your_gemini_api_key"

```

### 4. Database Setup

Execute the following SQL in your Supabase SQL Editor to prepare the vector table:

```
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE waiverpro_dom_elements (
    id BIGSERIAL PRIMARY KEY,
    chunk_index INT,
    content TEXT,
    embedding VECTOR(384)
);

```

---

## 🎯 Master Execution Sequence

To run the full 19-rule compliance loop from scratch, execute these commands sequentially:

**1. Secure Visual & DOM Evidence (100% Coverage):**

```
python extractors/capture_auth.py

```

**2. Flatten & Embed Data:**

```
python backend/semantic_embed.py

```

**3. Push Vectors to Supabase:**

```
python backend/inject_supabase.py

```

**4. Fire the Master Orchestrator:**

```
python backend/orchestrator.py

```

*The final report will be generated at `data/final_compliance_report.md` alongside bounding-box images in `data/screenshots/`.*

---

## 📂 Repository Structure

```
waiverpro-agent/
├── backend/
│   ├── compliance_agent.py    # Gemini API logic, structured output, bounding boxes
│   ├── extract_rules.py       # Setup script to parse canonical rules
│   ├── inject_supabase.py     # Bulk pgvector ingestion
│   ├── orchestrator.py        # Master loop, routing, and Markdown generation
│   └── semantic_embed.py      # DOM flattening and MiniLM-L6 vectorization
├── data/
│   ├── dom/                   # Raw JSON outputs from Playwright (action_items, dashboard, etc.)
│   ├── screenshots/           # Full-page captures and generated violation evidence
│   └── extracted_rules.json   # The canonical evaluation rules payload
├── extractors/
│   └── capture_auth.py        # Playwright networkidle scraper (8 routes + Modals)
├── README.md
└── requirements.txt
```