# bot.py

# === IMPORT LIBRARIES ===
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)
from dotenv import load_dotenv
import os
import re

# === LOAD ENVIRONMENT VARIABLES ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === CONFIGURATION ===
REQUIRED_GROUPS = [
    {"id": -1002385200153, "title": "Investment Group", "link": "https://t.me/+riOvrNP4SKQ2MWQ8"}
]

LANGUAGE, NAME, PHONE, COUNTRY, EMAIL = range(5)

# === /START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')],
        [InlineKeyboardButton("Français 🇫🇷", callback_data='lang_fr')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please select your language / Veuillez sélectionner votre langue:", reply_markup=reply_markup)
    return LANGUAGE

# === HANDLE LANGUAGE SELECTION ===
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["lang"] = query.data
    await query.edit_message_text("What is your full name?" if query.data == "lang_en" else "Quel est votre nom complet ?")
    return NAME

# === HANDLE NAME ===
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Share phone number", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

    await update.message.reply_text("Please share your phone number:" if context.user_data["lang"] == "lang_en" else "Veuillez partager votre numéro de téléphone :", reply_markup=contact_keyboard)
    return PHONE

# === HANDLE PHONE ===
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
    context.user_data["phone"] = phone_number

    await update.message.reply_text("What country are you from?" if context.user_data["lang"] == "lang_en" else "De quel pays venez-vous ?", reply_markup=ReplyKeyboardRemove())
    return COUNTRY

# === HANDLE COUNTRY ===
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    await update.message.reply_text("📧 Please enter your Gmail address:" if context.user_data["lang"] == "lang_en" else "📧 Veuillez entrer votre adresse Gmail :")
    return EMAIL

# === HANDLE EMAIL ===
def is_valid_gmail(email):
    """
    Check if the provided email is a valid Gmail address.
    """
    return re.match(r"^[a-zA-Z0-9_.+-]+@gmail\.com$", email)


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if not is_valid_gmail(email):
        await update.message.reply_text("❌ Invalid Gmail address. Please enter a valid Gmail (e.g. yourname@gmail.com):" if context.user_data["lang"] == "lang_en" else "❌ Adresse Gmail invalide. Veuillez entrer une adresse Gmail valide :")
        return EMAIL

    context.user_data["email"] = email

    user = context.user_data
    summary = (
        f"✅ Details received:\n"
        f"👤 Name: {user['name']}\n"
        f"📞 Phone: {user['phone']}\n"
        f"🌍 Country: {user['country']}\n"
        f"📧 Email: {user['email']}\n\n"
        f"Checking if you joined the groups..."
    )
    await update.message.reply_text(summary)
    return await check_user_membership(update, context)

# === CHECK GROUP MEMBERSHIP ===
async def is_user_in_group(bot, group_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=group_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def check_user_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot
    not_joined = []

    for group in REQUIRED_GROUPS:
        if not await is_user_in_group(bot, group["id"], user_id):
            not_joined.append(group)

    if not_joined:
        buttons = [[InlineKeyboardButton(f"Join {g['title']}", url=g['link'])] for g in not_joined]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("❗ Please join the group(s) below to continue:", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("✅ You're verified!")
        await menu(update, context)
        return ConversationHandler.END

# === MENU FUNCTION ===
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.user_data.get("lang", "lang_en")

    if user_lang == "lang_fr":
        keyboard = [
            ["📥 Dépôt", "💰 Investir"],
            ["📊 Solde", "💸 Retrait"],
            ["ℹ️ Aide"]
        ]
        text = "📋 Menu principal :"
    else:
        keyboard = [
            ["📥 Deposit", "💰 Invest"],
            ["📊 Balance", "💸 Withdraw"],
            ["ℹ️ Help"]
        ]
        text = "📋 Main Menu:"

    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# === MENU ACTIONS ===
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 Please wait while we initiate your MTN/Orange deposit...")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💸 Withdrawals are processed within 24 hours after approval.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Your current balance is: ₦0.00")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ For support, contact our admin @YourSupportHandle or visit FAQ.")

async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 To invest, please use the deposit option first.")

# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(handle_language)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, get_phone)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📥 Deposit$|^📥 Dépôt$"), deposit))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💰 Invest$|^💰 Investir$"), invest))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💸 Withdraw$|^💸 Retrait$"), withdraw))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📊 Balance$|^📊 Solde$"), balance))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ℹ️ Help$|^ℹ️ Aide$"), help_command))

    print("Bot is running...")
    app.run_polling()

# === RUN ===
if __name__ == "__main__":
    main()