"""TasteDesk agent: a tool-using agent that grounds small-business chat in Qloo taste data.

Two skills:
  * concierge  - a guest tells the bot what they love; the agent resolves those
                 entities in Qloo, picks a cuisine/place tag, and asks Qloo Insights
                 for places near the business that people with that taste love.
  * crowd      - the owner names their business; the agent finds it in Qloo and
                 asks what its audience loves (artists, movies, brands) to build a
                 playlist, event-night ideas and ad hooks.
The planner is rule-based (no paid LLM needed). If OPENAI_BASE_URL/OPENAI_API_KEY
are set (e.g. a free local Ollama), the final answer is rephrased by that LLM, but
all facts still come from Qloo.
"""
import json, os, re, urllib.request
import qloo_client as q

CUISINES = ["italian", "mexican", "japanese", "sushi", "thai", "indian", "vegan", "vegetarian",
            "french", "chinese", "korean", "bbq", "barbecue", "pizza", "burger", "seafood",
            "steakhouse", "mediterranean", "greek", "coffee", "cafe", "bakery", "brunch",
            "cocktail bar", "wine bar", "brewery", "ramen", "tapas", "vietnamese"]
LIKE_RE = re.compile(r"(?:i\s+(?:really\s+)?(?:love|like|enjoy|adore)|fan of|into|favorites? (?:are|is))\s+(.+?)(?:[.!?;]|\s+(?:and\s+)?(?:looking|want|need|where|recommend|suggest|any|for)\b|$)", re.I)
LOC_RE = re.compile(r"\b(?:in|near|around)\s+([A-Z][\w .'-]+?(?:,\s*[A-Z]{2})?)(?=[.!?,]|\s+(?:for|tonight|today|and)\b|$)")


class Trace(list):
    def tool(self, name, args, summary):
        self.append({"tool": name, "args": args, "result": summary})


def _split_likes(text):
    likes = []
    for m in LIKE_RE.finditer(text):
        chunk = re.sub(r"\b(movies?|films?|music|songs?|the band|shows?)\b", "", m.group(1), flags=re.I)
        for part in re.split(r",|\band\b|&|/", chunk):
            part = part.strip(" '\"")
            if 2 < len(part) < 60 and part.lower() not in CUISINES:
                likes.append(part)
    return likes[:5]


def _resolve_entities(likes, trace):
    found = []
    for name in likes:
        res = q.search(name, take=1)
        if res:
            e = res[0]
            found.append({"name": e.get("name"), "id": e.get("entity_id"), "type": (e.get("types") or ["?"])[0]})
        trace.tool("qloo.search", {"query": name}, found[-1]["name"] if res else "no match")
    return found


def _cuisine_tag(text, trace):
    low = text.lower()
    for c in CUISINES:
        if re.search(r"\b" + re.escape(c) + r"\b", low):
            for t in q.tags(c, take=5):
                if t.get("id", "").startswith("urn:tag:genre:place"):
                    trace.tool("qloo.tags", {"query": c}, t["id"])
                    return c, t["id"]
            trace.tool("qloo.tags", {"query": c}, "no place tag")
            return c, None
    return None, None


def _place_card(e):
    p = e.get("properties", {})
    return {"name": e.get("name"), "address": p.get("address"), "rating": p.get("business_rating"),
            "price_level": p.get("price_level"), "website": p.get("website"),
            "affinity": round((e.get("query") or {}).get("affinity", 0), 2),
            "keywords": [k["name"] for k in (p.get("keywords") or [])[:4]]}


