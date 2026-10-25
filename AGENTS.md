# AGENTS.md: EchoVal AI Multi-Agent Engineering Architecture

## 1. System Overview & Architectural Purpose
EchoVal AI is an autonomous, multi-agent deal valuation and push notification platform engineered to discover, evaluate, and alert users to high-margin e-commerce arbitrage opportunities. The system orchestrates four specialized agents in a unified feedback loop:

1. **Scanner Agent**: Ingests multi-category RSS feeds, parses raw HTML snippets with BeautifulSoup, and applies OpenAI Structured Outputs (JSON Schema via Pydantic) to extract standardized product descriptions and verified prices.
2. **Specialist Agent (Pricer)**: Connects to a remote 4-bit QLoRA fine-tuned model deployed on Modal GPU infrastructure to predict true market values from product descriptions, with local fallback estimation.
3. **Messaging Agent**: Evaluates predicted discounts against dynamic threshold criteria (default $50.00+) and dispatches priority notifications via Pushover push notifications or Twilio SMS.
4. **Planning Agent**: Coordinates pipeline execution, state persistence across runs (`memory.json`), and interactive session triage.

The system features a live Gradio web dashboard providing real-time telemetry, color-coded execution logs, an interactive opportunity table, and on-demand alert triggers.

---

## 2. Agent Responsibilities & Boundaries

### Scanner Agent (`agents/scanner.py`)
- **Ingestion**: Polls DealNews category feeds (Electronics, Computers, Automotive, Smart Home, Home & Garden).
- **Extraction**: Cleans DOM tree structures and strips tracking markup.
- **Filtering**: Filters out items previously evaluated by querying memory history to prevent duplicate API spend.
- **Validation**: Enforces strict schema conformity using OpenAI Structured Outputs (`model="gpt-4o-mini"` with `response_format=DealSelection`). Only products with unambiguous, positive pricing (> $0) are forwarded.

### Specialist Agent (`agents/specialist.py`)
- **Model Infrastructure**: Interfaces with a remote quantized LLM hosted on Modal cloud infrastructure (`pricer-service`).
- **Valuation Logic**: Sends product descriptions to the remote QLoRA model to generate deterministic market price estimates.
- **Resilience**: Implements automatic fallback estimation and graceful error logging to guarantee operational continuity during network latency or container cold starts.

### Messaging Agent (`agents/messaging.py`)
- **Multi-Channel Dispatch**: Supports Pushover push notifications (custom cashregister sound) and Twilio SMS.
- **Credential Safety**: Checks environment variable configurations before network calls. When credentials are unconfigured in development, logs simulated alerts rather than raising fatal runtime exceptions.

### Planning Agent (`agents/planner.py`)
- **Workflow Orchestration**: Directs the scan-evaluate-alert pipeline.
- **Threshold Gating**: Computes `discount = estimated_value - offer_price`. Deals exceeding the defined hurdle ($50+) are flagged and committed to persistent memory.

---

## 3. Engineering Constraints & Standards

### Formatting & Typography Rules (MANDATORY)
- **Strict Ban on Em Dashes and En Dashes**: Never use em dashes (\u2014) or en dashes (\u2013) anywhere in documentation, code comments, commit messages, or user-facing strings.
- **Permitted Separators**: Colons (:), parentheses (()), commas (,), or standard single ASCII hyphens (-) exclusively.

### Security & Credential Hygiene
- Zero secrets committed: `.env` must remain strictly git-ignored.
- All secrets are loaded through `python-dotenv` from local environment variables.
- Repository configuration must provide a fully documented `.env.example` template with sanitized dummy values.

### State & Vector Persistence
- Evaluated opportunities are persisted to `memory.json`.
- Historical runs prevent redundant scraping and API token consumption.
- Cache directories (`__pycache__`, `.ipynb_checkpoints`) must never be tracked by git.
