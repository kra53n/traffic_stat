import sys
import os

import dotenv
from loguru import logger

import tgbot


if __name__ == '__main__':
    dotenv.load_dotenv()

    logfile = "./logs/file.log"

    # add TRACE level to stdout
    logger.add(sys.stdout, level="TRACE")
    logger.add(logfile, level="TRACE")

    # setup logging at `/logs` directory
    logger.add(
        logfile,
        rotation=1024*1024, # in bytes
        retention=3,        # keep only 3 files
    )

    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    if tg_bot_token:
        tgbot.run(tg_bot_token)
