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
from models import IdentifiedRedditPost
from postgres import (
    aggregate_approved_mal_id_counts,
    connect_to_db,
    get_approved_anime_posts,
    get_approved_original_posts,
    insert_vk_record,
    set_downloaded_status_by_phash,
)
from tags_resolver import convert_tags_to_vk_string
from vk_helper import (
    get_latest_post_date_and_total_post_count,
    get_random_time_next_hour,
    post_photos_to_vk,
)

load_dotenv(find_dotenv(raise_error_if_not_found=True))
STATIC_PATH = os.getenv("STATIC_FOLDER_PATH")

DEBUG = False


def get_owner_id() -> int:
    if DEBUG:
        return int(os.environ.get("VK_KROTKADZIMA_OWNER_ID"))
    else:
        return int(os.environ.get("VK_KOTANIMA_OWNER_ID"))


class VkScheduler:
    def __init__(self):
        self._owner_id = get_owner_id()
        self._set_mal_ids_from_db()

        vk_info = get_latest_post_date_and_total_post_count(self._owner_id)
        self._postponed_posts_amount = vk_info.post_count or 0
        self._last_postponed_time = vk_info.last_postponed_time or 0

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

    def make_original_post(self) -> bool:
        """[summary]

        Returns:
            bool: True, if no more original posts left
        """
        conn = connect_to_db()
        original_posts = get_approved_original_posts(conn)
        conn.close()
        if not original_posts:
            raise NothingToPostError

        original_posts = [
            IdentifiedRedditPost.from_dict(post) for post in original_posts
        ]

        vk_post = VkPost(
            owner_id=self._owner_id,
            last_post_date=self._get_next_post_time(),
            reddit_posts=original_posts,
        )
        vk_post.upload()

        self._postponed_posts_amount += 1

    def make_anime_post(self, random_post=False) -> bool:
        """select random or next most popular myanimelist id and post to vk
        Args:
            random_post (bool, optional): [description]. Defaults to False.

        Returns:
            bool: True, if no anime posts left
        """
        #
        if random_post:
            try:
                mal_id = random.choice(self._aggregated_ids).mal_id
            except IndexError:
                print("No approved anime posts left")
                raise NothingToPostError
        else:
            try:
                mal_id = next(self._aggregated_ids_cycler).mal_id
            except StopIteration:
                print("No approved anime posts left")
                raise NothingToPostError

        conn = connect_to_db()
        anime_posts = get_approved_anime_posts(conn, mal_id=mal_id)
        conn.close()

        if not anime_posts:
            return False
        anime_posts = [IdentifiedRedditPost.from_dict(post) for post in anime_posts]

        vk_post = VkPost(
            owner_id=self._owner_id,
            last_post_date=self._get_next_post_time(),
            reddit_posts=anime_posts,
        )
        vk_post.upload()
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
        scheduler.make_anime_post(random_post=True)


class NothingToPostError(Exception):
    pass


def mark_as_undownloaded_in_db(phash: str):
    conn = connect_to_db()
    set_downloaded_status_by_phash(conn, status=False, phash=phash)
    conn.close()


class VkPost:
    def __init__(
        self,
        owner_id: int,
        last_post_date: int,
        reddit_posts: list[IdentifiedRedditPost],
    ):
        # 1) select first reddit post
        # 2) find similar images to it
        # 3) set main display message text
        # 4) set individual images hidden text
        # 5) upload to vk

        self.owner_id: int = owner_id
        self.last_post_date: int = last_post_date
        self.reddit_posts: list[IdentifiedRedditPost] = reddit_posts

        try:
            self.similar_posts = self.get_similar_looking_posts()
        except FileNotFoundError:
            try:
                self.reddit_posts[0]
            except IndexError:
                raise NothingToPostError

            mark_as_undownloaded_in_db(phash=self.reddit_posts[0].phash)
            return

    def upload(self):
        try:
            main_post_message = self.get_main_post_message(self.similar_posts)
        except AttributeError:
            print("No file")
            mark_as_undownloaded_in_db(phash=self.reddit_posts[0].phash)
            raise FileNotFoundError

        hidden_messages = self.get_list_of_hidden_messages(self.similar_posts)

        similar_img_paths = [
            str(pathlib.Path(STATIC_PATH, post.get_image_name()))
            for post in self.similar_posts
        ]
        try:
            post_photos_to_vk(
                OWNER_ID=self.owner_id,
                image_list=similar_img_paths,
                text=main_post_message,
                source_link=self.reddit_posts[0].source_link,
                hidden_text_list=hidden_messages,
                delay=self.last_post_date,
            )
        except Exception as e:
            raise Exception("Failed to post to vk") from e

        if not DEBUG:
            self.mark_posts_as_uploaded()
            self.delete_images_from_disk()

    def mark_posts_as_uploaded(self):
        # add to vk_post table
        conn = connect_to_db()
        for post in self.similar_posts:
            insert_vk_record(conn, self.last_post_date, post.phash)
            set_downloaded_status_by_phash(conn, status=False, phash=post.phash)

        if conn:
            conn.close()

    def delete_images_from_disk(self):
        similar_img_paths = [
            str(pathlib.Path(STATIC_PATH, post.get_image_name()))
            for post in self.similar_posts
        ]

        for path in similar_img_paths:
            try:
                os.remove(path)
            except OSError:
                print(f"Couldnt delete file {path}")
                pass

    def get_main_post_message(self, filtered_reddit_posts: list[IdentifiedRedditPost]):
        if not filtered_reddit_posts:
            return

        if len(filtered_reddit_posts) == 0:
            return ""

        elif len(filtered_reddit_posts) == 1:
            only_post = filtered_reddit_posts[0]
            return convert_tags_to_vk_string(only_post.visible_tags)

        else:
            return convert_tags_to_vk_string([filtered_reddit_posts[0].anime_name])

    def get_list_of_hidden_messages(
        self, filtered_reddit_posts: list[IdentifiedRedditPost]
    ) -> list[str]:
        if len(filtered_reddit_posts) == 0:
            return [""]

        elif len(filtered_reddit_posts) == 1:
            only_post = filtered_reddit_posts[0]
            return [
                convert_tags_to_vk_string(only_post.invisible_tags)
                + f"\n {only_post.source_link}"
            ]

        else:
            messages: list[str] = []
            existing_tags: list[str] = []
            for post in filtered_reddit_posts:
                msg = ""
                post_tags = post.invisible_tags

                # add character name to tags
                if post.character_name and post.invisible_tags:
                    post_tags = [post.character_name] + post.invisible_tags

                # filter existing tags
                if post_tags:
                    post_tags = [tag for tag in post_tags if tag not in existing_tags]

                    for tag in post_tags:
                        existing_tags.append(tag)

                    msg = convert_tags_to_vk_string(post_tags)

                if post.source_link:
                    msg += f"\n {post.source_link}"
                messages.append(msg)

            return messages

    def get_similar_looking_posts(self) -> list[str]:
        img_names = [post.get_image_name() for post in self.reddit_posts]
        similar_img_names = get_similar_imgs_by_histogram_correlation(
            img_names, CORRELATION_LIMIT=0.85, search_amount=2
        )
        if not similar_img_names:
            return

        return [
            post
            for post in self.reddit_posts
            if post.get_image_name() in similar_img_names
        ]


if __name__ == "__main__":
    main()
