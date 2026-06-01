from google import genai
from google.genai import types
import yfinance as yf
from datetime import datetime
from utils.db import get_db
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ── Tool functions the agent can call ──────────────────────────────────────

def get_team_sponsors(team_name: str) -> dict:
    """Get sponsors and stock tickers for a World Cup team"""
    db = get_db()
    team = db.teams.find_one({"team": team_name})
    if not team:
        return {"error": f"Team '{team_name}' not found in database"}
    return {"team": team_name, "sponsors": team["sponsors"]}

def get_historical_pattern(ticker: str, team: str, role: str = "winner") -> dict:
    """Get average stock movement after a team wins or loses"""
    db = get_db()
    query = {"ticker": ticker}
    if role == "winner":
        query["winner"] = team
    else:
        query["loser"] = team

    patterns = list(db.historical_patterns.find(query))
    if not patterns:
        return {"error": f"No historical data for {ticker} when {team} is {role}"}

    valid_1d = [p["change_1d_pct"] for p in patterns if p.get("change_1d_pct") is not None]
    valid_3d = [p["change_3d_pct"] for p in patterns if p.get("change_3d_pct") is not None]

    return {
        "ticker": ticker,
        "team": team,
        "role": role,
        "sample_size": len(patterns),
        "avg_1d_pct": round(sum(valid_1d) / len(valid_1d), 2) if valid_1d else None,
        "avg_3d_pct": round(sum(valid_3d) / len(valid_3d), 2) if valid_3d else None,
    }

def get_current_stock_price(ticker: str) -> dict:
    """Get current stock price and today's change"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        current = round(info.last_price, 2)
        prev_close = round(info.previous_close, 2)
        change_pct = round(((current - prev_close) / prev_close) * 100, 2)
        return {
            "ticker": ticker,
            "current_price": current,
            "prev_close": prev_close,
            "change_today_pct": change_pct,
            "currency": info.currency
        }
    except Exception as e:
        return {"error": f"Could not fetch price for {ticker}: {str(e)}"}

def save_signal_report(report: dict) -> dict:
    """Save a generated signal report to MongoDB"""
    db = get_db()
    import copy
    report_to_save = copy.deepcopy(report)
    report_to_save["created_at"] = datetime.utcnow().isoformat()
    result = db.signal_reports.insert_one(report_to_save)
    return {"saved": True, "id": str(result.inserted_id)}

# ── Tool dispatcher ─────────────────────────────────────────────────────────

def dispatch_tool(tool_name: str, tool_args: dict):
    if tool_name == "get_team_sponsors":
        return get_team_sponsors(**tool_args)
    elif tool_name == "get_historical_pattern":
        return get_historical_pattern(**tool_args)
    elif tool_name == "get_current_stock_price":
        return get_current_stock_price(**tool_args)
    elif tool_name == "save_signal_report":
        return save_signal_report(**tool_args)
    else:
        return {"error": f"Unknown tool: {tool_name}"}

# ── Tool schemas ────────────────────────────────────────────────────────────

tool_schemas = [
    types.FunctionDeclaration(
        name="get_team_sponsors",
        description="Get the corporate sponsors and stock tickers for a World Cup team",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "team_name": types.Schema(
                    type=types.Type.STRING,
                    description="The name of the national team e.g. Argentina, France, Brazil"
                )
            },
            required=["team_name"]
        )
    ),
    types.FunctionDeclaration(
        name="get_historical_pattern",
        description="Get average stock price movement after a team wins or loses",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "ticker": types.Schema(type=types.Type.STRING, description="Stock ticker e.g. ADS.DE, NKE"),
                "team": types.Schema(type=types.Type.STRING, description="Team name e.g. Argentina"),
                "role": types.Schema(type=types.Type.STRING, description="winner or loser")
            },
            required=["ticker", "team", "role"]
        )
    ),
    types.FunctionDeclaration(
        name="get_current_stock_price",
        description="Get the current stock price and today's change for a ticker",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "ticker": types.Schema(type=types.Type.STRING, description="Stock ticker e.g. NKE, BUD, V")
            },
            required=["ticker"]
        )
    ),
    types.FunctionDeclaration(
        name="save_signal_report",
        description="Save the final signal report to the database",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "report": types.Schema(type=types.Type.OBJECT, description="The complete signal report")
            },
            required=["report"]
        )
    )
]

gemini_tools = [types.Tool(function_declarations=tool_schemas)]

# ── Main agent ──────────────────────────────────────────────────────────────

def run_signal_agent(match_result: str):
    print(f"\n🏆 SportsPulse Signal Agent")
    print(f"⚽ Match: {match_result}")
    print("=" * 60)

    system_instruction = """You are SportsPulse, an AI investment signal agent.
    When given a World Cup match result, you:
    1. Identify the winning and losing teams
    2. Look up sponsors for both teams using get_team_sponsors
    3. Check historical stock patterns for key sponsors using get_historical_pattern
    4. Get current stock prices using get_current_stock_price
    5. Generate a clear signal report ranking the top 3 stocks to watch
    6. Save the report using save_signal_report

    Always check sponsors for BOTH the winner and loser.
    Focus on the most interesting signals — large historical moves or unusual price action.
    Be concise and specific with numbers.
    """

    messages = [types.Content(role="user", parts=[types.Part(text=match_result)])]
    
    # Agentic loop
    while True:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=gemini_tools,
                temperature=0.2
            )
        )

        candidate = response.candidates[0]
        messages.append(types.Content(role="model", parts=candidate.content.parts))

        # Check for tool calls
        tool_calls = [p for p in candidate.content.parts if p.function_call is not None]

        if not tool_calls:
            # Agent is done
            final_text = "".join(p.text for p in candidate.content.parts if hasattr(p, 'text') and p.text)
            if not final_text:
                final_text = "Signal report generated and saved to database successfully."
            print("\n📊 SIGNAL REPORT:")
            print("=" * 60)
            print(final_text)
            return final_text
       

        # Execute tools and feed results back
        tool_results = []
        for part in tool_calls:
            fc = part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args)

            print(f"🔧 Calling: {tool_name}({tool_args})")
            result = dispatch_tool(tool_name, tool_args)
            print(f"   → {result}")

            tool_results.append(types.Part(
                function_response=types.FunctionResponse(
                    name=tool_name,
                    response={"result": json.dumps(result)}
                )
            ))

        messages.append(types.Content(role="user", parts=tool_results))

if __name__ == "__main__":
    run_signal_agent("Argentina beat France 3-3 (4-2 on penalties) in the 2022 World Cup Final")