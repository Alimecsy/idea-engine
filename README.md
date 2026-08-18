# Idea Engine

Voice-first personal idea capture and intelligence pipeline.

## V1 flow

Telegram voice note → Groq Whisper transcription → Groq metadata enrichment → Notion Idea Reservoir → Telegram confirmation.

The raw transcript is canonical. Enrichment creates searchable metadata but is not allowed to block persistence.

## Stack

- FastAPI webhook service
- Telegram Bot API
- Groq `whisper-large-v3-turbo`
- Groq `openai/gpt-oss-20b` with strict structured output
- Notion API
- Railway deployment

## Notion schema

The target Idea Reservoir data source expects:

- `Idea` — title
- `Description` — rich text
- `Key Insight` — rich text
- `Summary` — rich text
- `Themes` — multi-select
- `Captured` — date
- `Source` — select including `Telegram Voice`
- `Status` — select including `Inbox`

The raw transcript is stored in the page body.

## Environment

Copy `.env.example` to `.env` locally or configure the same variables in Railway.

```bash
cp .env.example .env
```

Never commit secrets.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Telegram webhook

After deployment, configure Telegram to send updates to:

```text
https://<railway-domain>/telegram/webhook
```

Use the same secret configured in `TELEGRAM_WEBHOOK_SECRET` as Telegram's webhook `secret_token`.

## V1 boundaries

See `AGENTS.md`. Do not add queues, databases, vector stores, dashboards, scoring, or autonomous intelligence to V1 without a demonstrated requirement.
