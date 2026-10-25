"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types


from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_gemini_client():
    """Initialize and return a Gemini client using GEMINI_API_KEY from .env."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to a .env file in the project root.")
    return genai.Client(api_key=api_key)

def _call_llm(prompt: str, temperature: float = 0.7) -> str:
    """Helper: call Gemini and return the response text."""
    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=500,
        ),
    )
    return (response.text or "").strip()




# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    try:
        listings = load_listings()
    except Exception as e:
        print(f"[search_listings] Failed to load listings: {e}")
        return []
 
    # Step 1: Filter by price and size
    candidates = []
    for item in listings:
        # Price filter
        if max_price is not None:
            try:
                if float(item.get("price", 0)) > max_price:
                    continue
            except (TypeError, ValueError):
                continue
 
        # Size filter (case-insensitive, partial match so "M" matches "S/M")
        if size is not None:
            item_size = str(item.get("size", "")).upper()
            if size.upper() not in item_size:
                continue
 
        candidates.append(item)
 
    # Step 2: Score by keyword overlap with description
    keywords = set(re.findall(r"\w+", description.lower()))
 
    def score(item: dict) -> int:
        # Fields to search against
        searchable = " ".join([
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("category", "")),
            str(item.get("brand", "")),
            " ".join(item.get("style_tags", [])),
            " ".join(item.get("colors", [])),
        ]).lower()
        item_words = set(re.findall(r"\w+", searchable))
        return len(keywords & item_words)
 
    scored = [(score(item), item) for item in candidates]
 
    # Step 3: Drop zero-score items and sort best-first
    #results = [item for s, item in sorted(scored, key=lambda x: x[0], reverse=True) if s > 0]
        # Step 3: Keep items matching at least half the keywords, sorted best-first
    min_score = max(1, (len(keywords) + 1) // 2)
    results = [item for s, item in sorted(scored, key=lambda x: x[0], reverse=True) if s >= min_score]
 
    return results


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    item_title = new_item.get("title", "this item")
    item_desc = new_item.get("description", "")
    item_style_tags = ", ".join(new_item.get("style_tags", []))
    item_colors = ", ".join(new_item.get("colors", []))
    item_category = new_item.get("category", "")
 
    item_summary = (
        f"Item: {item_title}\n"
        f"Category: {item_category}\n"
        f"Colors: {item_colors}\n"
        f"Style: {item_style_tags}\n"
        f"Description: {item_desc}"
    )
 
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
 
    try:
        if not wardrobe_items:
            # Empty wardrobe — give general styling advice
            prompt = (
                f"A user just thrifted this item and wants outfit ideas:\n\n"
                f"{item_summary}\n\n"
                f"They don't have a wardrobe on file yet. Give them 1–2 general outfit ideas: "
                f"what kinds of pieces pair well with this item, what vibe or aesthetic it suits, "
                f"and any specific styling tips (tucking, layering, footwear, etc.). "
                f"Be specific and enthusiastic — sound like a friend who loves fashion, not a stylist writing a report."
            )
        else:
            # Format wardrobe items
            wardrobe_lines = []
            for w in wardrobe_items:
                w_desc = f"- {w.get('title', 'Unknown item')} ({w.get('category', '')})"
                if w.get("colors"):
                    w_desc += f", colors: {', '.join(w['colors'])}"
                if w.get("style_tags"):
                    w_desc += f", style: {', '.join(w['style_tags'])}"
                wardrobe_lines.append(w_desc)
            wardrobe_text = "\n".join(wardrobe_lines)
 
            prompt = (
                f"A user is considering buying this thrifted item:\n\n"
                f"{item_summary}\n\n"
                f"Here's what they already own:\n{wardrobe_text}\n\n"
                f"Suggest 1–2 specific outfits using the new item combined with pieces from their wardrobe. "
                f"Name the actual wardrobe pieces. Include styling tips (tuck, layer, roll sleeves, etc.) "
                f"and mention the overall vibe. Sound like a fashion-forward friend, not a product catalog."
                
            )
 
        return _call_llm(prompt, temperature=0.7)
 
    except Exception as e:
        return (
            f"Couldn't generate outfit suggestions right now ({e}). "
            f"Try pairing {item_title} with basics in complementary colors — you can't go wrong!"
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return (
            "Couldn't generate a fit card — the outfit suggestion was missing. "
            "Try running the outfit suggestion step first, then come back for your caption."
        )
 
    item_title = new_item.get("title", "this thrifted piece")
    item_price = new_item.get("price", "?")
    item_platform = new_item.get("platform", "a thrift platform")
    item_condition = new_item.get("condition", "")
 
    try:
        prompt = (
            f"Write a 2–4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
            f"Item details:\n"
            f"- Name: {item_title}\n"
            f"- Price: ${item_price}\n"
            f"- Found on: {item_platform}\n"
            f"- Condition: {item_condition}\n\n"
            f"Outfit context:\n{outfit}\n\n"
            f"Rules:\n"
            f"- Write in first person, casual tone — like a real OOTD post, not a product description\n"
            f"- Mention the item name, price, and platform naturally (each once)\n"
            f"- Capture the specific vibe of the outfit\n"
            f"- You can use 1–2 relevant emojis\n"
            f"- Do NOT use hashtags\n"
            f"- Make it feel fresh and specific to THIS outfit, not generic thrift content\n\n"
            f"Caption:"
        )
 
        # Higher temperature for more variety across runs
        return _call_llm(prompt, temperature=1.0)
 
    except Exception as e:
        return (
            f"Fit card generation hit a snag ({e}). "
            f"But here's the gist: just thrifted a {item_title} for ${item_price} off {item_platform} — "
            f"and it's everything. 🖤"
        )
