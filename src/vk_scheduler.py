import os
import pathlib
import random
from itertools import cycle

from dotenv import find_dotenv, load_dotenv

from add_metadata import add_metadata_to_approved_posts
from image_similarity import (
    generate_hist_cache,
    get_similar_imgs_by_histogram_correlation,
)
from postgres import (
    aggregate_approved_mal_id_counts,
    connect_to_db,
    get_approved_anime_posts,
    get_approved_original_posts,
    insert_vk_record,
    set_selected_status_by_phash,
)
from tags_resolver import convert_tags_to_vk_string
from vk_helper import (
    get_latest_post_date_and_total_post_count,
    get_random_time_next_hour,
    post_photos_to_vk,
)

load_dotenv(find_dotenv())


STATIC_PATH = os.getenv("STATIC_FOLDER_PATH")

DEBUG = False


class VkScheduler:
    def __init__(self):
        self._setup_owner_id()
        self._set_mal_ids_from_db()

        vk_info = get_latest_post_date_and_total_post_count(self._owner_id)
        self._postponed_posts_amount = vk_info.post_count or 0
        self._last_postponed_time = vk_info.last_postponed_time or 0

    def _setup_owner_id(self):
        if DEBUG:
            self._owner_id = int(os.environ.get("VK_KROTKADZIMA_OWNER_ID"))
        else:
            self._owner_id = int(os.environ.get("VK_KOTANIMA_OWNER_ID"))

    def _set_mal_ids_from_db(self):
        conn = connect_to_db()
        self._aggregated_ids = aggregate_approved_mal_id_counts(conn)
        conn.close()

        try:
            self._aggregated_ids.remove((0, None))
        except ValueError:
            print("cant remove none element from mal ids")
            pass

        self._aggregated_ids_cycler = cycle(self._aggregated_ids)

    def _get_next_post_time(self):
        last_post_date = get_random_time_next_hour(self._last_postponed_time)
        self._last_postponed_time = last_post_date
        return last_post_date

    def make_original_post(self):
        conn = connect_to_db()
        self._original_posts = get_approved_original_posts(conn)
        conn.close()

        generate_vk_post(
            self._owner_id, self._get_next_post_time(), self._original_posts
        )
        self._postponed_posts_amount += 1

    def make_anime_post(self, random_post=False):
        # select random or next most popular myanimelist id and post to vk
        if random_post:
            try:
                mal_id = random.choice(self._aggregated_ids).mal_id
            except IndexError:
                print("No approved anime posts left")
                return False
        else:
            try:
                mal_id = next(self._aggregated_ids_cycler).mal_id
            except StopIteration:
                print("No approved anime posts left")
                return False

        conn = connect_to_db()
        posts = get_approved_anime_posts(conn, mal_id=mal_id)
        conn.close()
        generate_vk_post(self._owner_id, self._get_next_post_time(), posts)
        self._postponed_posts_amount += 1

    def get_postponed_posts_amount(self):
        return self._postponed_posts_amount


def main():
    add_metadata_to_approved_posts()
    generate_hist_cache()  # for finding similar images in the future

    scheduler = VkScheduler()

    while scheduler.get_postponed_posts_amount() <= 100:
        scheduler.make_original_post()
        scheduler.make_anime_post(random_post=False)
        scheduler.make_anime_post(random_post=True)
        scheduler.make_anime_post(random_post=True)


class VkPost:
    def __init__(self, owner_id, last_post_date, reddit_posts):
        self.owner_id = owner_id
        self.last_post_date = last_post_date
        self.reddit_posts = reddit_posts

        self.post_data_img_path_dict = {}
        self.img_names: list[str] = []
        self.phash_list: list[str] = []  # so we can add these to vk_table later
        self.sub_name_list: list[str] = []

        self.similar_img_names = []

        self.init_post_data_dict()
        self.init_similar_images()

    def init_post_data_dict(self):
        for post in self.reddit_posts:
            img_name = f"{post.sub_name}_{post.post_id}.jpg"
            self.img_names.append(img_name)
            self.post_data_img_path_dict[img_name] = post

        try:
            self.first_img_name = self.img_names[0]
        except (IndexError, TypeError) as e:
            return False  # or not ?

    def init_similar_images(self):
        self.similar_img_names = get_similar_imgs_by_histogram_correlation(
            self.first_img_name, self.img_names, CORRELATION_LIMIT=0.85, search_amount=2
        )

        self.similar_img_names = [
            str(pathlib.Path(STATIC_PATH, img)) for img in similar_img_names
        ]


