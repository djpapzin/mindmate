# Brave Web Search Integration (MindMate)

This project includes **optional, opt-in** web search support powered by the
[Brave Search API](https://api.search.brave.com/).

The goal is to let MindMate fetch fresh, factual information **only when the
user explicitly asks for it**, without any background or surprise calls.

---

## 1. Configuration

Web search is disabled by default until you provide a Brave API key via
environment variables.

Set one of the following (first one wins):

- `BRAVE_API_KEY`
- `BRAVE_SEARCH_API` (legacy/fallback)

Example (Render / `.env`):

```bash
# Never commit secrets – set this in your host environment only
BRAVE_API_KEY=your_brave_subscription_token_here
```

> Note: The key is **never** logged. If it's missing or invalid, the bot will
> return a friendly "web search not configured / unavailable" message instead
> of crashing.

---

## 2. How it Works

The integration lives in two places:

- `src/web_search.py` – small helper module that wraps the Brave Search API
- `src/bot.py` – wires web search into the chat flow (explicit trigger only)

`web_search.py` exposes a single function:

```python
from web_search import search_web

result_text = search_web("bitcoin price today", max_results=5)
```

- It calls Brave's `/res/v1/web/search` endpoint.
- It returns a **plain text summary** of results (titles, URLs, short snippets).
- On any error (network, HTTP, missing config), it returns a human-friendly
  error string instead of raising.

The main bot only calls this helper when the user explicitly asks for it.

---

## 3. User Trigger Pattern (Opt-in Only)

To keep behaviour predictable and safe, v1 exposes a single, explicit trigger:

- Messages starting with `web:` invoke Brave search.

Examples:

- `web: bitcoin price today`
- `web: latest news about bipolar treatment`
- `web: weather in Johannesburg tomorrow`

When a message starts with `web:`:

1. The text after `web:` is taken as the **search query**.
2. `search_web(query, max_results=5)` is called.
3. The returned text is injected into the LLM prompt as extra **system
   context** (not as a user message).
4. The user message content is set to just the query portion (after `web:`).
5. If search fails, the bot replies that web search is unavailable and falls
   back to a normal non‑web response.

There are **no background or heuristic web calls**. If the user does not use
`web:`, the bot behaves exactly as before.

---

## 4. Prompt Integration Details

In `src/bot.py` inside `handle_message`:

- If `web_results` is available, the base system prompt is extended with:
  - A short instruction to treat the results as up‑to‑date context.
  - The formatted search results text block.
- This augmented system prompt is then passed as the **single system message**
  at the top of the `messages` list for `openai_client.chat.completions.create`.

This keeps the change minimal while ensuring the model:

- Sees the results as trusted but not absolute.
- Can still say "I don't know" or "the results aren't clear" when needed.

---

## 5. Dependencies

`requirements.txt` now includes:

```text
httpx>=0.27.0,<1.0.0
```

This is used as the HTTP client for Brave API calls.

Make sure to reinstall / update dependencies after pulling:

```bash
pip install -r requirements.txt
```

---

## 6. Safety Notes

- **No secrets in code** – API keys are only read from environment variables.
- **No key logging** – errors are logged with status codes and messages, never
  the token itself.
- **Opt-in only** – the bot will never call Brave unless the user starts their
  message with `web:`.
- **Graceful degradation** – on any error, the bot falls back to normal LLM
  behaviour and informs the user that web search isn't available right now.

This keeps web integration small, safe, and easy to reason about for future
iterations.
