"""Canonical model keys so the same model matches across leaderboards.

No-rollup policy: normalization only handles casing, punctuation, and
vendor naming -- every distinct variant stays its own row (e.g. "GPT-5",
"GPT-5 (high)" and "GPT-5 (low)" are three separate models). Parenthetical
content is kept as part of the key so reasoning-effort variants don't merge.
"""
import re

PAREN_OPEN = re.compile(r"\s*\(\s*")
PAREN_CLOSE = re.compile(r"\s*\)\s*")

# explicit raw-name -> canonical key overrides (checked after generic cleanup)
ALIASES = {
    # OpenAI
    "gpt5": "gpt-5", "gpt-5": "gpt-5",
    "gpt55": "gpt-5.5", "gpt-5.5": "gpt-5.5",
    "gpt55pro": "gpt-5.5-pro",
    "gpt54pro": "gpt-5.4-pro",
    "gpt6astra": "gpt-6-astra",
    # Anthropic
    "claudeopus46": "claude-opus-4.6", "claudeopus4.6": "claude-opus-4.6",
    "claudeopus47": "claude-opus-4.7",
    "claudeopus48": "claude-opus-4.8",
    "claudeopus5": "claude-opus-5",
    "claudefable5": "claude-fable-5", "claudefable51": "claude-fable-5.1",
    "fable5": "claude-fable-5", "fable51": "claude-fable-5.1",
    "opus5": "claude-opus-5",
    # Google
    "gemini3pro": "gemini-3-pro",
    "gemini37flash": "gemini-3.7-flash", "gemini38flash": "gemini-3.8-flash",
    "gemini3flash": "gemini-3-flash",
    # xAI
    "grok420": "grok-4.20", "grok4": "grok-4",
    # Meta
    "musespark12": "muse-spark-1.2",
    # others
    "kimi k3": "kimi-k3", "kimik3": "kimi-k3",
    "qwen38max": "qwen-3.8-max",
    "deepseekv4": "deepseek-v4",
}

DISPLAY = {
    "gpt-5": "GPT-5", "gpt-5.5": "GPT-5.5", "gpt-5.5-pro": "GPT-5.5 Pro",
    "gpt-5.4-pro": "GPT-5.4 Pro", "gpt-6-astra": "GPT-6 Astra",
    "claude-opus-4.6": "Claude Opus 4.6", "claude-opus-4.7": "Claude Opus 4.7",
    "claude-opus-4.8": "Claude Opus 4.8", "claude-opus-5": "Claude Opus 5",
    "claude-fable-5": "Claude Fable 5", "claude-fable-5.1": "Claude Fable 5.1",
    "gemini-3-pro": "Gemini 3 Pro", "gemini-3-flash": "Gemini 3 Flash",
    "gemini-3.7-flash": "Gemini 3.7 Flash", "gemini-3.8-flash": "Gemini 3.8 Flash",
    "grok-4": "Grok 4", "grok-4.20": "Grok 4.20",
    "muse-spark-1.2": "Muse Spark 1.2", "kimi-k3": "Kimi K3",
    "qwen38": "Qwen 3.8 Max", "qwen37": "Qwen 3.7 Max",
    "gpt54": "GPT-5.4", "gpt56sol": "GPT-5.6 Sol", "gpt56terra": "GPT-5.6 Terra",
    "glm53": "GLM 5.3", "glm52": "GLM 5.2", "glm51": "GLM 5.1",
    "glm53flash": "GLM 5.3 Flash",
    "gemini31propreview": "Gemini 3.1 Pro Preview",
    "gemini35flash": "Gemini 3.5 Flash", "gemini36flash": "Gemini 3.6 Flash",
    "musespark11": "Muse Spark 1.1", "musespark": "Muse Spark",
    "claudesonnet5": "Claude Sonnet 5", "claudesonnet46": "Claude Sonnet 4.6",
    "o3pro": "o3 Pro", "grok45": "Grok 4.5",
    "kimik26": "Kimi K2.6", "kimik27code": "Kimi K2.7 Code",
    "deepseekv4pro": "DeepSeek V4 Pro",
    "qwen-3.8-max": "Qwen 3.8 Max", "deepseek-v4": "DeepSeek V4",
}

ORG = {
    "gpt": "OpenAI",
    "claude": "Anthropic",
    "gemini": "Google",
    "grok": "xAI",
    "muse-spark": "Meta",
    "kimi": "Moonshot AI",
    "qwen": "Alibaba",
    "deepseek": "DeepSeek",
    "llama": "Meta",
    "mistral": "Mistral",
}

def _flatten_parens(n: str) -> str:
    """Turn '(...)' into plain words so variant info survives in the key."""
    n = PAREN_OPEN.sub(" ", n)
    n = PAREN_CLOSE.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()

def canonical(raw: str) -> str:
    n = _flatten_parens(raw.strip().lower())
    key = re.sub(r"[^a-z0-9]", "", n)
    if key in ALIASES:
        return ALIASES[key]
    # reinsert readability: try dotted version match
    dotted = re.sub(r"[^a-z0-9.]", "", n)
    if dotted in ALIASES:
        return ALIASES[dotted]
    return key

def _prettify(raw: str) -> str:
    n = _flatten_parens(raw).strip()
    n = re.sub(r"[-_]+", " ", n)
    n = re.sub(r"\s+", " ", n)
    words = []
    for w in n.split(" "):
        if w.lower() in ("gpt", "o1", "o3"):
            words.append(w.upper())
        elif re.fullmatch(r"[a-z]+\d[\d.]*", w.lower()):
            words.append(w[0].upper() + w[1:])
        else:
            words.append(w[:1].upper() + w[1:] if w else w)
    return " ".join(words)

def display_name(key: str, fallback_raw: str) -> str:
    if key in DISPLAY:
        return DISPLAY[key]
    return _prettify(fallback_raw)

ORG_ALIASES = {
    "zai": "Z.ai", "z.ai": "Z.ai",
    "google deepmind": "Google", "google": "Google",
    "anthropic": "Anthropic", "openai": "OpenAI",
    "meta": "Meta", "xai": "xAI",
    "alibaba": "Alibaba", "moonshot": "Moonshot AI",
    "deepseek": "DeepSeek", "mistral": "Mistral",
}

def org_for(key: str, raw_org) -> str:
    if raw_org:
        o = str(raw_org).strip()
        if o.lower() in ORG_ALIASES:
            return ORG_ALIASES[o.lower()]
        return o
    for prefix, org in ORG.items():
        if key.startswith(prefix):
            return org
    return "Unknown"
