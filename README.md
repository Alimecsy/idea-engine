# Idea Engine

Voice-first personal idea capture and intelligence pipeline.

**Idea Engine V1** — production live.

## V1 flow

```
Telegram voice note
→ Railway webhook
→ Groq Whisper transcription
→ Groq metadata enrichment
→ Notion Idea Reservoir
→ Telegram confirmation
```

The raw transcript is canonical. Enrichment creates searchable metadata but is not allowed to block persistence.

## Architecture

- **Capture**: Telegram voice note → `POST /telegram/webhook`
- **Transcription**: Groq `whisper-large-v3-turbo` (Telegram `.oga` files normalized to `.ogg`)
- **Enrichment**: Groq `openai/gpt-oss-20b` with strict JSON-schema structured output (title, description, key_insight, summary, themes)
- **Persistence**: Notion Idea Reservoir data source — metadata as properties, raw transcript in the page body
- **Confirmation**: Telegram reply with title and page URL, sent only after Notion persistence succeeds
- **Fallback**: if enrichment fails, minimal metadata is used; the raw transcript is still persisted

Raw transcript is the canonical, untouched record. Only the configured Telegram user may create captures.

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /telegram/webhook` — Telegram update receiver; requires `X-Telegram-Bot-Api-Secret-Token` matching `TELEGRAM_WEBHOOK_SECRET`

## Environment variables

Required (names only, set values in `.secrets` locally or in Railway):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `TELEGRAM_WEBHOOK_SECRET`
- `GROQ_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATA_SOURCE_ID`

Optional:

- `WHISPER_MODEL` (default `whisper-large-v3-turbo`)
- `METADATA_MODEL` (default `openai/gpt-oss-20b`)
- `NOTION_VERSION` (default `2026-03-11`)

Never commit secrets. `.secrets` is git-ignored; `.secrets.example` documents the required names.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .secrets.example .secrets   # fill in real values
uvicorn app.main:app --reload
```

Config loads from `.env` then `.secrets`; environment variables supplied by Railway/system take precedence.

Health check:

```bash
curl http://localhost:8000/health
```

## Railway deployment

- `Procfile` start command: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Set the required environment variables in the Railway service (no `.secrets` needed in production)
- Railway provides the public HTTPS domain; Telegram webhook is registered to `https://<railway-domain>/telegram/webhook` with `secret_token` = `TELEGRAM_WEBHOOK_SECRET`

## Notion schema

The Idea Reservoir data source expects: `Idea` (title), `Description`, `Key Insight`, `Summary`, `Themes` (multi-select), `Captured` (date), `Source` (select, includes `Telegram Voice`), `Status` (select, includes `Inbox`).

## V1 boundaries

See `AGENTS.md`. V1 excludes queues, databases, vector stores, dashboards, scoring, autonomous intelligence, and additional capture channels.