def concierge(message, city, trace):
    likes = _split_likes(message)
    m = LOC_RE.search(message)
    city = (m.group(1).strip() if m else None) or city
    ents = _resolve_entities(likes, trace)
    cuisine, tag = _cuisine_tag(message, trace)
    params = {"filter__location__query": city}
    if ents:
        params["signal__interests__entities"] = ",".join(e["id"] for e in ents)
    if tag:
        params["filter__tags"] = tag
    if not ents and not tag:
        return {"reply": "Tell me 1-3 things you love (an artist, a film, a show, a brand) and what you feel like eating - I'll match places to your taste.", "cards": []}
    places = q.insights("urn:entity:place", take=5, **params)
    trace.tool("qloo.insights", {"filter.type": "urn:entity:place", **{k.replace('__', '.'): v for k, v in params.items()}}, f"{len(places)} places")
    cards = [_place_card(p) for p in places]
    because = ", ".join(e["name"] for e in ents) or "your request"
    lines = [f"Because you love {because}" + (f" and want {cuisine}" if cuisine else "") + f", people with your taste in {city} rate these highest:"]
    for i, c in enumerate(cards, 1):
        kw = f" - known for {', '.join(c['keywords'])}" if c["keywords"] else ""
        lines.append(f"{i}. {c['name']} ({c['address'] or city}){kw} - taste match {int(c['affinity']*100)}%")
    if not cards:
        lines.append("Qloo returned no places for that combination - try a nearby bigger city or fewer filters.")
    return {"reply": "\n".join(lines), "cards": cards, "resolved": ents, "city": city}


def crowd(business, city, trace):
    res = q.search(f"{business} {city}".strip(), etype="urn:entity:place", take=1)
    if not res:
        trace.tool("qloo.search", {"query": business, "types": "urn:entity:place"}, "no match")
        return {"reply": f"I couldn't find '{business}' in Qloo. Try the exact name as on Google Maps plus the city.", "cards": []}
    biz = res[0]
    trace.tool("qloo.search", {"query": f"{business} {city}"}, biz["name"])
    out = {"business": biz["name"], "address": biz.get("properties", {}).get("address")}
    for t, label in (("artist", "artists"), ("movie", "movies"), ("brand", "brands"), ("tv_show", "tv_shows")):
        ents = q.insights(f"urn:entity:{t}", take=6, signal__interests__entities=biz["entity_id"])
        out[label] = [e["name"] for e in ents]
        trace.tool("qloo.insights", {"filter.type": f"urn:entity:{t}", "signal.interests.entities": biz["entity_id"]}, ", ".join(out[label][:3]))
    a, mv, b = out["artists"], out["movies"], out["brands"]
    lines = [f"Your crowd at {out['business']} ({out['address']}) - what Qloo says they love:",
             f"- Music: {', '.join(a) or 'n/a'}", f"- Movies: {', '.join(mv) or 'n/a'}",
             f"- TV: {', '.join(out['tv_shows']) or 'n/a'}", f"- Brands: {', '.join(b) or 'n/a'}", "", "Ideas you can use this week:"]
    if a:
        lines.append(f"* In-store playlist seeded with {', '.join(a[:3])}.")
        lines.append(f"* Theme night: '{a[0]} night' with a matching set menu.")
    if mv:
        lines.append(f"* Movie-night or menu special inspired by '{mv[0]}'.")
    if b:
        lines.append(f"* Co-marketing: your guests also love {', '.join(b[:2])} - ideal partners for a giveaway.")
    lines.append("* Feed these tastes into your website chatbot so it talks like your guests.")
    return {"reply": "\n".join(lines), "cards": [], "insights": out}


def _llm_polish(text):
    base, key = os.environ.get("OPENAI_BASE_URL"), os.environ.get("OPENAI_API_KEY", "none")
    if not base:
        return text
    body = json.dumps({"model": os.environ.get("OPENAI_MODEL", "llama3.1"), "messages": [
        {"role": "system", "content": "Rewrite warmly and briefly for a small-business chatbot. Keep every name and fact; add nothing."},
        {"role": "user", "content": text}]}).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(base.rstrip('/') + "/chat/completions", body,
                                   {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}), timeout=30)
        return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception:
        return text


def run(message, mode="concierge", city="Austin, TX", business=""):
    trace = Trace()
    if mode == "crowd":
        out = crowd(business or message, city, trace)
    else:
        out = concierge(message, city, trace)
    out["reply"] = _llm_polish(out["reply"])
    out["trace"] = trace
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(run(" ".join(sys.argv[1:]) or "I love Taylor Swift and Wes Anderson movies, looking for Italian dinner"), indent=2)[:3000])
