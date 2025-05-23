import os
import json

PROMPT_FILE = "config/prompt_templates.json"

def get_saved_prompts():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_prompt(name, content):
    prompts = get_saved_prompts()
    prompts[name] = content
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

def get_prompt(name):
    return get_saved_prompts().get(name, "")
