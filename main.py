import os
import logging
import random
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup Flask web server agar Render menganggap ini sebagai aplikasi web aktif
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Grok Pump Terminal Bot aktif dan berjalan 24/7 di Render!"

# Mengambil Token dari Environment Variables Render nanti
TOKEN = os.environ.get("TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Simulasi Database Sesuai Aturan Ketat Kamu
checking_pool = [
    {"name": "$PEBU", "dev_hold": 4, "bundles": 12, "rug_history": False},
    {"name": "$NEXA", "dev_hold": 14, "bundles": 5, "rug_history": False},  # Gagal aturan 1 (>10%)
    {"name": "$BLIP", "dev_hold": 2, "bundles": 30, "rug_history": False},  # Gagal aturan 2 (>25%)
    {"name": "$VORX", "dev_hold": 5, "bundles": 10, "rug_history": False},
]

holding_pool = [
    {"name": "$SPIXA", "pnl": "+307%"},
    {"name": "$SOLO", "pnl": "+117%"},
]

done_pool = [
    {"name": "$VOLT", "result": "+$610 (Target Tercapai)"},
    {"name": "$NEON", "result": "-$320 (Bundle Bergerak / Exit)"},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Grok Pump Terminal* aktif di Render!\n\n"
        "Perintah yang tersedia:\n"
        "/papan - Lihat status CHECKING, HOLDING, DONE\n"
        "/scan - Jalankan filter aturan ketat (Dev, Bundles, dll)\n"
        "/update_market - Simulasi pergerakan harga/exit",
        parse_mode="Markdown"
    )

async def papan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🤖 *Grok Bot* · PUMP.FUN TERMINAL · LIVE\n" \
           "aturan ketat aktif (Dev <10%, Bundle <25%)\n\n" \
           "🟡 *CHECKING*\n"
    
    for c in checking_pool:
        status = "→ BELI" if c["dev_hold"] <= 10 and c["bundles"] <= 25 and not c["rug_history"] else "SKIP"
        reason = ""
        if c["dev_hold"] > 10: reason = "(dev >10%)"
        elif c["bundles"] > 25: reason = "(bundles >25%)"
        elif c["rug_history"]: reason = "(rug history)"
        
        text += f"• `{c['name']}` {status} {reason}\n"
    
    text += "\n🟣 *HOLDING*\n"
    if holding_pool:
        for h in holding_pool:
            text += f"• `{h['name']}`  `{h['pnl']}`\n"
    else:
        text += "• (Kosong - Menunggu sinyal masuk)\n"
        
    text += "\n🟢 *DONE*\n"
    for d in done_pool:
        text += f"• `{d['name']}` — {d['result']}\n"
        
    text += f"\n_Scan Time: {datetime.now().strftime('%H:%M:%S')}_"
    await update.message.reply_text(text, parse_mode="Markdown")

async def scan_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global checking_pool, holding_pool
    
    pesan_proses = "🔍 *Memindai koin baru sesuai aturan ketat...*\n\n"
    
    for c in checking_pool:
        if c["dev_hold"] > 10:
            pesan_proses += f"❌ `{c['name']}`: SKIP (Dev hold {c['dev_hold']}% > 10%)\n"
        elif c["bundles"] > 25:
            pesan_proses += f"❌ `{c['name']}`: SKIP (Bundles {c['bundles']}% > 25%)\n"
        elif c["rug_history"]:
            pesan_proses += f"❌ `{c['name']}`: SKIP (Dev riwayat rug)\n"
        else:
            pesan_proses += f"✅ `{c['name']}`: LOLOS! → Masuk HOLDING\n"
            if not any(h['name'] == c['name'] for h in holding_pool):
                holding_pool.append({"name": c['name'], "pnl": "+0%"})
                
    await update.message.reply_text(pesan_proses, parse_mode="Markdown")

async def update_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global holding_pool, done_pool
    
    if not holding_pool:
        await update.message.reply_text("⚠️ Tidak ada posisi aktif di HOLDING saat ini.")
        return

    update_log = "⚡ *Evaluasi Sinyal Keluar & Target:*\n"
    sisa_holding = []
    
    for h in holding_pool:
        event_trigger = random.choice(["aman", "bundle_move", "target_hit"])
        
        if event_trigger == "bundle_move":
            update_log += f"🚨 `{h['name']}`: Bundle bergerak! Keluar sekarang (Aturan 4).\n"
            done_pool.append({"name": h['name'], "result": "Exit (Bundle Bergerak)"})
        elif event_trigger == "target_hit":
            update_log += f"🎯 `{h['name']}`: Capai target profit! Tutup posisi (Aturan 5).\n"
            done_pool.append({"name": h['name'], "result": "+$450 (Target Tercapai)"})
        else:
            change = random.randint(5, 35)
            current = int(h["pnl"].replace("%", "").replace("+", ""))
            new = current + change
            h["pnl"] = f"+{new}%"
            sisa_holding.append(h)
            update_log += f"📈 `{h['name']}` holding aman. PNL: `+{new}%`\n"
            
    holding_pool = sisa_holding
    await update.message.reply_text(update_log, parse_mode="Markdown")

def run_telegram_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("papan", papan))
    app.add_handler(CommandHandler("scan", scan_market))
    app.add_handler(CommandHandler("update_market", update_market))
    
    print("Bot Telegram siap berjalan via Polling...")
    app.run_polling()

if __name__ == "__main__":
    import threading
    # Jalankan Telegram bot di background thread
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Jalankan Flask server di port Render
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)
