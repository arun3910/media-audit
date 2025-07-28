import os
import json
from openai import OpenAI
import difflib
from markupsafe import Markup

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TONE_COLOR_MAP = {
    "Neutral": "secondary",
    "Angry": "danger",
    "Fearful": "purple",
    "Hopeful": "success"
}

def get_tone_color(tone):
    return TONE_COLOR_MAP.get(tone, "secondary")


def generate_diff_html(original: str, rewritten: str) -> str:
    """
    Generate word-level diff HTML between original and rewritten text.
    """
    diff = difflib.ndiff(original.split(), rewritten.split())
    result = []

    for word in diff:
        if word.startswith("- "):
            result.append(f"<span style='background-color:#ffcccc;' title='Removed'>{word[2:]}</span>")
        elif word.startswith("+ "):
            result.append(f"<span style='background-color:#ccffcc;' title='Added'>{word[2:]}</span>")
        elif word.startswith("  "):
            result.append(word[2:])
    return Markup(" ".join(result))


def analyze_article(text):
    prompt = f'''
You are a news media analyst. Analyze the following news article and return a JSON object with the following structure:

{{
  "summary": "...",  // a 3-line summary
  "perspective_label": "Pro-government | Critical | Sympathetic | Neutral | Corporate-friendly | Public-interest | Sensational",
  "tone": "Neutral | Angry | Fearful | Hopeful",
  "emotion_score": {{"anger": 0.0, "joy": 0.0, "fear": 0.0, "surprise": 0.0}}
  "rewritten": "..."  // Suggest a more neutral and balanced rewrite without changing the core facts.
}}

Even if the article appears objective, assign the most likely perspective_label based on its framing, tone, and language.

Article:
{text}
'''

    def call_gpt(model_name):
        return client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

    try:
        try:
            response = call_gpt("gpt-4o")
        except Exception as e:
            print("⚠️ GPT-4o failed, falling back to gpt-3.5")
            response = call_gpt("gpt-3.5-turbo")

        raw_text = response.choices[0].message.content.strip()

        if raw_text.startswith("```json") or raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(raw_text)

        # Ensure all required fields exist
        parsed.setdefault("summary", "Could not extract summary.")
        parsed.setdefault("perspective_label", "Unknown")
        parsed.setdefault("tone", "Unknown")
        parsed.setdefault("emotion_score", {
            "anger": 0.0,
            "joy": 0.0,
            "fear": 0.0,
            "surprise": 0.0
        })
        parsed.setdefault("rewritten", "Rewrite not available.")

        # Add tone color class for rendering
        parsed["tone_color"] = get_tone_color(parsed["tone"])

        return parsed

    except json.JSONDecodeError as je:
        print("⚠️ JSON parsing failed:", je)
        print("🔎 Raw GPT output was:", raw_text)
    except Exception as e:
        print("🔥 GPT API error:", e)

    return {
        "summary": "Could not process article.",
        "perspective_label": "Unknown",
        "tone": "Unknown",
        "tone_color": "secondary",
        "emotion_score": {"anger": 0, "joy": 0, "fear": 0, "surprise": 0},
    }

def rewrite_article(text):
    prompt = f'''
You are an editor helping improve clarity and engagement in news reporting. 
Rewrite the article below to make it clearer and concise so that users are more engrossed in reading the whole article. 
Analyze the current tone and improve it. Also improve perspective and emotional score.

Return only the rewritten article text.

Original Article:
{text}
'''

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        rewritten_text = response.choices[0].message.content.strip()
        return rewritten_text
    except Exception as e:
        print("🔥 Rewrite error:", e)
        return "Rewrite failed due to API error."


def suggest_headlines(text):
    prompt = f"""
You're an editorial headline expert. Given the article content below, suggest:
1. One improved, engaging headline that is clear and professional (not clickbait)
2. Two A/B testing headline variants

Article:
{text}

Respond with:
Headline: ...
Variants: ...
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        content = response.choices[0].message.content.strip()
        lines = content.split("\n")
        headline = lines[0].replace("Headline:", "").strip()
        variants = "  ".join(line.replace("Variants:", "").strip() for line in lines[1:] if line)
        return headline, variants
    except Exception as e:
        print("🛑 Headline error:", e)
        return "Unavailable", "Unavailable"


def fact_check_claims(text):
    prompt = f"""
You are a fact-checking assistant. Extract key factual claims from this article and verify them against known public facts. 
Return brief results in the form of bullet points with claim# and verification# for display.

Respond in points without bullets.

Article:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("🛑 Fact-check error:", e)
        return Markup("<p>Fact-checking failed or not available.</p>")


def bias_framing_analysis(text):
    prompt = f"""
You are a media framing analyst.

Analyze the framing and bias in the article below. Return a brief summary of:
1. Framing style used (e.g. sympathetic, critical, neutral, sensational)
2. How different groups (public, corporate, political, regional) may perceive it
3. Suggestions to make the framing more balanced or neutral if needed

Respond in 3 points in different lines without bullets.

Article:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("🛑 Bias framing error:", e)
        return "Framing analysis unavailable."


def tone_effect_analysis(text):
    prompt = f"""
You're a tone and communication strategist.

Analyze the article tone and return:
1. Summary of the tone's effect on readers
2. Which demographics it may attract or alienate
3. Suggestions to fine-tune the tone to reach a broader or intended audience

Respond in 3 points in different lines without bullets.

Article:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("🛑 Tone analysis error:", e)
        return "Tone perception analysis unavailable."
