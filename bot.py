import os
import json
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==============================
# Получаем переменные окружения
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
# ==============================

# Загружаем credentials из переменной окружения
credentials_dict = json.loads(GOOGLE_CREDENTIALS)
gc = gspread.service_account_from_dict(credentials_dict)
sheet = gc.open_by_key(SHEET_ID).sheet1

# -----------------------------
def get_data():
    return sheet.get_all_records()

def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Моя инфа", callback_data="me")],
        [InlineKeyboardButton("📋 Все", callback_data="all")],
        [InlineKeyboardButton("🔍 Кто я", callback_data="me")]
    ])

def format_user(row):
    return f"👤 {row['name']}\n🏷 Звание: {row['title']}\n🔢 Кол-во букв: {row['letters']}"
# -----------------------------

# -----------------------------
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    data = get_data()

    for row in data:
        if row["tg_name"] == username:
            await update.message.reply_text(
                format_user(row),
                reply_markup=build_keyboard()
            )
            return

    await update.message.reply_text(
        "Тебя нет в таблице 😢",
        reply_markup=build_keyboard()
    )

async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /who @username")
        return

    username = context.args[0].replace("@", "")
    data = get_data()

    for row in data:
        if row["tg_name"] == username:
            await update.message.reply_text(
                format_user(row),
                reply_markup=build_keyboard()
            )
            return

    await update.message.reply_text(
        "Пользователь не найден",
        reply_markup=build_keyboard()
    )

async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_data()
    text = "📋 Список званий:\n\n"
    for row in data:
        text += f"{row['name']} — {row['title']} ({row['letters']})\n"

    await update.message.reply_text(
        text,
        reply_markup=build_keyboard()
    )
# -----------------------------

# -----------------------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = get_data()
    username = query.from_user.username

    if query.data in ["me"]:
        for row in data:
            if row["tg_name"] == username:
                await query.message.edit_text(
                    format_user(row),
                    reply_markup=build_keyboard()
                )
                return
        await query.message.edit_text(
            "Тебя нет в таблице 😢",
            reply_markup=build_keyboard()
        )

    elif query.data == "all":
        text = "📋 Список званий:\n\n"
        for row in data:
            text += f"{row['name']} — {row['title']} ({row['letters']})\n"
        await query.message.edit_text(
            text,
            reply_markup=build_keyboard()
        )
# -----------------------------

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("me", me))
app.add_handler(CommandHandler("who", who))
app.add_handler(CommandHandler("all", all_users))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()
