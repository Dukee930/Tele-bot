import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==== CONFIG ====
BOT_TOKEN = "8278690206:AAFc0ko_BIzC4WbK1gQgnyJa37jrzmpNnTo"  # <- keep secret, replace if token was exposed
OWNER_USERNAME = "@humblesports"              # your telegram handle (notification target)
BTC_ADDRESS = "bc1qy3h2gaqqdccw8puv6x8vtck4ynsgwv6ef5qzcp"

# per-user pending orders stored here: user_id -> dict with order info
# Example entry:
# pending_orders[user_id] = {
#     "plan_key": "plan_1",
#     "plan_name": "1-Month Plan",
#     "price": "$50",
#     "created_at": datetime.utcnow(),
#     "deadline": datetime.utcnow() + timedelta(minutes=5),
#     "timeout_task": asyncio.Task(...)
# }
pending_orders = {}

# ==== UTILITIES ====
def build_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Hosting Plans", callback_data="plans")],
        [InlineKeyboardButton("🧱 Add-ons", callback_data="addons")],
        [InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
    ])

def build_plans_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 1-Month - $50", callback_data="plan_1")],
        [InlineKeyboardButton("⚡️ 3-Month - $120", callback_data="plan_3")],
        [InlineKeyboardButton("🚀 6-Month - $230", callback_data="plan_6")],
        [InlineKeyboardButton("🌐 12-Month - $400", callback_data="plan_12")],
        [InlineKeyboardButton("⬅ Back", callback_data="home")]
    ])

def build_addons_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧩 Bulletproof Aged Domains", callback_data="addon_domains")],
        [InlineKeyboardButton("🔐 Private Reverse Proxy", callback_data="addon_proxy")],
        [InlineKeyboardButton("🧱 Custom Server Setup", callback_data="addon_custom")],
        [InlineKeyboardButton("⬅ Back", callback_data="home")]
    ])

def plan_details(plan_key):
    plans = {
        "plan_1": ("🔥 1-Month Plan", "$50"),
        "plan_3": ("⚡️ 3-Month Plan", "$120"),
        "plan_6": ("🚀 6-Month Plan", "$230"),
        "plan_12": ("🌐 12-Month Plan", "$400"),
    }
    return plans.get(plan_key)

# ==== HANDLERS ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🌐 *ɦʊʍɮʟɛ ɦօʂȶֆ — Elite Bulletproof Hosting*\n\n"
        "We provide premium, privacy-focused hosting with fast setup and 24/7 support.\n"
        "Browse plans below and tap *Make Purchase* to begin — payments are handled via BTC. "
        "After you submit your tx hash, our team will verify and activate your order (max wait time 30 mins).\n\n"
        "Choose an option below 👇"
    )
    await update.message.reply_text(welcome, reply_markup=build_main_keyboard(), parse_mode="Markdown")

