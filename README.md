## 🚀 Setup & Execution Guide

To run a full multi-page evaluation cycle, execute the pipeline in this exact sequence. 

**1. Database Reset (Optional but Recommended)**
To prevent semantic cross-contamination between runs, truncate the vector table before injecting new UI states:

```
TRUNCATE TABLE waiverpro_dom_elements;
```

**2. The Multi-Page Extraction Sequence**
Fires Playwright to navigate the authentication flow, wait for network idle states, and capture the spatial DOM/screenshots across all target routes.

```
python extractors/capture_auth.py
```

**3. Vectorization**
Flattens the raw JSON hierarchical DOM into coordinate-aware semantic strings, injecting [PAGE: xxx] tags for isolated retrieval.

```
python backend/semantic_embed.py
```

**4. Supabase Injection**
Pushes the vectorized interface state to the remote PostgreSQL database.

```
python backend/inject_supabase.py
```

**5. Autonomous Evaluation**
Runs the rulebook against the captured UI states. Generates the final Markdown discrepancy report and draws bounding boxes on violation screenshots.

```
python backend/orchestrator.py
```

**⚠️ Known Limitations & Assumptions**
Free-Tier API Constraints & Resilience: The pipeline relies on the Gemini 2.5 Flash free-tier API, which imposes strict 15 RPM (Requests Per Minute) and daily request limits. Consequently, the pipeline is susceptible to 429 Rate Limit and 503 High Demand server spikes. Mitigation: The reasoning core (run_compliance_check) is wrapped in a Tenacity-style exception handler utilizing exponential backoff (15s -> 30s -> 60s) to patiently survive server-side volatility without crashing the audit loop.

Context Starvation in Dense UIs: Data-heavy Single Page Applications (SPAs) like the Dashboard view generate over 100+ semantic chunks. Restricting the RAG retrieval (match_count) too tightly causes the LLM to hallucinate missing UI elements (e.g., status chips) because the vector math prioritizes other elements. Mitigation: The retrieval threshold is intentionally uncapped to match_count: 30 to accommodate high-density DOM environments, leveraging Gemini's large context window.

Explicit Navigation Routing: The Playwright extraction layer is not a recursive autonomous crawler. It relies on explicit programmed routing instructions to hit secondary states (e.g., /dashboard/user-management, Settings modals). Rules targeting unmapped routes will fail deterministically by design.