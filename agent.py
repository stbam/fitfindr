"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parser ──────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query
    using regex — fast, free, and no LLM call needed for structured extraction.

    Examples:
        "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

        "looking for a leather jacket size XL"
        → {"description": "leather jacket", "size": "XL", "max_price": None}
    """
    # Extract max_price: "under $30", "max $45", "$30 or less", "below $25"
    price_match = re.search(
        r"(?:under|max|below|less than|no more than)\s*\$?\s*(\d+(?:\.\d+)?)"
        r"|\$(\d+(?:\.\d+)?)\s*(?:or less|max|ceiling)",
        query,
        re.IGNORECASE,
    )
    max_price = None
    if price_match:
        raw = price_match.group(1) or price_match.group(2)
        max_price = float(raw)

    # Extract size: "size M", "size XL", "in S/M", standalone XS/S/M/L/XL/XXL
    size_match = re.search(
        r"\bsize\s+([A-Z]{1,3}(?:\/[A-Z]{1,3})?)"
        r"|\bin\s+([A-Z]{1,3}(?:\/[A-Z]{1,3})?)\b"
        r"|\b(XS|S|M|L|XL|XXL|XXXL)\b",
        query,
        re.IGNORECASE,
    )
    size = None
    if size_match:
        size = (size_match.group(1) or size_match.group(2) or size_match.group(3)).upper()

    # Description: strip filler words and extracted tokens to get the core item phrase
    description = query
    # Remove price clause
    description = re.sub(
        r"(?:under|max|below|less than|no more than)\s*\$?\s*\d+(?:\.\d+)?",
        "",
        description,
        flags=re.IGNORECASE,
    )
    description = re.sub(
        r"\$\d+(?:\.\d+)?\s*(?:or less|max|ceiling)?",
        "",
        description,
        flags=re.IGNORECASE,
    )
    # Remove size clause
    description = re.sub(
        r"\bsize\s+[A-Z]{1,3}(?:\/[A-Z]{1,3})?\b"
        r"|\bin\s+[A-Z]{1,3}(?:\/[A-Z]{1,3})?\b"
        r"|\b(?:XS|S|M|L|XL|XXL|XXXL)\b",
        "",
        description,
        flags=re.IGNORECASE,
    )
    # Strip filler openers
    description = re.sub(
        r"^(?:i'?m?\s+)?(?:looking for|searching for|find me|want|need|got|i want|i need)\s+a?\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )
    # Collapse whitespace and punctuation artifacts
    description = re.sub(r"[,;]+", " ", description)
    description = " ".join(description.split()).strip()

    return {
        "description": description or query,  # fall back to raw query if stripping removes too much
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings — branch point
    try:
        results = search_listings(
            description=parsed["description"],
            size=parsed["size"],
            max_price=parsed["max_price"],
        )
    except Exception as exc:
        session["error"] = (
            f"Search failed unexpectedly: {exc}. "
            "Please try again or rephrase your query."
        )
        return session

    session["search_results"] = results

    if not results:
        # Build a helpful, specific error message
        constraints = []
        if parsed["size"]:
            constraints.append(f"size {parsed['size']}")
        if parsed["max_price"] is not None:
            constraints.append(f"under ${parsed['max_price']:.0f}")
        constraint_str = " and ".join(constraints)
        hint = (
            f" Try removing the {constraint_str} filter"
            if constraint_str
            else " Try different keywords"
        )
        session["error"] = (
            f"No listings found for \"{parsed['description']}\""
            + (f" ({constraint_str})" if constraint_str else "")
            + f".{hint}, or broaden your description."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    try:
        outfit = suggest_outfit(
            new_item=session["selected_item"],
            wardrobe=session["wardrobe"],
        )
    except Exception as exc:
        session["error"] = (
            f"Found your item ({session['selected_item']['title']}) but couldn't "
            f"generate outfit suggestions: {exc}. Try again in a moment."
        )
        return session

    session["outfit_suggestion"] = outfit

    # Step 6: Create fit card
    try:
        fit_card = create_fit_card(
            outfit=session["outfit_suggestion"],
            new_item=session["selected_item"],
        )
    except Exception as exc:
        # Outfit suggestion succeeded — partial result is still useful
        session["error"] = (
            f"Outfit suggestion is ready but the fit card failed: {exc}. "
            "You can still use the outfit suggestion above."
        )
        return session

    session["fit_card"] = fit_card

    # Step 7: Return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"Parsed: {session['parsed']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Parsed: {session2['parsed']}")
    print(f"Error message: {session2['error']}")