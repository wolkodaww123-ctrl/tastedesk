"""Minimal Qloo hackathon API client (stdlib only) with private on-disk cache."""
import hashlib, json, os, urllib.parse, urllib.request

BASE = os.environ.get("QLOO_BASE_URL", "https://hackathon.api.qloo.com")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")


def _key():
    k = os.environ.get("QLOO_API_KEY")
    if not k and os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
        for line in open(os.path.join(os.path.dirname(__file__), ".env")):
            if line.startswith("QLOO_API_KEY="):
                k = line.strip().split("=", 1)[1]
    if not k:
        raise RuntimeError("Set QLOO_API_KEY (see README)")
    return k


def get(path, params):
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    url = f"{BASE}{path}?{qs}"
    h = hashlib.sha1(url.encode()).hexdigest()
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = os.path.join(CACHE_DIR, h + ".json")
    if os.path.exists(cp):
        return json.load(open(cp))
    req = urllib.request.Request(url, headers={"X-Api-Key": _key(), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
    except Exception as e:  # keep the agent alive on API errors
        return {"error": str(e)}
    json.dump(data, open(cp, "w"))
    return data


def search(query, etype=None, take=3):
    d = get("/search", {"query": query, "types": etype, "take": take})
    return d.get("results", []) if isinstance(d.get("results"), list) else []


def tags(query, take=5):
    d = get("/v2/tags", {"filter.query": query, "take": take})
    return d.get("results", {}).get("tags", []) if isinstance(d.get("results"), dict) else []


def insights(ftype, take=6, **params):
    p = {"filter.type": ftype, "take": take}
    p.update({k.replace("__", "."): v for k, v in params.items()})
    d = get("/v2/insights", p)
    return d.get("results", {}).get("entities", []) if isinstance(d.get("results"), dict) else []
