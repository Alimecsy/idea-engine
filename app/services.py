import json
from dataclasses import dataclass
from datetime import datetime

import httpx
from groq import Groq

from app.config import Settings


@dataclass
class IdeaMetadata:
    title: str
    description: str
    key_insight: str
    summary: str
    themes: list[str]


class GroqService:
    def __init__(self, settings: Settings):
        self.client = Groq(api_key=settings.groq_api_key)
        self.whisper_model = settings.whisper_model
        self.metadata_model = settings.metadata_model

    def transcribe(self, filename: str, audio: bytes) -> str:
        result = self.client.audio.transcriptions.create(
            file=(filename, audio),
            model=self.whisper_model,
            response_format="json",
            temperature=0.0,
        )
        transcript = result.text.strip()
        if not transcript:
            raise ValueError("Groq returned an empty transcript")
        return transcript

    def enrich(self, transcript: str) -> IdeaMetadata:
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "key_insight": {"type": "string"},
                "summary": {"type": "string"},
                "themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 7,
                },
            },
            "required": ["title", "description", "key_insight", "summary", "themes"],
            "additionalProperties": False,
        }
        response = self.client.chat.completions.create(
            model=self.metadata_model,
            reasoning_effort="low",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create retrieval metadata for a personal idea reservoir. Preserve the user's meaning. "
                        "Do not evaluate feasibility, score the idea, recommend actions, or invent facts. "
                        "Title: concise and searchable. Description: one sentence. Key insight: one proposition. "
                        "Summary: 2-4 sentences. Themes: 1-7 short reusable topic labels."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "idea_metadata", "strict": True, "schema": schema},
            },
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return IdeaMetadata(**data)

    @staticmethod
    def fallback_metadata(transcript: str, captured_at: datetime) -> IdeaMetadata:
        preview = " ".join(transcript.split())
        title = f"Voice idea — {captured_at.strftime('%Y-%m-%d %H:%M')}"
        description = preview[:300] if preview else "Voice idea captured without metadata enrichment."
        return IdeaMetadata(
            title=title,
            description=description,
            key_insight=description,
            summary=description,
            themes=["Unclassified"],
        )


class TelegramService:
    def __init__(self, settings: Settings):
        self.token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_url = f"https://api.telegram.org/file/bot{self.token}"

    async def download_voice(self, file_id: str) -> tuple[str, bytes]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/getFile", params={"file_id": file_id})
            response.raise_for_status()
            file_path = response.json()["result"]["file_path"]
            audio = await client.get(f"{self.file_url}/{file_path}")
            audio.raise_for_status()
        return file_path.rsplit("/", 1)[-1], audio.content

    async def send_message(self, chat_id: int, text: str) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            response.raise_for_status()


class NotionService:
    def __init__(self, settings: Settings):
        self.api_key = settings.notion_api_key
        self.data_source_id = settings.notion_data_source_id
        self.notion_version = settings.notion_version

    async def save_idea(self, metadata: IdeaMetadata, transcript: str, captured_at: datetime) -> str:
        payload = {
            "parent": {"type": "data_source_id", "data_source_id": self.data_source_id},
            "properties": {
                "Idea": {"title": [{"text": {"content": metadata.title[:2000]}}]},
                "Description": {"rich_text": [{"text": {"content": metadata.description[:2000]}}]},
                "Key Insight": {"rich_text": [{"text": {"content": metadata.key_insight[:2000]}}]},
                "Summary": {"rich_text": [{"text": {"content": metadata.summary[:2000]}}]},
                "Themes": {"multi_select": [{"name": theme[:100]} for theme in metadata.themes]},
                "Captured": {"date": {"start": captured_at.isoformat()}},
                "Source": {"select": {"name": "Telegram Voice"}},
                "Status": {"select": {"name": "Inbox"}},
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Raw Transcript"}}]},
                },
                *self._paragraph_blocks(transcript),
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["url"]

    @staticmethod
    def _paragraph_blocks(text: str) -> list[dict]:
        chunks = [text[i : i + 1900] for i in range(0, len(text), 1900)] or [""]
        return [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            }
            for chunk in chunks
        ]
