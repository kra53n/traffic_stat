import dataclasses
import datetime
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
    last_input_nicknames: typing.Optional[list[str]] = None
    period: typing.Optional[int] = None # in days


class Storage(dict):
    def __getitem__(self, key: int) -> UserStorage:
        if key not in self:
            self[key] = UserStorage()
        return super().__getitem__(key)


storage = Storage()


@dataclasses.dataclass
class SettingRule:
    short_way: typing.Optional[typing.Callable[[UserStorage, list[str]], typing.Optional[str]]] = None
    long_way: typing.Optional[typing.Callable[[UserStorage, list[str]], typing.Optional[str]]] = None


def stat_short_setting_rule(us: UserStorage, vals: list[str]):
    us.last_input_nicknames = vals


settings_rules: dict[str, SettingRule] = {
    "stat": SettingRule(
        short_way = stat_short_setting_rule,
    ),
}


@dataclasses.dataclass
class Command:
    name: str
    description: str
    callable: typing.Any = None
    

format_bytes_table = (
    "bytes",
    "KiB", # kibibyte
    "MiB", # mebibyte
    "GiB", # gibibyte
    "TiB", # tebibyte
    "PiB", # pebibyte
    "EiB", # exbibyte
    "ZiB", # zebibyte
    "YiB", # yobibyte
    "RiB", # robibyte
    "QiB", # quebibyte
)


def format_bytes(bytes: int) -> str:
    cnt = 0
    while True:
        tmp = bytes >> 10 # shift to right by 1024
        if tmp == 0:
            return f"{bytes} {format_bytes_table[cnt]}"
        bytes = tmp
        cnt += 1


def format_statistic_for_summary(statistic: statistic.Statistic, bytes: typing.Optional[int] = None) -> str:
    if not bytes:
        bytes = statistic.alltime
    return f"{datetime.date(statistic.year, statistic.month, statistic.day).strftime('%d %b')} {format_bytes(bytes):>8}"


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
        raise Exception(err_msg)
    
    storage[user.id].last_input_nicknames = nicknames

    return grouped_statistic_by_nicknames


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

    /users - send message with proxy users
    
    /settings - change command behaviours
        /settings command value
        /settings command field value"""
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

    if not update.message.from_user:
        logger.error("no user")
        return

    try:
        grouped_statistc_by_nicknames = await get_grouped_statistic_by_nicknames(update.message)
    except Exception as e:
        return await update.message.reply_text(", ".join(e.args))

    user_storage = storage[update.message.from_user.id]
    period = user_storage.period
    if not period:
        period = 30 # set 30 days by default

    # accept period to grouped_statistic_by_nicknames
    for nickname, statistic_list in grouped_statistc_by_nicknames.items():
        grouped_statistc_by_nicknames[nickname] = statistic_list[-period:]

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

    try:
        grouped_statistc_by_nicknames = await get_grouped_statistic_by_nicknames(update.message)
    except Exception as e:
        return await update.message.reply_text(", ".join(e.args))

    message = ""
    for nickname, statistic in grouped_statistc_by_nicknames.items():
        message += f"class {nickname}:\r\n"
        statistic = statistic[-6:]
        match len(statistic):
            case 0:
                message += "no statistic"
            case 1:
                message += "    " + format_statistic_for_summary(statistic[0])
            case _:
                message += "\r\n".join(("    " + format_statistic_for_summary(statistic[i], statistic[i].alltime - statistic[i-1].alltime) for i in range(1, len(statistic))))
        message += "\r\n\r\n\r\n"

    await update.message.reply_text(f"```python\r\n{message}```", parse_mode="Markdown")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return users list
    """
    logger.info("users command called")
    raw_records = db.get(db_src=db.src(), table_name="stat")
    statistic_records: list[statistic.Statistic] = statistic.get_list(raw_records)
    grouped_statistic_by_nickname: dict[str, list] = statistic.group_by("nickname", statistic_records)
    await update.message.reply_text("\r\n".join(grouped_statistic_by_nickname.keys())) # type: ignore



async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The configuration of other commands results.

    Rule of parsing a command:
    - short way
        /settings command value
    - long way
        /settings command field value

    It is possible to have 2 ways for 1 command and if it is, short way set by command context.
    """
    logger.info("settings command called")

    if not update.message:
        logger.error("no message")
        return

    if not update.message.from_user:
        raise Exception("no user provided to the message")
    
    if not update.message.text:
        raise Exception("was given a message without text")

    # skip `/settings`
    tokens = update.message.text.split()[1:]

    if not tokens:
        return update.message.reply_text("""The configuration of other commands results.

    Rule of parsing a command:
    - short way
        /settings command value
    - long way
        /settings command field value

    It is possible to have 2 ways for 1 command and if it is, short way set by command context""")

    # validate given words sequence
    command = tokens[0]
    setting_rule = settings_rules[command]
    if not command:
        return await update.message.reply_text(f"🚨 there is no command /{command}")
    if len(tokens) == 1:
        return await update.message.reply_text(f"🚨 fields and values was not provided")
    if len(tokens) == 2 and not setting_rule.short_way:
        return await update.message.reply_text(f"🚨 command /{command} does not have short way")
    if len(tokens) % 2 == 1:
        return await update.message.reply_text("🚨 wrong numbers of fields and values")

    # skip command
    args = tokens[1:] 

    # execute command
    exec_command = setting_rule.short_way if len(args) == 1 else setting_rule.long_way

    if not exec_command:
        if len(args) == 1:
            return await update.message.reply_text("🚨 there is short setting option for command /{command}")
        else:
            return await update.message.reply_text("🚨 there is long setting option for command /{command}")

    try:
        result = exec_command(storage[update.message.from_user.id], args)
        if not result:
            result = "command succeeded"
    except Exception as e:
        result = f"🚨 {', '.join(e.args)}"

    await update.message.reply_text(result)


commands = (
        Command(name="start", description="start message", callable=start),
        Command(name="health", description="check bot health", callable=health),
        Command(name="stat", description="statistic figures", callable=stat),
        Command(name="summary", description="users summary", callable=summary),
        Command(name="users", description="users list", callable=users),
        Command(name="settings", description="change command behaviours", callable=settings),
)


async def post_init(app: Application):
    logger.trace("add command commands")
    await app.bot.set_my_commands((BotCommand(command.name, command.description) for command in commands))


def run(tg_bot_token: str):
    logger.info("run telegram bot")
    app = ApplicationBuilder().token(tg_bot_token).post_init(post_init).build()
    app.add_handlers(tuple(CommandHandler(command.name, command.callable) for command in commands))
    app.run_polling()
