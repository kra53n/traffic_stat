import io

from telegram import (
    Update,
    InputMediaPhoto,
    BotCommand,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import statistic
import db
import plot


async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("health", "check bot health"),
        BotCommand("stat", "statistic figures"),
        BotCommand("users", "users list"),
    ])


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check bot health
    """
    await update.message.reply_text(f"Bot is alive, {update.effective_user.first_name}") # type: ignore


async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Give user the statistic
    """
    # get args, skip command
    args = update.message.text.split()[1:] # type: ignore
    if not args:
        return await update.message.reply_text("nicknames should be provided") # type: ignore
    
    # get data for the plot
    raw_records: list[list] = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nickname: dict[str, list] = statistic.group_by("nickname", statistic_records)

    # exclude nicknames that not provided as arguments in command
    if args[0] != "all":
        grouped_statistic_by_nickname_keys = tuple(grouped_statistic_by_nickname.keys())
        for nickname in grouped_statistic_by_nickname_keys:
            if nickname not in args:
                grouped_statistic_by_nickname.pop(nickname)

    # build figures
    fig1 = io.BytesIO()
    fig2 = io.BytesIO()
    plot.alltime_figure(grouped_statistic_by_nickname, fig1)
    plot.diff_figure(grouped_statistic_by_nickname, fig2)

    media_group = (
        InputMediaPhoto(fig1.getvalue()),
        InputMediaPhoto(fig2.getvalue()),
    )
    await update.message.reply_media_group(media_group) # type: ignore
    
    fig1.close()
    fig2.close()


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return users list
    """
    raw_records = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nickname: dict[str, list] = statistic.group_by("nickname", statistic_records)
    await update.message.reply_text("\r\n".join(grouped_statistic_by_nickname.keys())) # type: ignore


def run(tg_bot_token: str):
    app = ApplicationBuilder().token(tg_bot_token).post_init(post_init).build()
    app.add_handlers(
        (
            CommandHandler("health", health),
            CommandHandler("stat", stat),
            CommandHandler("users", users),
        )
    )
    app.run_polling()