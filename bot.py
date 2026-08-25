import os
import random
import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

DB = "wonder_cs2.db"

CASES = [
    ("🔫 Glock-18 | Fade", 500),
    ("🔫 AK-47 | Redline", 300),
    ("🔫 AWP | Asiimov", 800),
    ("🔫 M4A1-S | Printstream", 1000),
    ("🔫 Karambit | Doppler", 2500),
]


def db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 1000
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skin TEXT,
            price INTEGER
        )
    """)
    conn.commit()
    return conn


def add_user(user):
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username or user.first_name)
    )
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)

    keyboard = [
        [
            InlineKeyboardButton("🎁 Case ochish", callback_data="case"),
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
        ],
        [
            InlineKeyboardButton("🎒 Inventar", callback_data="inventory"),
        ],
    ]

    await update.message.reply_text(
        f"🔥 *Wonder CS2* ga xush kelibsiz, {user.first_name}!\n\n"
        "🎁 Case oching va tasodifiy CS2 skin oling.\n"
        "💰 Boshlang‘ich balans: 1000 coin",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    add_user(query.from_user)

    if query.data == "profile":
        conn = db()
        user = conn.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()
        conn.close()

        await query.edit_message_text(
            f"👤 *Profil*\n\n"
            f"ID: `{user_id}`\n"
            f"💰 Balans: *{user[0]} coin*",
            parse_mode="Markdown"
        )

    elif query.data == "case":
        conn = db()
        user = conn.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

        if user[0] < 100:
            conn.close()
            await query.edit_message_text(
                "❌ Case ochish uchun 100 coin kerak."
            )
            return

        skin, price = random.choice(CASES)

        conn.execute(
            "UPDATE users SET balance = balance - 100 WHERE user_id=?",
            (user_id,)
        )
        conn.execute(
            "INSERT INTO inventory (user_id, skin, price) VALUES (?, ?, ?)",
            (user_id, skin, price)
        )
        conn.commit()
        conn.close()

        await query.edit_message_text(
            f"🎁 *CASE OCHILDI!*\n\n"
            f"🎉 Sizga tushdi:\n"
            f"*{skin}*\n\n"
            f"💎 Taxminiy qiymat: {price} coin\n"
            f"💰 Case narxi: 100 coin",
            parse_mode="Markdown"
        )

    elif query.data == "inventory":
        conn = db()
        items = conn.execute(
            "SELECT skin, price FROM inventory WHERE user_id=?",
            (user_id,)
        ).fetchall()
        conn.close()

        if not items:
            await query.edit_message_text(
                "🎒 Inventaringiz hozircha bo‘sh."
            )
            return

        text = "🎒 *Sizning inventaringiz:*\n\n"

        for i, (skin, price) in enumerate(items, 1):
            text += f"{i}. {skin} — 💎 {price} coin\n"

        await query.edit_message_text(
            text,
            parse_mode="Markdown"
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buttons))

    application.run_polling()


if __name__ == "__main__":
    main()
