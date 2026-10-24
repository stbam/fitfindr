"""
fitfindr_mcp.py

MCP server that exposes the FitFindr tools to an MCP client (e.g. Claude Code).
The client's LLM does the planning that agent.py does by hand: it decides
which tools to call, in what order, and with what arguments.

Run directly (stdio transport):
    python fitfindr_mcp.py
"""

from mcp.server.mcpserver import MCPServer

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

mcp = MCPServer(
    "fitfindr",
    instructions=(
        "FitFindr helps users find secondhand clothing. Use `search` to find "
        "listings, `outfit_ideas` to style a chosen listing with the user's "
        "wardrobe, and `fit_card` to write a caption for the final outfit."
    ),
)


def _wardrobe(use_wardrobe: bool) -> dict:
    return get_example_wardrobe() if use_wardrobe else get_empty_wardrobe()


# ── tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def search(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Search secondhand listings (Depop, thredUp, Poshmark) by keywords.

    Args:
        description: Keywords for the item, e.g. "vintage graphic tee".
        size:        Optional size filter, e.g. "M" or "XL".
        max_price:   Optional price ceiling in USD (inclusive).
        limit:       Max number of results to return, best match first.
    """
    return search_listings(description, size, max_price)[:limit]


@mcp.tool()
def outfit_ideas(listing: dict, use_wardrobe: bool = True) -> str:
    """
    Suggest 1–2 outfits pairing a listing (as returned by `search`) with the
    user's wardrobe. Set use_wardrobe=False for general styling advice.
    """
    return suggest_outfit(listing, _wardrobe(use_wardrobe))


@mcp.tool()
def fit_card(outfit: str, listing: dict) -> str:
    """
    Write a short Instagram/TikTok-style caption for an outfit built around
    a listing. `outfit` is the text returned by `outfit_ideas`.
    """
    return create_fit_card(outfit, listing)


# ── resources ─────────────────────────────────────────────────────────────────

@mcp.resource("fitfindr://wardrobe", mime_type="application/json")
def wardrobe() -> dict:
    """The user's current wardrobe (example closet)."""
    return get_example_wardrobe()


if __name__ == "__main__":
    mcp.run()