async def back_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Allows user to return to main menu from anywhere
    await update.message.reply_text("Returned to main menu.", reply_markup=build_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Home / main menu
    if data == "home":
        await query.edit_message_text("Main menu:", reply_markup=build_main_keyboard())

    # Plans list
    elif data == "plans":
        await query.edit_message_text("**Hosting Plans** 💼\n\nChoose your preferred plan:", reply_markup=build_plans_keyboard(), parse_mode="Markdown")

    # Addons list
    elif data == "addons":
        await query.edit_message_text("**Add-ons** 🧱\n\nBoost your hosting with powerful extras:", reply_markup=build_addons_keyboard(), parse_mode="Markdown")

    # Selected a specific plan -> show details + Make Purchase button
    elif data.startswith("plan_"):
        pd = plan_details(data)
        if not pd:
            await query.edit_message_text("Unknown plan.")
            return
        plan_name, price = pd
        text = (
            f"*{plan_name} — {price}*\n\n"
            "✅ Premium Masked IP\n✅ Bulletproof Hosting\n✅ Secured Server\n✅ 24/7 Support\n\n"
            f"To purchase, tap *Make Purchase* below. You will have *5 minutes* to send BTC to the address provided.\n\n"
            f"_Note: We will manually verify your payment. After submitting your TX hash, allow up to 30 minutes for order delivery._"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Make Purchase", callback_data=f"make_{data}")],
            [InlineKeyboardButton("⬅ Back", callback_data="plans")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
        ])
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    # Selected addon -> show details (similar to plan)
    elif data.startswith("addon_"):
        addon_map = {
            "addon_domains": ("🧩 Bulletproof Aged Domains", "$90"),
            "addon_proxy": ("🔐 Private Reverse Proxy", "$60"),
            "addon_custom": ("🧱 Custom Server Setup", "$150"),
        }
        name, price = addon_map.get(data, ("Addon", "Contact"))
        text = f"*{name} — {price}*\n\nContact {OWNER_USERNAME} to purchase.\n\n⬅ Back to Add-ons."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="addons"), InlineKeyboardButton("🏠 Main Menu", callback_data="home")]])
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    # Make purchase flow: create pending order, start timer, show address + controls
    elif data.startswith("make_"):
        _, plan_key = data.split("_", 1)
        pd = plan_details(plan_key)
        if not pd:
            await query.edit_message_text("Unknown plan.")
            return
        plan_name, price = pd
        user_id = query.from_user.id

        # If user already has a pending order, notify
        if user_id in pending_orders:
            await query.edit_message_text("You already have a pending order. Please finish it or wait for it to expire.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⌛ View Pending Order", callback_data="view_pending")], [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]]))
            return

        # Create pending order
        now = datetime.utcnow()
        deadline = now + timedelta(minutes=5)
        pending_orders[user_id] = {
            "plan_key": plan_key,
            "plan_name": plan_name,
            "price": price,
            "created_at": now,
            "deadline": deadline,
            "tx_hash": None,
        }

        # create timeout task
        loop = asyncio.get_running_loop()
        task = loop.create_task(order_timeout_handler(user_id, context))
        pending_orders[user_id]["timeout_task"] = task

        # Show payment instructions + buttons
        text = (
            f"*Payment instructions for {plan_name} — {price}*\n\n"
            "1) You have *5 minutes* to send the BTC payment to the address below.\n"
            "2) Optionally press *Generate 1-time address* (for formality) — it will display the address below.\n"
            "3) After sending, tap *I've Paid* and paste your transaction hash.\n\n"
            f"*BTC Address:* `{BTC_ADDRESS}`\n\n"
            "*Maximum wait time for order activation: 30 minutes.*"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Generate 1-time address", callback_data="gen_addr")],
            [InlineKeyboardButton("✅ I've Paid (Submit TX Hash)", callback_data="confirm_paid")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")],
        ])
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    elif data == "gen_addr":
        # For formality, we show the same BTC address (no generation)
        await query.edit_message_text(f"🔒 One-time address (for formality):\n`{BTC_ADDRESS}`\n\nTap *I've Paid* after you send payment.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I've Paid (Submit TX Hash)", callback_data="confirm_paid")],[InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]))

    elif data == "confirm_paid":
        user_id = query.from_user.id
        if user_id not in pending_orders:
            await query.edit_message_text("You don't have a pending order. Please choose a plan first.", reply_markup=build_main_keyboard())
            return
        # Ask user to send tx hash — switch to listening mode by telling them to paste tx hash
        await query.edit_message_text("Please *paste your transaction hash* (tx id) now. Example: `txhash123...`", parse_mode="Markdown")

        # set a flag that this user is expected to send tx hash (we'll check in message handler)
        context.user_data["expecting_tx"] = True

    elif data == "cancel_order":
        user_id = query.from_user.id
        if user_id in pending_orders:
            # cancel associated timeout task
            task = pending_orders[user_id].get("timeout_task")
            if task and not task.done():
                task.cancel()
            del pending_orders[user_id]
            await query.edit_message_text("Your pending order has been cancelled. Returned to main menu.", reply_markup=build_main_keyboard())
        else:
            await query.edit_message_text("No pending order found.", reply_markup=build_main_keyboard())

    elif data == "view_pending":
        user_id = query.from_user.id
        o = pending_orders.get(user_id)
        if not o:
            await query.edit_message_text("No pending order.", reply_markup=build_main_keyboard())
            return
        remaining = int((o["deadline"] - datetime.utcnow()).total_seconds() // 1)
        await query.edit_message_text(f"Pending: {o['plan_name']} — {o['price']}\nDeadline in ~{remaining} seconds.\nBTC: `{BTC_ADDRESS}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I've Paid (Submit TX Hash)", callback_data="confirm_paid"), InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]))

# message handler to capture tx hash input
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # If user is expected to send tx hash
    expecting = context.user_data.get("expecting_tx", False)
    if expecting and user_id in pending_orders:
        # treat the message as tx hash
        tx_hash = text.split()[0]  # first token
        pending_orders[user_id]["tx_hash"] = tx_hash

        # cancel timeout task
        task = pending_orders[user_id].get("timeout_task")
        if task and not task.done():
            task.cancel()

        # send confirmation to buyer
        await update.message.reply_text("Thanks — your transaction hash has been received. We will verify it and activate your order. Maximum wait time: 30 minutes.\n\nOrder details sent to admin.", reply_markup=build_main_keyboard())

        # notify owner/admin with details
        o = pending_orders[user_id]
        buyer = f"{update.effective_user.full_name} (@{update.effective_user.username})" if update.effective_user.username else update.effective_user.full_name
        notify_text = (
            f"📥 *New Order Submission*\n\n"
            f"*Buyer:* {buyer}\n"
            f"*Product:* {o['plan_name']} — {o['price']}\n"
            f"*TX Hash:* `{tx_hash}`\n"
            f"*BTC Address used:* `{BTC_ADDRESS}`\n"
            f"*Submitted at:* {datetime.utcnow().isoformat()} UTC\n\n"
            "Please verify the payment on-chain and activate the order."
        )
        # send to owner
        try:
            await context.bot.send_message(chat_id=OWNER_USERNAME, text=notify_text, parse_mode="Markdown")
        except Exception as e:
            # if sending to username fails, try sending to chat id if you set it
            print("Failed to notify owner by username:", e)

        # keep order for records (you can persist as needed)
        # remove from pending
        del pending_orders[user_id]
        context.user_data["expecting_tx"] = False
        return

    # normal fallback
    await update.message.reply_text("I didn't understand that. Use the menu or /back to return.", reply_markup=build_main_keyboard())

# timeout handler
async def order_timeout_handler(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        # sleep until deadline
        while True:
            if user_id not in pending_orders:
                return
            now = datetime.utcnow()
            deadline = pending_orders[user_id]["deadline"]
            seconds = (deadline - now).total_seconds()
            if seconds <= 0:
                break
            # sleep either remaining seconds or a chunk
            await asyncio.sleep(min(5, seconds))
        # timeout reached
        if user_id in pending_orders:
            try:
                await context.bot.send_message(chat_id=user_id, text="⏰ Your payment window (5 minutes) has expired. The pending order has been cancelled. Please create a new order if you still want to buy.", reply_markup=build_main_keyboard())
            except Exception:
                pass
            # remove pending order
            del pending_orders[user_id]
    except asyncio.CancelledError:
        # task cancelled because user submitted tx hash
        return

# ==== MAIN ====
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("back", back_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
