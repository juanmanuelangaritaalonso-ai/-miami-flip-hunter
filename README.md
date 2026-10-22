# Miami Flip Hunter

Deployable mobile-friendly web app for scanning web-accessible Miami resale listings.

## Run
1. Install Python 3.11+
2. `pip install -r requirements.txt`
3. Set `FIRECRAWL_API_KEY`
4. `python app.py`
5. Open the shown URL on your phone (same network for local use).

## Deploy
Works on Render/Railway/Fly.io or another Python host. Add the environment variable:
`FIRECRAWL_API_KEY=...`

## Important
This version uses permitted/publicly accessible web search through Firecrawl. It does not bypass
Facebook Marketplace/OfferUp login, CAPTCHA, robots controls, or anti-bot protections.
The current resale estimate is a conservative starter formula, not a sold-comps database.
Replace it with a sold-price provider before treating BUY as a final purchasing decision.
