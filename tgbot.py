import dataclasses
import typing
import io

from loguru import logger
from telegram import (
    Update,
    InputMediaPhoto,
    BotCommand,
    User,
    Message,
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
    last_input_nicknames: typing.Optional[list["str"]] = None


class Storage(dict):
    def __getitem__(self, key: int) -> UserStorage:
        if key not in self:
            self[key] = UserStorage()
        return super().__getitem__(key)


storage = Storage()


async def get_grouped_statistic_by_nicknames(message: Message) -> dict[str, list[typing.Any]]:
    user: typing.Optional[User] = message.from_user
    if not user:
        raise Exception("no user provided to the message")

    # get nicknames, skip command
    nicknames = message.text.split()[1:] # type: ignore

    if not nicknames:
        if not user:
            raise Exception("no user provided to the message")

        nicknames = storage[user.id].last_input_nicknames
        if not nicknames and user.username:
            nicknames = [user.username]

    if not nicknames:
        raise Exception("should be given nickname or nicknames, see /start")

    logger.info(f"nicknames: {nicknames}")

    # get data from db
    raw_records: list[list] = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nicknames: dict[str, list] = statistic.group_by("nickname", statistic_records)

    # exclude nicknames that not provided as arguments in command
    if nicknames[0] != "all":
        grouped_statistic_by_nicknames_keys = tuple(grouped_statistic_by_nicknames.keys())
        for nickname in grouped_statistic_by_nicknames_keys:
            if nickname not in nicknames:
                grouped_statistic_by_nicknames.pop(nickname)
        
    # send error message if users does not exists
    if not grouped_statistic_by_nicknames:
        if nicknames[0] == "all":
            await message.reply_text("there is no any statistic collected yet") # type: ignore
            return {}
        if len(nicknames) == 1:
            err_msg = f"there is no user {nicknames[0]}"
        else:
            err_msg = "there is no users: " + ", ".join(nicknames)
        await message.reply_text(err_msg)
        return {}
    
    storage[user.id].last_input_nicknames = nicknames

    return grouped_statistic_by_nicknames



def run(tg_bot_token: str):
    logger.info("run telegram bot")
    app = ApplicationBuilder().token(tg_bot_token).post_init(post_init).build()
    app.add_handlers(
        (
            CommandHandler("start", start),
            CommandHandler("health", health),
            CommandHandler("stat", stat),
            CommandHandler("users", users),
            CommandHandler("summary", summary),
        )
    )
    app.run_polling()


async def post_init(app: Application):
    logger.trace("add command commands")
    await app.bot.set_my_commands([
        BotCommand("start", "start message"),
        BotCommand("health", "check bot health"),
        BotCommand("stat", "statistic figures"),
        BotCommand("summary", "users summary"),
        BotCommand("users", "users list"),
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prints start message
    """
    message = """Show statistic of proxy usage

    /start - start message i guess

    /health - send message if bot is alive

    /stat - send message with figures
        /stat user1 - send figures with user1
        /stat user1 user2 - send figures with user1 and user2

    /summary - send message with summary
        /summary user1 - send summary with user1
        /summary user1 user2 - send summary with user1 and user2

    /users - send message with proxy users"""
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

    if not update.message:
        logger.error("no message")
        return

    grouped_statistc_by_nicknames = await get_grouped_statistic_by_nicknames(update.message)

    # build figures
    fig1 = io.BytesIO()
    fig2 = io.BytesIO()
    plot.alltime_figure(grouped_statistc_by_nicknames, fig1)
    plot.diff_figure(grouped_statistc_by_nicknames, fig2)

    media_group = (
        InputMediaPhoto(fig1.getvalue()),
        InputMediaPhoto(fig2.getvalue()),
    )
    await update.message.reply_media_group(media_group) # type: ignore
    
    fig1.close()
    fig2.close()


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send user summary
    """
    logger.info("summary command called")

    if not update.message:
        logger.error("no message")
        return

    grouped_statistc_by_nicknames = await get_grouped_statistic_by_nicknames(update.message)
    message = ""
    for nickname, statistic in grouped_statistc_by_nicknames.items():
        message += "  " + nickname + "\r\n"
        statistic = statistic[-6:]
        match len(statistic):
            case 0:
                message += "no statistic"
            case 1:
                message += "    " + f"{statistic[0].day} {statistic[0].month} " + statistic[0].alltime + " GiB"
            case _:
                message += "\r\n".join(("    " + f"{statistic[i].day} {statistic[i].month} " + str((statistic[i].alltime - statistic[i-1].alltime) / 1024 / 1024 / 1024) + " GiB" for i in range(1, len(statistic))))
                print(message)
        message += "\r\n"

    await update.message.reply_text(message)


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return users list
    """
    logger.info("users command called")
    raw_records = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nickname: dict[str, list] = statistic.group_by("nickname", statistic_records)
    await update.message.reply_text("\r\n".join(grouped_statistic_by_nickname.keys())) # type: ignore
