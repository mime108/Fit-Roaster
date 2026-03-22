import streamlit as st
import requests
import base64
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import fiftyone as fo

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="Outfit Court",
    page_icon="👔",
    layout="centered"
)

# ── STYLING ────────────────────────────────────────────────────
st.markdown("""
<style>
    .title {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        color: white;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def call_vision(image_bytes, prompt, mime_type="image/jpeg"):
    """Calls Gemini Vision — same as query_gemini_vision plugin."""
    base64_image = encode_image(image_bytes)
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

def roast_outfit(image_bytes, mime_type):
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

    text = call_vision(image_bytes, prompt, mime_type)
    text = text.strip()

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    text  = text.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)

def generate_restyle(dalle_prompt):
    """Generate restyle image using Gemini."""
    payload = {
        "contents": [{
            "parts": [{"text": dalle_prompt}]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "responseMimeType":   "text/plain"
        }
    }
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    content = response.json()
    if "error" in content:
        raise ValueError(content["error"].get("message", str(content["error"])))
    for part in content["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise ValueError("No image in response")

def save_to_fiftyone(image_bytes, roast_data, restyle_image_bytes=None):
    """Saves uploaded image + all metadata to FiftyOne dataset."""

    if fo.dataset_exists("outfit_roaster"):
        dataset = fo.load_dataset("outfit_roaster")
    else:
        dataset = fo.Dataset(name="outfit_roaster")
        dataset.persistent = True

    os.makedirs("images", exist_ok=True)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = f"upload_{timestamp}.jpg"
    image_path = os.path.abspath(os.path.join("images", clean_name))

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    sample = fo.Sample(filepath=image_path)
    rating = roast_data.get("rating", 0)

    # Basic fields
    sample["roast"]          = roast_data.get("roast",          "")
    sample["rating"]         = rating
    sample["rating_reason"]  = roast_data.get("rating_reason",  "")
    sample["whats_wrong"]    = roast_data.get("whats_wrong",    [])
    sample["restyle_advice"] = roast_data.get("restyle_advice", "")
    sample["dalle_prompt"]   = roast_data.get("dalle_prompt",   "")
    sample["type"]           = "original"
    sample["source"]         = "frontend_upload"
    sample["restyle_image"]  = ""

    # Caption for FiftyOne panel
    sample["caption_viewer"] = f"""Verdict: {roast_data.get('verdict', '')}
Rating: {rating}/10
Roast: {roast_data.get('roast', '')}
Whats Wrong: {', '.join(roast_data.get('whats_wrong', []))}
Glow Up: {roast_data.get('restyle_advice', '')}"""

    # Classifications for dashboard
    sample["verdict"] = fo.Classification(
        label=roast_data.get("verdict", "UNKNOWN")
    )
    sample["most_roasted_item"] = fo.Classification(
        label=roast_data.get("most_roasted_item", "unknown")
    )

    # Tags
    sample.tags.append("roasted")
    sample.tags.append("frontend_upload")

    if rating >= 8:
        sample.tags.append("elite_fit")
    elif rating >= 5:
        sample.tags.append("mid_fit")
    elif rating >= 3:
        sample.tags.append("needs_help")
    else:
        sample.tags.append("fashion_crime")

    dataset.add_sample(sample)

    # Save restyle image if provided
    if restyle_image_bytes:
        os.makedirs("generated", exist_ok=True)
        restyle_path = os.path.abspath(
            os.path.join("generated", f"restyled_{timestamp}.png")
        )
        with open(restyle_path, "wb") as f:
            f.write(restyle_image_bytes)

        restyle_sample = fo.Sample(filepath=restyle_path)
        restyle_sample["type"]           = "restyled"
        restyle_sample["original_image"] = image_path
        restyle_sample["roast"]          = roast_data.get("roast", "")
        restyle_sample["rating"]         = rating
        restyle_sample["restyle_advice"] = roast_data.get("restyle_advice", "")
        restyle_sample.tags.append("restyled")
        restyle_sample.tags.append("frontend_upload")
        dataset.add_sample(restyle_sample)

        sample["restyle_image"] = restyle_path
        sample.save()

    dataset.persistent = True
    return image_path

# ── UI ─────────────────────────────────────────────────────────

st.markdown('<p class="title">👔 Outfit Court</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Upload your outfit. Prepare to be judged.</p>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload your outfit photo",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed"
)

if uploaded_file:
    image_bytes = uploaded_file.read()
    mime_type   = "image/png" if uploaded_file.name.endswith(".png") else "image/jpeg"

    st.image(image_bytes, caption="Your Outfit", use_column_width=True)

    if st.button("⚖️ Take Me To Court", type="primary", use_container_width=True):
        with st.spinner("Gemini is judging your outfit..."):
            try:
                data = roast_outfit(image_bytes, mime_type)
                st.session_state["roast_data"]  = data
                st.session_state["image_bytes"] = image_bytes

                save_to_fiftyone(image_bytes, data)
                st.success("Saved to FiftyOne!")

            except Exception as e:
                st.error(f"Failed: {e}")

if "roast_data" in st.session_state:
    data   = st.session_state["roast_data"]
    rating = data.get("rating", 0)

    if rating >= 8:
        emoji = "🔥"
        color = "#00ff88"
    elif rating >= 5:
        emoji = "😐"
        color = "#ffaa00"
    else:
        emoji = "💀"
        color = "#ff4444"

    # Rating display
    st.markdown(f"""
    <div style="text-align:center; margin: 1.5rem 0">
        <div style="font-size:3rem">{emoji}</div>
        <div style="font-size:3rem; font-weight:900; color:{color}">{rating}/10</div>
        <div style="color:#aaa; font-size:1rem; margin-top:0.5rem">
            {data.get('rating_reason', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Verdict badge
    verdict = data.get("verdict", "")
    verdict_colors = {
        "SLAY":       "#00ff88",
        "ALMOST":     "#ffaa00",
        "NEEDS WORK": "#ff8800",
        "NOPE":       "#ff4444"
    }
    vcolor = verdict_colors.get(verdict, "#888")
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:1rem">
        <span style="background:{vcolor}22; color:{vcolor};
                     padding:6px 20px; border-radius:20px;
                     font-weight:700; font-size:1.1rem">
            {verdict}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Roast
    st.markdown("### 💬 The Verdict")
    st.markdown(f"> {data.get('roast', '')}")

    # Whats wrong
    st.markdown("### ❌ Fashion Crimes Committed")
    for item in data.get("whats_wrong", []):
        st.markdown(f"- {item}")

    # Restyle advice
    st.markdown("### ✨ How To Fix This")
    st.info(data.get("restyle_advice", ""))

    # Restyle button
    st.markdown("---")
    st.markdown("### 🎨 Want to see the improved look?")

    if st.button("✨ Generate My Restyle", type="primary", use_container_width=True):
        with st.spinner("Gemini is creating your improved outfit..."):
            try:
                image_data = generate_restyle(data.get("dalle_prompt", ""))
                st.session_state["restyle_image"] = image_data

                save_to_fiftyone(
                    st.session_state["image_bytes"],
                    st.session_state["roast_data"],
                    restyle_image_bytes=image_data
                )
                st.success("Restyle saved to FiftyOne!")

            except Exception as e:
                st.error(f"Restyle failed: {e}")

if "restyle_image" in st.session_state:
    st.markdown("### 👗 Your Restyled Look")
    col1, col2 = st.columns(2)
    with col1:
        st.image(
            st.session_state["image_bytes"],
            caption="Before",
            use_column_width=True
        )
    with col2:
        st.image(
            st.session_state["restyle_image"],
            caption="After (AI Generated)",
            use_column_width=True
        )
    st.success("Glow up complete! Check FiftyOne to see your results.")