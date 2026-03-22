from dotenv import load_dotenv
import os
import json
import time
import requests
import base64
import fiftyone as fo
import fiftyone.brain as fob

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── HELPERS ────────────────────────────────────────────────────

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def call_gemini_vision(image_path, prompt):
    mime_type    = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
    base64_image = encode_image(image_path)
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": base64_image}}
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.7
        }
    }
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    content = response.json()
    if "error" in content:
        raise ValueError(content["error"].get("message", str(content["error"])))
    return content["candidates"][0]["content"]["parts"][0].get("text", "")

# ── ROAST FUNCTION ─────────────────────────────────────────────

def roast_outfit(image_path):
    print(f"    Roasting with Gemini Vision...")

    prompt = """You are a sarcastic but witty fashion critic.

Look at this outfit and return a JSON object with exactly these fields:
- roast: exactly 2 short sentences maximum. No apostrophes.
- rating: number from 1-10
- rating_reason: one sentence explaining the score. No apostrophes.
- whats_wrong: array of 2-4 short strings (clothing piece names only)
- restyle_advice: 2-3 sentences on how to restyle. No apostrophes.
- dalle_prompt: under 30 words. Start with "A full body photo of a person wearing"
- verdict: one of exactly these values: "SLAY", "NOPE", "ALMOST", "NEEDS WORK"
- most_roasted_item: the single worst clothing piece e.g. "shoes", "jacket", "pants"

CRITICAL RULES:
- Return ONLY the JSON object
- No markdown, no backticks, no code blocks
- No apostrophes anywhere
- roast must be 2 sentences max
- Valid JSON only

Example:
{
  "roast": "This outfit has given up on life. The shoes are doing the most damage.",
  "rating": 4,
  "rating_reason": "The shoes are clean but nothing else is.",
  "whats_wrong": ["baggy jeans", "oversized hoodie"],
  "restyle_advice": "Try slim fit jeans and a fitted shirt.",
  "dalle_prompt": "A full body photo of a person wearing slim fit dark jeans and a white fitted shirt",
  "verdict": "NEEDS WORK",
  "most_roasted_item": "jeans"
}"""

    text = call_gemini_vision(image_path, prompt)
    print(f"    Raw response: {text[:100]}...")

    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()

    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)

# ── THE AGENT LOOP ─────────────────────────────────────────────

def run_agent():
    print("=" * 50)
    print("OUTFIT COURT — GEMINI VISION AGENT")
    print("=" * 50)

    if fo.dataset_exists("outfit_roaster"):
        dataset = fo.load_dataset("outfit_roaster")
        print(f"Loaded existing dataset: {len(dataset)} samples")
    else:
        dataset = fo.Dataset(name="outfit_roaster")
        dataset.persistent = True
        print("Created new dataset")

    # Get all images
    image_folder = "images"
    image_files  = [
        os.path.join(image_folder, f)
        for f in sorted(os.listdir(image_folder))
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    print(f"Found {len(image_files)} images")

    # Add new images
    existing_paths = set(dataset.values("filepath"))
    new_images = [
        f for f in image_files
        if os.path.abspath(f) not in existing_paths
    ]

    if new_images:
        print(f"Adding {len(new_images)} new images...")
        for img in new_images:
            sample = fo.Sample(filepath=os.path.abspath(img))
            sample["type"] = "original"
            dataset.add_sample(sample)

    # Find unprocessed
    print("\nAgent scanning for unroasted outfits...")
    unprocessed = dataset.match(
        ~fo.ViewField("tags").contains("roasted")
    ).match(
        fo.ViewField("type") == "original"
    )

    total   = len(unprocessed)
    success = 0
    failed  = 0

    print(f"Found {total} outfits to roast\n")

    for i, sample in enumerate(unprocessed):
        filename = os.path.basename(sample.filepath)
        print(f"[{i+1}/{total}] {filename}")

        # Retry logic
        max_retries = 3
        data        = None

        for attempt in range(max_retries):
            try:
                data = roast_outfit(sample.filepath)
                break
            except Exception as retry_err:
                if "quota" in str(retry_err).lower() or "429" in str(retry_err):
                    print(f"    Rate limited. Waiting 60s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(60)
                else:
                    raise retry_err

        if data is None:
            print(f"    Failed after {max_retries} retries")
            failed += 1
            continue

        try:
            # Store all fields
            sample["roast"]          = data.get("roast",          "")
            sample["rating"]         = data.get("rating",          0)
            sample["rating_reason"]  = data.get("rating_reason",  "")
            sample["whats_wrong"]    = data.get("whats_wrong",    [])
            sample["restyle_advice"] = data.get("restyle_advice", "")
            sample["dalle_prompt"]   = data.get("dalle_prompt",   "")
            sample["restyle_image"]  = ""

            # Caption for FiftyOne panel
            sample["caption_viewer"] = f"""Verdict: {data.get('verdict', '')}
Rating: {data.get('rating', 0)}/10
Roast: {data.get('roast', '')}
Whats Wrong: {', '.join(data.get('whats_wrong', []))}
Glow Up: {data.get('restyle_advice', '')}"""

            # Classifications for dashboard
            sample["verdict"] = fo.Classification(
                label=data.get("verdict", "UNKNOWN")
            )
            sample["most_roasted_item"] = fo.Classification(
                label=data.get("most_roasted_item", "unknown")
            )

            # Tags
            rating = data.get("rating", 0)
            sample.tags.append("roasted")
            sample.tags.append("awaiting_restyle")

            if rating >= 8:
                sample.tags.append("elite_fit")
            elif rating >= 5:
                sample.tags.append("mid_fit")
            elif rating >= 3:
                sample.tags.append("needs_help")
            else:
                sample.tags.append("fashion_crime")

            sample.save()
            success += 1

            emoji = "🔥" if rating >= 8 else "😐" if rating >= 5 else "💀"
            print(f"    {emoji} {rating}/10 — {data.get('verdict','')}")
            print(f"    {data.get('roast','')[:80]}...")
            print()

            # Wait 30 seconds between requests
            time.sleep(30)

        except Exception as e:
            print(f"    Failed to save: {e}")
            failed += 1
            continue

    # Brain similarity
    roasted = dataset.match_tags("roasted")
    if len(roasted) >= 2:
        print("\nComputing outfit similarity (CLIP)...")
        try:
            fob.compute_similarity(
                roasted,
                model="clip-vit-base32-torch",
                brain_key="outfit_sim"
            )
            print("Similarity ready!")
        except Exception as e:
            print(f"Similarity skipped: {e}")

    # Summary
    print("=" * 50)
    print("AGENT COMPLETE")
    print("=" * 50)
    print(f"Roasted  : {success}")
    print(f"Failed   : {failed}")

    elite  = len(dataset.match_tags("elite_fit"))
    mid    = len(dataset.match_tags("mid_fit"))
    needs  = len(dataset.match_tags("needs_help"))
    crimes = len(dataset.match_tags("fashion_crime"))

    print(f"\n🔥 Elite fits    : {elite}")
    print(f"😐 Mid fits      : {mid}")
    print(f"😬 Needs help    : {needs}")
    print(f"💀 Fashion crimes: {crimes}")

    dataset.persistent = True

    print("\nLaunching FiftyOne app...")
    session = fo.launch_app(dataset)
    input("\nPress Enter to exit...\n")

if __name__ == "__main__":
    run_agent()