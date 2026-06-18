# WaiverPro AI Compliance Agent

An end-to-end autonomous QA engine designed to ingest compliance PDF manuals, dynamically extract canonical UI rules, scrape live SPA application states, and generate deterministic compliance discrepancy reports with visual overlay evidence.

## 🏗️ Architecture & Pipeline Overview

The system is decoupled into three independent execution layers to ensure resilience and prevent frontend volatility from crashing the reasoning core:
1. **Extraction Layer (Playwright):** Handles multi-page authentication, handles dynamic React single-page application hydration (waiting out skeleton loaders), and captures raw DOM trees along with high-resolution screenshots.
2. **Storage & Retrieval Layer (Supabase + Local Embeddings):** Maps elements into a spatial-semantic vector space utilizing `all-MiniLM-L6-v2`. Rather than feeding raw HTML noise to the LLM, the DOM is flattened into highly structured spatial text strings including coordinate geometry.
3. **Reasoning Layer (Gemini):** A strict dual-model setup. `gemini-3.1-flash-lite` handles high-volume processing of dense document rules, while `gemini-2.5-flash` acts as a deterministic judge via strict Pydantic JSON schemas operating at `temperature=0.0`.

## 🛠️ Tech Stack Justifications (The "Why")

* **Playwright vs. Selenium:** Playwright was chosen due to its built-in auto-waiting mechanisms, superior handling of shadow DOM elements, and robust network idle tracking, which are critical for capturing modern, highly async SPAs without resorting to brittle, hardcoded sleep statements.
* **Spatial-Semantic DOM Encoding:** Instead of feeding walls of raw HTML which dilutes LLM attention mechanisms and increases token costs, the DOM is converted to coordinates-aware semantic fragments. This allows the vector DB to search across both explicit text labels and UI geography simultaneously.
* **Deterministic Structured Output:** By forcing the reasoning model to match an absolute JSON schema, we eliminate hallucinated evaluations and cleanly pass coordinate dimensions straight into Pillow to generate highlighted visual evidence automatically.

## 🚀 Setup & Execution Guide
[Leaving this blank for now — will add the multi-page commands later]

## ⚠️ Known Limitations & Assumptions
[Leaving this blank — will brutally document the scope edges]