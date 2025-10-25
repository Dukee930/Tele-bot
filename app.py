from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==== CONFIG ====
BOT_TOKEN = "8278690206:AAFc0ko_BIzC4WbK1gQgnyJa37jrzmpNnTo"
OWNER_USERNAME = "@humblesports"  # your Telegram handle

# ==== MENU SETUP ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💼 Hosting Plans", callback_data="plans")],
        [InlineKeyboardButton("🧱 Add-ons", callback_data="addons")],
        [InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌐 **Welcome to ɦʊʍɮʟɛ ɦօʂȶֆ**\n\n"
        "Your premium bulletproof and secured hosting solution.\n\n"
        "Choose an option below 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==== CALLBACK HANDLERS ====

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "plans":
        keyboard = [
            [InlineKeyboardButton("🔥 1-Month - $50", callback_data="plan_1")],
            [InlineKeyboardButton("⚡️ 3-Month - $120", callback_data="plan_3")],
            [InlineKeyboardButton("🚀 6-Month - $230", callback_data="plan_6")],
            [InlineKeyboardButton("🌐 12-Month - $400", callback_data="plan_12")],
            [InlineKeyboardButton("⬅ Back to Menu", callback_data="home")]
        ]
        await query.edit_message_text(
            "**Hosting Plans** 💼\n\nChoose your preferred plan:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "addons":
        keyboard = [
            [InlineKeyboardButton("🧩 Bulletproof Aged Domains", callback_data="addon_domains")],
            [InlineKeyboardButton("🔐 Private Reverse Proxy", callback_data="addon_proxy")],
            [InlineKeyboardButton("🧱 Custom Server Setup", callback_data="addon_custom")],
            [InlineKeyboardButton("⬅ Back to Menu", callback_data="home")]
        ]
        await query.edit_message_text(
            "**Add-ons** 🧱\n\nBoost your hosting with powerful extras:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data.startswith("plan_"):
        plans = {
            "plan_1": ("🔥 1-Month Plan", "$50"),
            "plan_3": ("⚡️ 3-Month Plan", "$120"),
            "plan_6": ("🚀 6-Month Plan", "$230"),
            "plan_12": ("🌐 12-Month Plan", "$400")
        }
        plan_name, price = plans[query.data]
        msg = f"**{plan_name} — {price}**\n\n✅ Premium Masked IP\n✅ Bulletproof Hosting\n✅ Secured Server\n✅ 24/7 Support\n\nTo purchase, contact {OWNER_USERNAME}"
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif query.data.startswith("addon_"):
        addons = {
            "addon_domains": "🧩 **Bulletproof Aged Domains**\nHigh-trust aged domains for your hosting setup.\n\nContact {OWNER_USERNAME} to purchase.",
            "addon_proxy": "🔐 **Private Reverse Proxy**\nProtect your network layer with advanced reverse proxy.\n\nContact {OWNER_USERNAME}.",
            "addon_custom": "🧱 **Custom Server Setup**\nWe’ll build your own bulletproof infrastructure from scratch.\n\nContact {OWNER_USERNAME}."
        }
        text = addons[query.data].format(OWNER_USERNAME=OWNER_USERNAME)
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "home":
        await start(update, context)

# ==== MAIN ====

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
