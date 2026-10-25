# FitFindr — Starter Kit

## Setup

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

```
GEMINI_API_KEY=your_key_here {root of the folder}
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:

```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:

```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Use as an MCP server

FitFindr's tools are also exposed as an MCP server (`fitfindr_mcp.py`), so an AI client like Claude can decide which tools to call and in what order.

1. Clone the repo, create a venv, and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your own Gemini key:

   ```
   GEMINI_API_KEY=your_key_here
   ```

3. Connect a client:
   - **Claude Code:** open the project folder. It picks up `.mcp.json` automatically.
   - **Claude Desktop:** add this to its config file, replacing `/path/to/fitfindr` with the full path to your clone:

     ```json
     {
       "mcpServers": {
         "fitfindr": {
           "command": "/path/to/fitfindr/.venv/bin/python",
           "args": ["/path/to/fitfindr/fitfindr_mcp.py"]
         }
       }
     }
     ```

4. Try a prompt like:

   > Find me a vintage graphic tee under $30 and style it with my wardrobe.

### Tools

| Tool           | Inputs                                                                        | Returns                                     |
| -------------- | ----------------------------------------------------------------------------- | ------------------------------------------- |
| `search`       | `description`, `size` (optional), `max_price` (optional), `limit` (default 5) | List of matching listings, best match first |
| `outfit_ideas` | `listing`, `use_wardrobe` (default `true`)                                    | 1–2 outfit suggestions as text              |
| `fit_card`     | `outfit`, `listing`                                                           | A short social-media caption                |
