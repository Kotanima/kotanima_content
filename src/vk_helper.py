    """Helper functions for VK API
    """
import datetime
import json
import os
from collections import namedtuple
from random import randint

import pytz
import requests
import vk_api
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True))

# авторизация
# https://vk.com/dev/authcode_flow_user
# step 1: send request
# https://oauth.vk.com/authorize?client_id=CLIENT_ID&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=offline,wall,photos,audio,video,stories,ads,docs,groups,stats&response_type=code&v=5.130
# step 2: paste response code in url below and send request again
# https://oauth.vk.com/access_token?client_id=CLIENT_ID&client_secret=CLIENT_SECRET&redirect_uri=https://oauth.vk.com/blank.html&code=RESPONSE_CODE_FROM_VK
# step 3: copy paste access token into VkApi(token="UR_TOKEN") field


def vk_auth():
    vk_session = vk_api.VkApi(token=os.environ.get("VK_ACCESS_TOKEN"))
    vk = vk_session.get_api()
    return vk


def post_photos_to_vk(
    OWNER_ID: int,
    image_list: list,
    text: str,
    source_link: str,
    hidden_text_list: list,
    delay: int,
):
    vk = vk_auth()
    destination = vk.photos.getWallUploadServer()
    photo_responses = []
    for counter, img_path in enumerate(image_list):
        meta = requests.post(
            destination["upload_url"],
            files={"file1": open(img_path, "rb")},
        )
        result = json.loads(meta.text)
        photo = vk.photos.saveWallPhoto(
            photo=result["photo"],
            hash=result["hash"],
            server=result["server"],
            caption=hidden_text_list[counter],
        )
        photo_responses.append(f"photo{photo[0]['owner_id']}_{photo[0]['id']}")

        # unselect from db by hash

    vk.wall.post(
        owner_id=-OWNER_ID,
        from_group=1,
        publish_date=delay,
        message=text,
        copyright=source_link,
        attachments=",".join(photo_responses),
    )


def get_random_time_next_hour(date_timestamp: int):
    date = datetime.datetime.fromtimestamp(date_timestamp)
    random_minute = randint(1, 59)
    date += datetime.timedelta(hours=1)
    date = date.replace(minute=random_minute)
    return int(date.timestamp())


def get_latest_post_date_and_total_post_count(OWNER_ID: int):
    vk = vk_auth()
    tools = vk_api.VkTools(vk)

    wall = tools.get_all(
        "wall.get", 100, {"owner_id": -OWNER_ID, "filter": "postponed"}
    )

    latest_time = 0
    for item in wall["items"]:
        if item["date"] > latest_time:
            latest_time = item["date"]

    print(f"{latest_time=}")
    if latest_time == 0:
        tz = pytz.timezone("Europe/Moscow")
        current_date = datetime.datetime.now(tz)
        latest_time = int(current_date.timestamp())

    vk_info = namedtuple("vk_info", ["last_postponed_time", "post_count"])
    return vk_info(latest_time, wall["count"])
