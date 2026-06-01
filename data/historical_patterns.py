import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from utils.db import get_db

# Past World Cup key match dates and outcomes
# Format: (date, team_won, team_lost, stage)
historical_matches = [
    # 2022 World Cup notable matches
    ("2022-12-18", "Argentina", "France", "Final"),
    ("2022-12-14", "Argentina", "Croatia", "Semifinal"),
    ("2022-12-13", "France", "Morocco", "Semifinal"),
    ("2022-12-10", "Argentina", "Netherlands", "Quarterfinal"),
    ("2022-12-10", "France", "England", "Quarterfinal"),
    ("2022-12-06", "Argentina", "Australia", "Round of 16"),
    ("2022-12-04", "France", "Poland", "Round of 16"),

    # 2018 World Cup notable matches
    ("2018-07-15", "France", "Croatia", "Final"),
    ("2018-07-10", "France", "Belgium", "Semifinal"),
    ("2018-07-11", "Croatia", "England", "Semifinal"),
    ("2018-07-06", "France", "Uruguay", "Quarterfinal"),

    # 2014 World Cup notable matches
    ("2014-07-13", "Germany", "Argentina", "Final"),
    ("2014-07-08", "Germany", "Brazil", "Semifinal"),
    ("2014-07-09", "Argentina", "Netherlands", "Semifinal"),
]

# Tickers to track
tickers = {
    "ADS.DE": "Adidas",
    "NKE": "Nike",
    "BUD": "Budweiser (AB InBev)",
    "V": "Visa",
    "KO": "Coca-Cola",
    "MELI": "Mercado Libre",
    "ING": "ING Group",
    "SAN": "Santander",
}

def get_price_change(ticker, match_date, days_after=3):
    """Calculate % price change after a match"""
    try:
        match_dt = datetime.strptime(match_date, "%Y-%m-%d")
        
        # Get price window: 1 day before to days_after after match
        start = match_dt - timedelta(days=2)
        end = match_dt + timedelta(days=days_after + 2)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start.strftime("%Y-%m-%d"), 
                           end=end.strftime("%Y-%m-%d"))
        
        if hist.empty or len(hist) < 2:
            return None
            
        # Get closing price on/just after match day
        hist.index = hist.index.tz_localize(None)
        after_match = hist[hist.index >= match_dt]
        before_match = hist[hist.index < match_dt]
        
        if after_match.empty or before_match.empty:
            return None
            
        price_before = before_match["Close"].iloc[-1]
        price_after_1d = after_match["Close"].iloc[0] if len(after_match) > 0 else None
        price_after_3d = after_match["Close"].iloc[min(2, len(after_match)-1)]
        
        change_1d = ((price_after_1d - price_before) / price_before * 100) if price_after_1d else None
        change_3d = ((price_after_3d - price_before) / price_before * 100)
        
        return {
            "price_before": round(price_before, 2),
            "price_after_1d": round(price_after_1d, 2) if price_after_1d else None,
            "price_after_3d": round(price_after_3d, 2),
            "change_1d_pct": round(change_1d, 2) if change_1d else None,
            "change_3d_pct": round(change_3d, 2),
        }
    except Exception as e:
        print(f"  ⚠️ Error fetching {ticker} for {match_date}: {e}")
        return None

def build_historical_patterns():
    db = get_db()
    db.historical_patterns.drop()
    
    patterns = []
    
    print("📈 Fetching historical stock patterns...\n")
    
    for match_date, winner, loser, stage in historical_matches:
        print(f"Processing {winner} vs {loser} ({stage}, {match_date})")
        
        # Get sponsors for winner and loser from MongoDB
        winner_doc = db.teams.find_one({"team": winner})
        loser_doc = db.teams.find_one({"team": loser})
        
        affected_tickers = set()
        if winner_doc:
            for s in winner_doc["sponsors"]:
                if s["ticker"]:
                    affected_tickers.add(s["ticker"])
        if loser_doc:
            for s in loser_doc["sponsors"]:
                if s["ticker"]:
                    affected_tickers.add(s["ticker"])
        
        for ticker in affected_tickers:
            company_name = tickers.get(ticker, ticker)
            print(f"  📊 Fetching {company_name} ({ticker})...")
            
            price_data = get_price_change(ticker, match_date)
            
            if price_data:
                pattern = {
                    "match_date": match_date,
                    "winner": winner,
                    "loser": loser,
                    "stage": stage,
                    "ticker": ticker,
                    "company": company_name,
                    "winner_sponsor": ticker in [s["ticker"] for s in (winner_doc["sponsors"] if winner_doc else [])],
                    **price_data
                }
                patterns.append(pattern)
                print(f"  ✅ {company_name}: 1d={price_data['change_1d_pct']}%, 3d={price_data['change_3d_pct']}%")
            else:
                print(f"  ❌ No data for {ticker}")
    
    if patterns:
        db.historical_patterns.insert_many(patterns)
        db.historical_patterns.create_index("ticker")
        db.historical_patterns.create_index("winner")
        db.historical_patterns.create_index([("ticker", 1), ("winner", 1)])
        print(f"\n✅ Stored {len(patterns)} historical patterns in MongoDB")
    
    return patterns

def get_avg_pattern(ticker, team, role="winner"):
    """Get average price movement for a ticker when a team wins/loses"""
    db = get_db()
    
    query = {"ticker": ticker}
    if role == "winner":
        query["winner"] = team
    else:
        query["loser"] = team
    
    patterns = list(db.historical_patterns.find(query))
    
    if not patterns:
        return None
    
    avg_1d = sum(p["change_1d_pct"] for p in patterns if p.get("change_1d_pct")) / len(patterns)
    avg_3d = sum(p["change_3d_pct"] for p in patterns if p.get("change_3d_pct")) / len(patterns)
    
    return {
        "ticker": ticker,
        "team": team,
        "role": role,
        "sample_size": len(patterns),
        "avg_1d_pct": round(avg_1d, 2),
        "avg_3d_pct": round(avg_3d, 2),
    }

if __name__ == "__main__":
    build_historical_patterns()
    
    # Test average pattern lookup
    print("\n--- Test: Adidas after Argentina wins ---")
    result = get_avg_pattern("ADS.DE", "Argentina", "winner")
    print(result)
    
    print("\n--- Test: Nike after France wins ---")
    result = get_avg_pattern("NKE", "France", "winner")
    print(result)