def generate_vk_post(OWNER_ID, last_post_date, reddit_posts):
    """Select first image from post, find similar ones
    Add tags to them, post to vk
    """
    post_data_img_path_dict = {}
    img_names = []
    phash_list = []  # so we can add these to vk_table later
    sub_name_list = []

    for post in reddit_posts:
        img_name = f"{post.sub_name}_{post.post_id}.jpg"
        img_names.append(img_name)
        post_data_img_path_dict[img_name] = post

    try:
        first_img_name = img_names[0]
    except (IndexError, TypeError) as e:
        return  # or not ?

    similar_img_names = get_similar_imgs_by_histogram_correlation(
        first_img_name, img_names, CORRELATION_LIMIT=0.85, search_amount=2
    )

    res_img_paths = []
    for img in [first_img_name] + similar_img_names:
        img_path = pathlib.Path(STATIC_PATH, img)
        res_img_paths.append(str(img_path))

    first_obj = post_data_img_path_dict[first_img_name]
    (_, sub_name, source_link, visible_tags, invisible_tags, phash) = first_obj
    phash_list.append(phash)
    sub_name_list.append(sub_name)

    total_tag_count = 0  # we need to make sure there is less than 10 tags in the post
    if visible_tags:
        total_tag_count += len(visible_tags)
    if invisible_tags:
        total_tag_count += len(invisible_tags)

    total_hidden_tag_list = (
        []
    )  # keep track of already added hidden tags, so we dont add duplicates

    if len(similar_img_names) == 0:  # only 1 picture (no similar ones)
        display_text = convert_tags_to_vk_string(visible_tags)
        hidden_text = convert_tags_to_vk_string(invisible_tags)

    else:  # more than one picture: only display anime name and hide char name
        try:
            anime_name = visible_tags[0]
        except (IndexError, TypeError) as e:
            anime_name = None
        try:
            char_name = visible_tags[1]
        except (IndexError, TypeError) as e:
            char_name = None

        if anime_name:
            display_text = convert_tags_to_vk_string([anime_name])
        else:
            display_text = ""

        if char_name:  # add it to invis tags
            total_hidden_tag_list.append(char_name)
            hidden_text = convert_tags_to_vk_string([char_name])
            hidden_text += convert_tags_to_vk_string(invisible_tags)
        else:
            hidden_text = convert_tags_to_vk_string(invisible_tags)

    post_source_link = source_link

    VK_MAX_TAGS_LIMIT = 10

    hidden_text_list = [hidden_text]
    for img_name in similar_img_names:
        post = post_data_img_path_dict[img_name]
        (_, sub_name, source_link, visible_tags, invisible_tags, phash) = post
        phash_list.append(phash)
        sub_name_list.append(sub_name)
        if source_link:
            hidden_text = source_link + "\n"
        else:
            hidden_text = ""

        # get rid of tags that were already used
        if invisible_tags:
            invisible_tags = [
                tag for tag in invisible_tags if tag not in total_hidden_tag_list
            ]
        else:
            invisible_tags = []

        # add unique ones
        total_hidden_tag_list += invisible_tags
        # check VK tags amount limit
        if total_tag_count + len(invisible_tags) < VK_MAX_TAGS_LIMIT:
            total_tag_count += len(invisible_tags)
            hidden_text += convert_tags_to_vk_string(invisible_tags)
            hidden_text_list.append(hidden_text)

    try:
        post_photos_to_vk(
            OWNER_ID,
            res_img_paths,
            display_text,
            post_source_link,
            hidden_text_list,
            last_post_date,
        )
    except Exception as e:
        raise Exception("Failed to post to vk") from e

    # cleanup

    # add to vk_post table
    conn = connect_to_db()
    for phash, sub_name in zip(phash_list, sub_name_list):
        insert_vk_record(conn, last_post_date, phash)
        set_selected_status_by_phash(conn, status=None, phash=phash)

    conn.close()

    # delete files
    for path in res_img_paths:
        try:
            os.remove(path)
        except Exception:
            print(f"Couldnt delete file {path}")
            pass


if __name__ == "__main__":
    main()
