import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================== CONFIG ==================
TELEGRAM_TOKEN = "8276928278:AAHCKZ08sgDYSAlJq96j3bX-AsuoCKyFtp4"
ODDS_API_KEY = "1e7ef6e10bd168f169e4863e0fad92fb"

# Λίστα leagues (μπορείς να προσθέτεις)
LEAGUES = {
    "premier": "soccer_epl",
    "champions": "soccer_champions_league",
    "bundesliga": "soccer_germany_bundesliga",
    "seriea": "soccer_italy_serie_a",
    "laliga": "soccer_spain_la_liga",
    "ligue1": "soccer_france_ligue_one",
    "superleague": "soccer_greece_super_league",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **AI Betting Bot** - Free Edition\n\n"
        "🔥 /predictions → Γενικά προγνωστικά\n"
        "🏆 /premier | /champions | /bundesliga | /seriea | /laliga | /ligue1 | /superleague\n\n"
        "🎯 Αποδόσεις: **1.70 - 2.60**\n"
        "📊 Στόχος σιγουριάς: **≥65%**"
    )

def calculate_confidence(odds: float) -> int:
    """Απλή αλλά βελτιωμένη heuristic για free version"""
    if odds <= 1.85:
        return 72
    elif odds <= 2.10:
        return 68
    elif odds <= 2.40:
        return 65
    else:
        return 62

async def send_predictions(update: Update, context: ContextTypes.DEFAULT_TYPE, league_key: str = "soccer_epl"):
    url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    
    try:
        response = requests.get(url, timeout=25)
        response.raise_for_status()
        events = response.json()

        results = []
        for event in events[:25]:   # Περιορισμός για απόδοση
            if not event.get('bookmakers'):
                continue
                
            outcomes = event['bookmakers'][0]['markets'][0]['outcomes']
            home_team = event.get('home_team')
            away_team = event.get('away_team')

            for team, odds in [(home_team, next((o['price'] for o in outcomes if o['name'] == home_team), None)),
                              (away_team, next((o['price'] for o in outcomes if o['name'] == away_team), None))]:
                
                if odds and 1.70 <= odds <= 2.60:
                    confidence = calculate_confidence(odds)
                    if confidence >= 65:
                        results.append(
                            f"**{home_team} — {away_team}**\n"
                            f"→ **{team}** @ **{odds}** (Σιγουριά: **{confidence}%**)"
                        )

        if results:
            header = f"🔥 Προγνωστικά - {league_key.replace('soccer_', '').replace('_', ' ').upper()}\n\n"
            await update.message.reply_text(header + "\n\n".join(results[:10]))
        else:
            await update.message.reply_text("Δεν βρέθηκαν προγνωστικά που πληρούν τα κριτήρια αυτή τη στιγμή.")

    except Exception as e:
        await update.message.reply_text(f"❌ Σφάλμα σύνδεσης: {str(e)}")

# ================== HANDLERS ==================
async def general_predictions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_predictions(update, context, "soccer_epl")

# Dynamic handlers για όλα τα leagues
for cmd, key in LEAGUES.items():
    async def make_handler(league_key):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await send_predictions(update, context, league_key)
        return handler
    
    # Θα τα προσθέσουμε παρακάτω

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predictions", general_predictions))
    
    # Προσθήκη όλων των leagues
    for command, league_key in LEAGUES.items():
        async def create_handler(lkey):
            async def handler(u, c):
                await send_predictions(u, c, lkey)
            return handler
        handler_func = create_handler(league_key)
        app.add_handler(CommandHandler(command, handler_func))

    print("🚀 AI Betting Bot τρέχει... (Free & Ready for GitHub)")
    app.run_polling()
