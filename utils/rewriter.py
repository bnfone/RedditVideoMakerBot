# utils/rewriter.py  ──  2025-05-03
"""
• Sends ONE OpenAI-Chat request in strict JSON-mode
• Expects:  { hook: "...", body: "...", caption: "..." }
• Stores the raw JSON in assets/temp/<reddit_id>/rewriter.json
• Adds ai_caption to reddit_obj   (for later videos.json)
"""
from __future__ import annotations
import json, os, re, requests
from pathlib import Path
from utils import settings
from utils.posttextparser import posttextparser

def rewrite_reddit(reddit_obj: dict) -> dict:
    cfg = settings.config["settings"]["rewriter"]
    if not (cfg["enabled"] and settings.config["settings"]["storymode"]):
        return reddit_obj                                           # bypass

    # ───────────────────────────────────────────────────  OpenAI settings
    endpoint      = cfg["api_endpoint"].rstrip("/")
    headers = {
        "Authorization": f"Bearer {cfg['api_token']}",
        "Content-Type":  "application/json",
    }
    model         = cfg["model"]
    prompt_tpl    = cfg["prompt"]
    target_group  = cfg["target_group"]
    want_caption  = cfg.get("generate_caption", True)               # new flag

    # ───────────────────────────────────────────────────  helpers
    def reddit_id() -> str:
        return re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])

    def _call_openai(full_text: str) -> dict:
        user_prompt = (
            "Return STRICTLY a JSON object with **exactly** three keys:\n"
            " - hook   : catchy TikTok/Short title, ≤ 90 chars, no spoiler\n"
            " - body   : rewritten story (~1 min read-aloud, 2nd-person, CTA, no emojis)\n"
            " - caption: (optional) 1-2 sentence Instagram/YT description + 3-5 hashtags, ≤ 150 chars\n\n"
            f"Target group: {target_group}\n"
            "Don't add extra keys, arrays or markdown.\n\n"
            f"Additional Info:\n{prompt_tpl}\n"
            "----- ORIGINAL STORY -----\n"
            f"{full_text}"
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a social-media copywriter."},
                {"role": "user",   "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},             # ← JSON-mode!
            "temperature": 0.7,
            "top_p": 0.9,
        }

        r = requests.post(f"{endpoint}/chat/completions", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]         # already pure JSON

    # ───────────────────────────────────────────────────  workflow
    full_story = " ".join(reddit_obj["thread_post"]) \
        if settings.config["settings"]["storymodemethod"] == 1 else reddit_obj["thread_post"]

    print("⟳ Rewriter: requesting OpenAI JSON …")
    raw_json = _call_openai(full_story)

    # save raw response for debugging / reuse
    temp_dir = Path(f"assets/temp/{reddit_id()}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "rewriter.json").write_text(raw_json, encoding="utf-8")

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        print("⚠ Rewriter: invalid JSON – falling back to original text.")
        return reddit_obj

    reddit_obj["thread_title"] = data.get("hook", reddit_obj["thread_title"])

    body = data.get("body", full_story)
    reddit_obj["thread_post"] = (
        posttextparser(body) if isinstance(body, str) else body
    )

    reddit_obj["ai_caption"] = data.get("caption", "") if want_caption else ""

    return reddit_obj
