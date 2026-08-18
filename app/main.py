import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request

from app.config import get_settings
from app.services import GroqService, NotionService, TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("idea-engine")

settings = get_settings()
groq = GroqService(settings)
telegram = TelegramService(settings)
notion = NotionService(settings)

app = FastAPI(title="Idea Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()
    message = update.get("message") or {}
    sender = message.get("from") or {}

    if sender.get("id") != settings.telegram_allowed_user_id:
        return {"ok": True}

    voice = message.get("voice")
    if not voice:
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id:
            await telegram.send_message(chat_id, "Send me a voice note and I’ll save the idea.")
        return {"ok": True}

    chat_id = message["chat"]["id"]
    file_id = voice["file_id"]
    captured_at = datetime.fromtimestamp(message.get("date", 0), tz=timezone.utc)

    # Acknowledge Telegram immediately; processing continues in-process.
    asyncio.create_task(process_voice(chat_id, file_id, captured_at))
    return {"ok": True}


async def process_voice(chat_id: int, file_id: str, captured_at: datetime) -> None:
    try:
        filename, audio = await telegram.download_voice(file_id)
        transcript = await asyncio.to_thread(groq.transcribe, filename, audio)

        # Metadata enrichment is useful but must never be allowed to destroy the raw capture.
        try:
            metadata = await asyncio.to_thread(groq.enrich, transcript)
        except Exception:
            logger.exception("Metadata enrichment failed; saving fallback metadata")
            metadata = groq.fallback_metadata(transcript, captured_at)

        page_url = await notion.save_idea(metadata, transcript, captured_at)
        await telegram.send_message(chat_id, f"Saved: {metadata.title}\n{page_url}")
    except Exception:
        logger.exception("Voice capture failed")
        await telegram.send_message(chat_id, "Capture failed. The idea was not saved; please resend the voice note.")
