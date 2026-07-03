import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === ΒΑΛΕ ΕΔΩ ΤΑ KEYS ΣΟΥ (ή καλύτερα μέσω environment variables) ===
TELEGRAM_TOKEN = "8276928278:AAHCKZ08sgDYSAlJq96j3bX-AsuoCKyFtp4"
ODDS_API_KEY = "1e7ef6e10bd168f169e4863e0fad92fb"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Καλώς ήρθες στον AI Betting Bot!**\n\n"
        "🔍 /predictions → Προγνωστικά pre-game (1.70-2.60)\n"
        "🎯 Στόχος: Value bets με καλή αξία\n"
        "⚠️ Παίξε υπεύθυνα!"
    )

async def predictions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        events = resp.json()

        results = []
        for event in events[:20]:
            if not event.get('bookmakers'):
                continue
                
            bookie = event['bookmakers'][0]
            market = bookie['markets'][0]['outcomes']
            
            home_team = event.get('home_team')
            away_team = event.get('away_team')
            
            home_odds = next((o['price'] for o in market if o['name'] == home_team), None)
            draw_odds = next((o['price'] for o in market if o['name'] == "Draw"), None)
            away_odds = next((o['price'] for o in market if o['name'] == away_team), None)

            # Φίλτρο αποδόσεων + value logic
            for team, odds in [(home_team, home_odds), (away_team, away_odds)]:
                if odds and 1.70 <= odds <= 2.60:
                    implied = round((1 / odds) * 100, 1)
                    if implied <= 58:  # Value filter (μπορεί να βελτιωθεί με ML)
                        results.append(
                            f"**{home_team} - {away_team}**\n"
                            f"→ **{team}** @ **{odds}** (Implied prob: {implied}%)"
                        )

        if results:
            msg = "\n\n".join(results[:10])
            await update.message.reply_text(f"🔥 **Προτεινόμενα Προγνωστικά**\n\n{msg}\n\n📊 The Odds API data")
        else:
            await update.message.reply_text("Δεν βρέθηκαν value bets αυτή τη στιγμή στις κύριες αγορές. Δοκίμασε αργότερα ή άλλο πρωτάθλημα.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Σφάλμα: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predictions", predictions))
    
    print("🚀 Bot τρέχει... (Ctrl+C για stop)")
    app.run_polling()
