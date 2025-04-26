# utils/rewriter.py

import json
import requests
from utils import settings
from utils.posttextparser import posttextparser

def rewrite_reddit(reddit_obj: dict) -> dict:
    """
    Only in story mode: Send the full story to OpenAI once,
    get back a JSON with 'hook' and 'body', then split 'body' into sentences.
    Comments remain unchanged; other modes bypass this completely.
    """
    cfg = settings.config["settings"]["rewriter"]
    # only activate when rewriter.enabled AND storymode = True
    if not cfg["enabled"] or not settings.config["settings"]["storymode"]:
        return reddit_obj

    endpoint = cfg["api_endpoint"]
    headers = {
        "Authorization": f"Bearer {cfg['api_token']}",
        "Content-Type": "application/json",
    }
    model   = cfg["model"]
    prompt = cfg["prompt"]
    
    target_group = cfg["target_group"]

    def _call_api(full_text: str) -> dict:
        """
        Send one request that asks for a JSON { hook: "...", body: "..." }.
        """
        # fill in the prompt
        story = full_text

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a social media expert."},
                {"role": "user", "content":
                    "Please output a JSON object with two fields:\n\n"
                    f"1) 'hook': an exciting TikTok video title (max. 90 chars) that teases but does not spoil the story, tailored to my target group: {target_group}.\n"
                    "2) 'body': the rewritten story text, preserving original meaning, ~1.1 minute read-aloud, engaging, lively, youthful, direct ('you'), TikTok-compliant.\n\n"
                    "Do NOT include any extra keys. Respond ONLY with valid JSON. Do not use any Emojis!\n\n"
                    f"Additional Info:\n{prompt}"
                    f"STORY:\n{story}"
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "n": 1,
        }

        # DEBUG: outgoing request
        print("\n--- Rewriter Debug ---")
        print(">> POST", endpoint)
        print(">> Payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        response = requests.post(endpoint, headers=headers, json=payload)
        print("<< Status code:", response.status_code)
        print("<< Raw response:")
        print(response.text)

        response.raise_for_status()
        data = response.json()

        # extract the assistant's content and parse JSON
        text = data["choices"][0]["message"]["content"]
        print("<< Assistant raw content:")
        print(text)

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            print("!! JSON parse error:", e)
            # fallback: wrap entire text as body
            result = {"hook": reddit_obj["thread_title"], "body": full_text}

        print("<< Parsed result:", result)
        print("--- End Rewriter Debug ---\n")
        return result

    # 1) Combine all story paragraphs into one text blob
    if settings.config["settings"]["storymodemethod"] == 1:
        full_story = " ".join(reddit_obj["thread_post"])
    else:
        full_story = reddit_obj["thread_post"]

    # 2) Call the API once
    print("⟳ Rewriter: sending full story to OpenAI for hook+body…")
    api_output = _call_api(full_story)

    # 3) Replace title and post content
    reddit_obj["thread_title"] = api_output.get("hook", reddit_obj["thread_title"])
    # split body into sentences for TTS
    body_text = api_output.get("body", full_story)
    if isinstance(body_text, str):
        reddit_obj["thread_post"] = posttextparser(body_text)
    else:
        # if somehow already a list, trust it
        reddit_obj["thread_post"] = body_text

    return reddit_obj
