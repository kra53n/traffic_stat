import dataclasses
import typing
import io

from loguru import logger
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


@dataclasses.dataclass
class UserStorage:
    """
    Dataclass for storing some user telegram stuff for better telegram interaction.
    """
    last_stat_args: typing.Optional[list["str"]] = None


class Storage(dict):
    def __getitem__(self, key: int) -> UserStorage:
        if key not in self:
            self[key] = UserStorage()
        return super().__getitem__(key)


storage = Storage()


def run(tg_bot_token: str):
    logger.info("run telegram bot")
    app = ApplicationBuilder().token(tg_bot_token).post_init(post_init).build()
    app.add_handlers(
        (
            CommandHandler("start", start),
            CommandHandler("health", health),
            CommandHandler("stat", stat),
            CommandHandler("users", users),
        )
    )
    app.run_polling()


async def post_init(app: Application):
    logger.trace("add command commands")
    await app.bot.set_my_commands([
        BotCommand("start", "start message"),
        BotCommand("health", "check bot health"),
        BotCommand("stat", "statistic figures"),
        BotCommand("users", "users list"),
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prints start message
    """
    message = """Show statistic of proxy usage

    /start - start message i guess

    /health - send message if bot is alive

    /users - send message with proxy users

    /stat - send message with figures
        /stat user1 - send figures with user1
        /stat user1 user2 - send figures with user1 and user2"""
    logger.info("start command called")
    await update.message.reply_text(message) # type: ignore


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check bot health
    """
    logger.info("health called")
    await update.message.reply_text(f"Bot is alive, {update.effective_user.first_name}") # type: ignore


async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Give user the statistic
    """
    logger.info("stat command called")

    # get args, skip command
    args = update.message.text.split()[1:] # type: ignore
    logger.info(f"args: {args}")

    user_telegram_id = update.message.chat.id # type: ignore

    if not args:
        args = storage[user_telegram_id].last_stat_args
    if not args:
        return await update.message.reply_text("nicknames should be provided") # type: ignore
    storage[user_telegram_id].last_stat_args = args

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
        
    # send error message if users does not exists
    if not grouped_statistic_by_nickname:
        if args[0] == "all":
            await update.message.reply_text("there is no any statistic collected yet") # type: ignore
            return
        if len(args) == 1:
            message = f"there is no user {args[0]}"
        else:
            message = "there is no users: " + ", ".join(args)
        await update.message.reply_text(message) # type: ignore
        return
    
    storage[user_telegram_id].last_stat_args = args

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
    logger.info("users command called")
    raw_records = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nickname: dict[str, list] = statistic.group_by("nickname", statistic_records)
    await update.message.reply_text("\r\n".join(grouped_statistic_by_nickname.keys())) # type: ignore
