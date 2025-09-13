# utils/rewriter.py
"""
Configurable AI Rewriter Module
• Sends OpenAI Chat requests in strict JSON mode
• Expects: { hook: "...", body: "...", caption: "..." }
• Stores raw JSON in assets/temp/<reddit_id>/rewriter.json
• Fully configurable prompts and system messages via config
• Supports multiple target groups and use cases
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

    # OpenAI API settings
    endpoint      = cfg["api_endpoint"].rstrip("/")
    headers = {
        "Authorization": f"Bearer {cfg['api_token']}",
        "Content-Type":  "application/json",
    }
    model         = cfg["model"]
    system_prompt = cfg.get("system_prompt", "You are a helpful AI assistant that rewrites content.")
    user_prompt_template = cfg["prompt"]
    target_group  = cfg["target_group"]
    want_caption  = cfg.get("generate_caption", True)

    # ───────────────────────────────────────────────────  helpers
    def reddit_id() -> str:
        return re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])

    def _call_openai(full_text: str) -> dict:
        # Build the user prompt from the template with variable substitution
        json_instructions = (
            "Return STRICTLY a JSON object with **exactly** three keys:\n"
            " - hook   : as described in the prompt below\n"
            " - body   : as described in the prompt below\n"
            " - caption: (optional) 1-2 sentence Instagram/YT description + 3-5 hashtags, ≤ 150 chars\n\n"
            "Don't add extra keys, arrays or markdown.\n\n"
        )
        
        # Replace variables in the user prompt template
        user_prompt = user_prompt_template.format(
            target_group=target_group,
            original_story=full_text,
            json_instructions=json_instructions
        )
        
        # If template doesn't use variables, fall back to old format
        if "{" in user_prompt_template:
            # Template uses variables - already formatted above
            pass
        else:
            # Legacy format - append the story
            user_prompt = f"{json_instructions}Target group: {target_group}\n\n{user_prompt_template}\n\n----- ORIGINAL STORY -----\n{full_text}"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        
        # Handle model-specific parameters
        if model.startswith("gpt-5") and model != "gpt-5-chat-latest":
            # GPT-5 family models use reasoning_effort instead of temperature/top_p
            payload["reasoning_effort"] = cfg.get("reasoning_effort", "medium")
            if "verbosity" in cfg:
                payload["verbosity"] = cfg["verbosity"]
        else:
            # Traditional models (GPT-4o, GPT-3.5, etc.) support temperature/top_p
            payload["temperature"] = 0.4
            payload["top_p"] = 0.7

        # Try the request with retry on timeout
        max_retries = 2
        for attempt in range(max_retries):
            try:
                r = requests.post(f"{endpoint}/chat/completions", headers=headers, json=payload, timeout=120)
                
                # Debug: print detailed error info
                if not r.ok:
                    print(f"⚠ OpenAI API Error {r.status_code}: {r.text}")
                    print(f"⚠ Request payload: {json.dumps(payload, indent=2)}")
                
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]         # already pure JSON
                
            except requests.exceptions.ReadTimeout:
                if attempt < max_retries - 1:
                    print(f"⚠ Request timed out (attempt {attempt + 1}/{max_retries}), retrying...")
                    continue
                else:
                    print("⚠ Request timed out after all retries. You may want to try 'reasoning_effort = \"minimal\"' or switch to 'gpt-4o-mini'")
                    raise

    # ───────────────────────────────────────────────────  workflow
    full_story = " ".join(reddit_obj["thread_post"]) \
        if settings.config["settings"]["storymodemethod"] == 1 else reddit_obj["thread_post"]

    print("⟳ Rewriter: requesting AI rewrite...")
    raw_json = _call_openai(full_story)

    # save raw response for debugging / reuse
    temp_dir = Path(f"assets/temp/{reddit_id()}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "rewriter.json").write_text(raw_json, encoding="utf-8")

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        print("⚠ Rewriter: Invalid JSON response - falling back to original text.")
        return reddit_obj

    reddit_obj["thread_title"] = data.get("hook", reddit_obj["thread_title"])

    body = data.get("body", full_story)
    reddit_obj["thread_post"] = (
        posttextparser(body) if isinstance(body, str) else body
    )

    reddit_obj["ai_caption"] = data.get("caption", "") if want_caption else ""

    return reddit_obj
