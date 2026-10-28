Time spent: 128 minutes

# Pax Distribution — AI Customer Review Triage Automation

An automated AI pipeline that ingests, deduplicates, classifies, and alerts on customer reviews using Python, Google Gemini, and Resend.

## 1. Tools & AI Model Selection
- **Language & Runtime**: Python was selected over low-code tools (like n8n) to ensure precise data cleaning, item isolation, modular testing, and custom error recovery.
- **AI Model**: **Google Gemini 2.5 Flash** was chosen for its low latency, high cost-efficiency (~$0.075 / 1M tokens), strong multilingual capabilities, and native Pydantic structured output.
- **Validation**: **Pydantic** validates the model's responses against the expected schema and allowed classification values using strict Enums (`Sentiment`, `Category`, `Urgency`).
- **Notifications**: **Resend API** handles instant critical safety alerts and end-of-run summaries with CSV attachments.

## 2. How to Run
1. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. **Environment Setup**: Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY` and `RESEND_API_KEY`. (An example key structure is provided in `.env.example`).
   > *Note: You can sign up and generate a free API key at [resend.com](https://resend.com).*
3. **Execute Pipeline**:
   - **Default (Sample CSV)**: `python -m src.main`
   - **Custom Local CSV**: `python -m src.main path/to/reviews.csv`
   - **Google Sheets URL**: `python -m src.main "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"`
4. **Run Unit Tests**: `python -m pytest`

## 3. Edge Case Handling
- **Duplicates**: Filtered automatically using `Review ID` before calling the AI. Only the first review with a given ID is processed, and any repeated duplicates are skipped.
- **Empty Reviews**: Filtered during pre-processing; marked `Needs Manual Review` without wasting LLM tokens.
- **Non-English Reviews**: Prompt engineering and system instructions guide Gemini to translate foreign language reviews (e.g. Spanish `R-1008`) into a concise 1-sentence English summary.
- **Star Rating Mismatches**: Gemini classifies based on written review facts rather than star ratings. Product safety hazards (e.g., smoking kettle in `R-1002`, snapped poles in `R-1009`) override ratings and trigger `Critical` urgency.
- **Prompt Injection Defense**: System prompts isolate review text as untrusted data, neutralizing embedded instructions attempting to manipulate output (e.g., `R-1009`).

## 4. Assumptions
- Duplicate Resolution: When multiple rows share the same Review ID, I assumed the first occurrence is authoritative and retained it while skipping subsequent occurrences.
- Single Classification per Review: When a review mentions multiple issues, I assign one primary category based on the most significant issue, prioritizing safety concerns where applicable.
- Execution Model: I designed the solution as a command-line batch workflow because the assessment focuses on processing a supplied dataset rather than providing a user interface or continuous monitoring.

## 5. Scaling to 500 Daily Reviews (Production Roadmap & Cost Breakdown)

### A. Reliability, State & Failure Recovery
- **Persistent Database Deduplication**: Store processed Review IDs in a database to prevent reprocessing across runs.
- **Automated Retry & Rate Limiting**: Wrap Gemini and Resend API calls with exponential backoff retries to handle transient network drops or API rate limits gracefully without aborting the batch run.
- **Notification Idempotency**: Persist notification status and use idempotency controls where supported to reduce duplicate alerts and improve recovery.

### B. Speed & Concurrency
- **Asynchronous Parallel Execution**: Transition from sequential processing to async or task queues. Evaluate controlled parallel processing if throughput requirements justify it. Limit concurrency according to the model provider's rate limits and the notification service's constraints.

### C. AI Infrastructure Strategy: Managed API vs. Self-Hosted Open-Weight Models

#### 1. Managed API (`Google Gemini 2.5 Flash` — Primary Recommendation)
- **Cost-Efficiency**: Extremely low cost per request (~$0.015/day for 500 reviews), keeping operational overhead near zero.
- **Key Benefits**: Zero server maintenance, 99.9% uptime SLA, fast response times, and native Pydantic JSON schema support out-of-the-box.

#### 2. Self-Hosted Open-Weight Models (e.g. `Gemma 2 9B` / `Llama 3.1 8B` — Strategic Alternative)
- **Concept**: Fine-tuning a smaller, specialized open-weight model (such as Gemma or Llama) specifically on Pax Distribution review triage datasets, served via vLLM or Ollama.
- **Key Advantages**:
  - **Data Privacy & Compliance**: Keeps all customer review data completely in-house without transmitting content to external cloud APIs.
  - **Custom Fine-Tuning Accuracy**: Allows training the model on company-specific product terminology, custom defect categories, and internal brand guidelines.
  - **Predictable Cost Scaling**: Provides a scalable long-term solution as daily processing volume expands to tens of thousands of reviews.
