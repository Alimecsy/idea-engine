# Idea Engine Build Constitution

## Mission
Preserve spontaneous ideas with near-zero capture friction and make them searchable for later intelligence work.

## V1 contract
Telegram voice note → Groq Whisper transcription → Groq metadata enrichment → Notion Idea Reservoir → Telegram confirmation.

## Non-negotiables
1. Raw transcript is canonical and must be preserved unchanged.
2. Metadata enrichment may fail without blocking persistence; fall back to minimal metadata.
3. Never claim an idea was saved unless Notion persistence succeeded.
4. Only the configured Telegram user may create captures.
5. Verify Telegram webhook secret on every webhook request.
6. Do not add databases, queues, vector stores, agents, dashboards, or frontends in V1 unless a demonstrated requirement demands them.
7. Keep providers behind small service boundaries so Telegram, Groq, or Notion can be replaced later.
8. Secrets live only in environment variables and must never be committed.
9. Prefer idempotent, inspectable behavior over clever abstractions.
10. Every future intelligence layer must read metadata first and open raw transcripts only when needed.

## Canonical metadata
- title
- description
- key_insight
- summary
- themes
- captured_at
- source
- status
- raw_transcript

## Capture invariant
If transcription succeeds, the system should make its best effort to persist the raw transcript even when metadata enrichment fails.

## V1 exclusions
No opportunity scoring, recommendations, semantic embeddings, knowledge graph, scheduled synthesis, or automatic actions.
