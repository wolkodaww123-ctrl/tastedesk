# Devpost submission text (English; Russian summary at bottom)

Project name: TasteDesk
Tagline (<=200 chars): A taste-aware AI concierge for small businesses: website chat that recommends places and plans events from what guests actually love, powered by Qloo.
Built with: python, qloo, javascript, html, render

## Inspiration
We build websites and AI chatbots for small businesses. Their bots answer politely but generically - they don't know the guest. Qloo's taste graph lets a small cafe or hotel bot reason about real cultural taste.

## What it does
- Guest concierge: a guest shares what they love (artists, films, shows) plus a craving; the agent resolves those entities in Qloo, maps the craving to a Qloo tag and calls Insights for places near the business ranked by taste affinity.
- Know your crowd: the owner enters the business name; the agent finds the venue in Qloo and pulls the audience's music, film, TV and brand affinities, then suggests a playlist, theme nights and co-marketing partners.
- Transparent agent: every tool call (search, tags, insights) with arguments and result is shown under the answer.

## How we built it
Pure-Python (stdlib) agent with three Qloo tools: /search, /v2/tags, /v2/insights on the hackathon API. Rule-based planner, optional LLM (OpenAI-compatible, e.g. local Ollama) only for wording. Private server-side cache; no Qloo data stored in the repo. Web UI is a single HTML page.

## Challenges
Picking valid tag IDs per filter.type (Insights silently ignores invalid params), and keeping answers useful when a city has thin data.

## What's next
Embed widget for client websites, Telegram/WhatsApp versions, menus personalised by taste.

## Testing instructions
Open the demo URL, try "I love Taylor Swift and Wes Anderson movies, looking for Italian dinner" (city Austin, TX), then switch to "Know your crowd" and type "Juniper". No login needed.

---
[RU] TasteDesk - чат-бот для кафе/ресторанов/отелей на базе вкусового графа Qloo: гостю подбирает места по его вкусам, владельцу показывает, что любит его аудитория, и даёт идеи (плейлист, тематические вечера, партнёры).
