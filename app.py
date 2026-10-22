
import os, re, json, math, time
from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder="static")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY","").strip()

SYSTEM_PROMPT = """You are a resale-deal analyst for Miami, Florida.
Analyze marketplace listings for flipping. Be conservative. Never invent a price or condition.
Return JSON fields: title, price, estimated_resale, estimated_profit, margin_pct, demand,
sell_speed, risk, score, verdict, max_buy, reason, red_flags, url.
Profit = estimated resale - purchase price - estimated selling/transaction costs.
If evidence is weak, lower score and mark CHECK. Ignore broken, parts, replica/fake, locked,
stolen-looking, incomplete, or suspicious listings. Prefer local pickup opportunities.
"""

def fc_search(q):
    if not FIRECRAWL_API_KEY:
        return {"error":"Missing FIRECRAWL_API_KEY. Set it in the environment."}
    r=requests.post(
        "https://api.firecrawl.dev/v2/search",
        headers={"Authorization":f"Bearer {FIRECRAWL_API_KEY}","Content-Type":"application/json"},
        json={"query":q,"limit":20,"sources":["web"],"scrapeOptions":{"formats":["markdown"]}},
        timeout=45)
    r.raise_for_status()
    return r.json()

@app.get("/")
def index():
    return send_from_directory("static","index.html")

@app.post("/api/search")
def search():
    data=request.get_json(force=True)
    query=(data.get("query") or "cameras").strip()
    max_buy=float(data.get("max_buy") or 2000)
    min_profit=float(data.get("min_profit") or 50)
    location="Miami, Florida"
    queries=[
        f'{query} for sale {location} marketplace',
        f'{query} used {location} OfferUp',
        f'{query} used for sale {location}'
    ]
    raw=[]
    errors=[]
    for q in queries:
        try:
            x=fc_search(q)
            if "error" in x: errors.append(x["error"]); break
            raw.extend(x.get("data",[]))
        except Exception as e:
            errors.append(str(e))
    # Deduplicate and extract simple prices. AI analysis is intentionally conservative in this
    # deployable starter: it does not fabricate resale comps when they aren't in the sources.
    seen=set(); listings=[]
    for item in raw:
        url=item.get("url","")
        if not url or url in seen: continue
        seen.add(url)
        title=item.get("title") or "Untitled listing"
        text=(item.get("description") or item.get("markdown") or item.get("snippet") or "")
        prices=[float(x.replace(",","")) for x in re.findall(r'\$\s?([0-9][0-9,]*(?:\.[0-9]{1,2})?)', title+" "+text)]
        price=min(prices) if prices else None
        if price is None or price>max_buy: continue
        # Conservative placeholder until a sold-comps source is supplied.
        resale=round(price*1.25,2)
        costs=round(max(10, resale*0.10),2)
        profit=round(resale-price-costs,2)
        margin=round(profit/price*100,1) if price else 0
        score=max(0,min(100,round(45 + margin*1.3)))
        verdict="BUY" if profit>=min_profit and score>=75 else ("CHECK" if score>=55 else "PASS")
        listings.append({
            "title":title,"price":price,"estimated_resale":resale,
            "estimated_profit":profit,"margin_pct":margin,"demand":"Unknown",
            "sell_speed":"Unknown","risk":"Medium","score":score,"verdict":verdict,
            "max_buy":round(max(0,resale-costs-min_profit),2),
            "reason":"Initial estimate; verify condition and sold comps before buying.",
            "red_flags":[],"url":url,"source":item.get("sourceURL") or url
        })
    listings.sort(key=lambda x:x["score"], reverse=True)
    return jsonify({"listings":listings[:50],"errors":errors,
                    "note":"Resale estimates are conservative placeholders until sold-comps data is connected."})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","8080")))
