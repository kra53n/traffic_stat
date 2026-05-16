import dotenv
import os

import tgbot


if __name__ == '__main__':
    dotenv.load_dotenv()
    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    if tg_bot_token:
        tgbot.run(tg_bot_token)

    # TODO add figure name