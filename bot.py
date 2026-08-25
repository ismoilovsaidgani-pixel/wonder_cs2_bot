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
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "wonder-secret-2026")

DB = "wonder_cs2.db"

CASES = [
    ("🔫 Glock-18 | Fade", 500),
    ("🔫 AK-47 | Redline", 300),
    ("🔫 AWP | Asiimov", 800),
    ("🔫 M4A1-S | Printstream", 1000),
    ("🔪 Karambit | Doppler", 2500),
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
        """
        INSERT OR IGNORE INTO users
        (user_id, username, balance)
        VALUES (?, ?, 1000)
        """,
        (
            user.id,
            user.username or user.first_name
        )
    )

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 Case ochish",
                callback_data="case"
            ),
            InlineKeyboardButton(
                "👤 Profil",
                callback_data="profile"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎒 Inventar",
                callback_data="inventory"
            ),
        ],
    ]

    await update.message.reply_text(
        f"🔥 *Wonder CS2* ga xush kelibsiz, "
        f"{user.first_name}!\n\n"
        "🎁 Case oching va tasodifiy skin oling.\n"
        "💰 Boshlang‘ich balans: *1000 coin*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    add_user(user)

    if query.data == "profile":

        conn = db()

        result = conn.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        conn.close()

        balance = result[0] if result else 0

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            f"👤 *PROFIL*\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 Balans: *{balance} coin*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "case":

        conn = db()

        result = conn.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        balance = result[0]

        if balance < 100:
            conn.close()

            await query.edit_message_text(
                "❌ Case ochish uchun *100 coin* kerak.",
                parse_mode="Markdown"
            )
            return

        skin, price = random.choice(CASES)

        conn.execute(
            """
            UPDATE users
            SET balance = balance - 100
            WHERE user_id = ?
            """,
            (user_id,)
        )

        conn.execute(
            """
            INSERT INTO inventory
            (user_id, skin, price)
            VALUES (?, ?, ?)
            """,
            (user_id, skin, price)
        )

        conn.commit()
        conn.close()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎁 Yana ochish",
                    callback_data="case"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎒 Inventar",
                    callback_data="inventory"
                )
            ],
        ]

        await query.edit_message_text(
            f"🎁 *CASE OCHILDI!*\n\n"
            f"🎉 Sizga tushdi:\n"
            f"*{skin}*\n\n"
            f"💎 Qiymati: *{price} coin*\n"
            f"💰 Case narxi: *100 coin*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "inventory":

        conn = db()

        items = conn.execute(
            """
            SELECT skin, price
            FROM inventory
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        if not items:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "⬅️ Orqaga",
                        callback_data="home"
                    )
                ]
            ]

            await query.edit_message_text(
                "🎒 *INVENTAR*\n\n"
                "Hozircha inventaringiz bo‘sh.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        text = "🎒 *SIZNING INVENTARINGIZ*\n\n"

        for number, (skin, price) in enumerate(items, 1):
            text += (
                f"{number}. {skin}\n"
                f"   💎 {price} coin\n\n"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎁 Case ochish",
                    callback_data="case"
                ),
                InlineKeyboardButton(
                    "👤 Profil",
                    callback_data="profile"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎒 Inventar",
                    callback_data="inventory"
                ),
            ],
        ]

        await query.edit_message_text(
            "🔥 *Wonder CS2*\n\n"
            "Kerakli bo‘limni tanlang:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi!"
        )

    if not PUBLIC_URL:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL topilmadi!"
        )

    port = int(
        os.environ.get("PORT", "10000")
    )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(buttons)
    )

    webhook_path = "wonder-cs2-webhook"

    webhook_url = (
        f"{PUBLIC_URL}/{webhook_path}"
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
