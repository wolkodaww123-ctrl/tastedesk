# TasteDesk - taste-aware AI concierge for small businesses

Built by TITANHOLD LLC for the **Qloo Agentic Hackathon** (2026).

Small cafes, restaurants and boutique hotels put chatbots on their websites, but those bots give generic
answers ("try our pasta!"). TasteDesk is an agent that grounds every answer in **Qloo's taste graph**,
so it actually knows what a guest - and a business's crowd - loves.

## Two agent skills
1. **Guest concierge** - a guest writes *"I love Taylor Swift and Wes Anderson movies, looking for Italian dinner"*.
   The agent (a) extracts the tastes, (b) resolves each one with Qloo `/search`, (c) maps the craving to a
   Qloo place tag via `/v2/tags`, (d) calls `/v2/insights` (`filter.type=urn:entity:place`, `filter.location.query`,
   `signal.interests.entities`, `filter.tags`) and returns places ranked by Qloo taste affinity, with what each is known for.
2. **Know your crowd (owner)** - the owner types their business name. The agent finds the venue in Qloo and asks
   Insights what its audience loves across music, film, TV and brands, then turns that into a playlist, theme nights
   and co-marketing partners.

Every agent step (tool + arguments + result) is shown under each answer, so judges can see exactly how Qloo is used.
Without Qloo this app cannot work: the recommendations *are* the taste graph.

## Run locally (no dependencies, Python 3.9+)
```bash
export QLOO_API_KEY=your_hackathon_key      # from the Qloo hackathon form
python3 server.py                           # open http://localhost:8080
python3 agent.py "I love Radiohead, any brunch spot in Austin, TX?"   # CLI
```
Optional: set `OPENAI_BASE_URL` (e.g. a free local Ollama at `http://localhost:11434/v1`) and `OPENAI_MODEL`
to let an LLM rephrase answers. Facts always come from Qloo.

## Deploy (free)
- **Render**: New > Blueprint > this repo (`render.yaml`), set `QLOO_API_KEY`.
- **Hugging Face Spaces**: Docker Space, push this repo, add secret `QLOO_API_KEY` (port 7860).

## Files
- `agent.py` - planner + tools (search, tags, insights), concierge and crowd skills
- `qloo_client.py` - stdlib Qloo client with private server-side cache (`cache/`, git-ignored; no Qloo data in the repo)
- `server.py`, `static/index.html` - web chat demo
- `DEMO_VIDEO_SCRIPT.md`, `DEVPOST_SUBMISSION.md`

## License
MIT - see `LICENSE`.
