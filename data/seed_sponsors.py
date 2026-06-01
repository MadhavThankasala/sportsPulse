from utils.db import get_db

sponsors_data = [
    {
        "team": "Argentina",
        "confederation": "CONMEBOL",
        "world_cup_wins": 3,
        "sponsors": [
            {"company": "Adidas", "ticker": "ADS.DE", "type": "kit"},
            {"company": "Mercado Libre", "ticker": "MELI", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Brazil",
        "confederation": "CONMEBOL",
        "world_cup_wins": 5,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "Guaraná Antarctica (Ambev)", "ticker": "ABEV", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "France",
        "confederation": "UEFA",
        "world_cup_wins": 2,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "Danone", "ticker": "DANOY", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "England",
        "confederation": "UEFA",
        "world_cup_wins": 1,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Germany",
        "confederation": "UEFA",
        "world_cup_wins": 4,
        "sponsors": [
            {"company": "Adidas", "ticker": "ADS.DE", "type": "kit"},
            {"company": "Deutsche Telekom", "ticker": "DTEGY", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Spain",
        "confederation": "UEFA",
        "world_cup_wins": 1,
        "sponsors": [
            {"company": "Adidas", "ticker": "ADS.DE", "type": "kit"},
            {"company": "Santander", "ticker": "SAN", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "USA",
        "confederation": "CONCACAF",
        "world_cup_wins": 0,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "Coca-Cola", "ticker": "KO", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Portugal",
        "confederation": "UEFA",
        "world_cup_wins": 0,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Netherlands",
        "confederation": "UEFA",
        "world_cup_wins": 0,
        "sponsors": [
            {"company": "Nike", "ticker": "NKE", "type": "kit"},
            {"company": "ING Group", "ticker": "ING", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
    {
        "team": "Mexico",
        "confederation": "CONCACAF",
        "world_cup_wins": 0,
        "sponsors": [
            {"company": "Adidas", "ticker": "ADS.DE", "type": "kit"},
            {"company": "Coca-Cola", "ticker": "KO", "type": "regional_sponsor"},
            {"company": "Budweiser", "ticker": "BUD", "type": "official_wc_sponsor"},
            {"company": "Visa", "ticker": "V", "type": "official_wc_sponsor"},
        ]
    },
]

# Official World Cup sponsors (apply to all teams)
wc_sponsors = [
    {"company": "Adidas", "ticker": "ADS.DE", "type": "official_partner"},
    {"company": "Coca-Cola", "ticker": "KO", "type": "official_partner"},
    {"company": "Wanda Group", "ticker": None, "type": "official_partner"},
    {"company": "Hyundai/Kia", "ticker": "HYMTF", "type": "official_partner"},
    {"company": "Qatar Airways", "ticker": None, "type": "official_partner"},
    {"company": "Visa", "ticker": "V", "type": "official_partner"},
    {"company": "Budweiser (AB InBev)", "ticker": "BUD", "type": "official_partner"},
]

def seed_database():
    db = get_db()
    
    # Clear existing data
    db.teams.drop()
    db.wc_sponsors.drop()
    
    # Insert teams and sponsors
    db.teams.insert_many(sponsors_data)
    db.wc_sponsors.insert_many(wc_sponsors)
    
    print(f"✅ Seeded {len(sponsors_data)} teams")
    print(f"✅ Seeded {len(wc_sponsors)} World Cup sponsors")
    
    # Create indexes for fast lookup
    db.teams.create_index("team")
    db.teams.create_index("sponsors.ticker")
    print("✅ Indexes created")

def get_sponsors_for_team(team_name):
    db = get_db()
    team = db.teams.find_one({"team": team_name})
    if not team:
        return None
    return team["sponsors"]

if __name__ == "__main__":
    seed_database()
    
    # Test it
    print("\n--- Test Query ---")
    sponsors = get_sponsors_for_team("Argentina")
    print(f"Argentina sponsors: {sponsors}")