import json
import requests
import time
from model.models import DiscordRequestMainContent
from utils.utils import setup_logger

logger = setup_logger(__name__)

HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 10
SLEEP_INTERVAL = 3


def post_message(webhook_url, show_data: DiscordRequestMainContent):
    main_content = json.dumps(show_data.__dict__)
    logger.debug(main_content)
    try:
        response = requests.post(
            url=webhook_url, headers=HEADERS, data=main_content, timeout=TIMEOUT
        )
        response.raise_for_status()
        logger.debug("Success post request")
    except Exception as err:
        logger.warning("Failed post request: '{}'".format(err))
        raise


def post_message_list(webhook_url, show_data: list[DiscordRequestMainContent]):
    # リストが空のときはリクエストを送らない
    if show_data == []:
        logger.debug("No POST data...Finish!")
        return
    for data in show_data:
        post_message(webhook_url, data)
        # 大量の更新があった場合でも429が返ってこないようにする
        time.sleep(SLEEP_INTERVAL)
    logger.debug("All POST requests are finished!")
