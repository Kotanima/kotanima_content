import os
import pathlib
import random

from dotenv import find_dotenv, load_dotenv

from add_metadata import add_metadata_to_approved_posts
from image_similarity import get_similar_imgs_by_histogram_correlation
from postgres import (aggregate_approved_mal_id_counts, connect_to_db,
                      get_approved_anime_posts, get_approved_original_posts,
                      insert_vk_record, set_selected_status_by_phash)
from tags_resolver import convert_tags_to_vk_string
from vk_helper import (get_latest_post_date_and_total_count,
                       get_random_time_next_hour, post_photos_to_vk)

load_dotenv(find_dotenv())


STATIC_PATH = os.getenv("STATIC_FOLDER_PATH")


def main():
    # add_metadata_to_approved_posts()

    conn, _ = connect_to_db()
    OWNER_ID = int(os.environ.get("VK_KOTANIMA_OWNER_ID"))
    return

    last_post_date, postponed_posts_amount = get_latest_post_date_and_total_count(OWNER_ID)

    POST_AMOUNT_INCREMENT = 2  # post 1 original post and 1 anime post
    anime_counter = 0

    while postponed_posts_amount + POST_AMOUNT_INCREMENT <= 70:
        postponed_posts_amount += POST_AMOUNT_INCREMENT

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_original_posts(conn)
        generate_vk_post(OWNER_ID, last_post_date, posts)

        mal_ids = aggregate_approved_mal_id_counts(conn)
        try:
            mal_ids.remove((0, None))
        except ValueError as e:
            # TODO add post without any approved posts
            raise Exception('No approved posts') from e

        # alternate between most popular posts and random posts
        if anime_counter % 2 == 0:
            mal_id = mal_ids[anime_counter][1]
        else:
            mal_id = random.choice(mal_ids)[1]

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_anime_posts(conn, mal_id=mal_id)
        generate_vk_post(OWNER_ID, last_post_date, posts)
        anime_counter += 1

    conn.close()


def generate_vk_post(OWNER_ID, last_post_date, reddit_posts):
    """Select first image from post, find similar ones
    Add tags to them, post to vk
    """
    post_data_img_path_dict = {}
    img_paths = []
    phash_list = []  # so we can add these to vk_table later
    sub_name_list = []

    for post in reddit_posts:
        (post_id, sub_name, source_link, visible_tags, invisible_tags, _) = post
        img_path = pathlib.Path(STATIC_PATH, f"{sub_name}_{post_id}.jpg")
        img_path = str(img_path)
        img_paths.append(img_path)
        post_data_img_path_dict[img_path] = post

    try:
        first_img_path = img_paths[0]
    except IndexError:
        return  # or not ?

    similar_img_paths = get_similar_imgs_by_histogram_correlation(first_img_path, img_paths, CORRELATION_LIMIT=0.9, search_amount=2)
    res_img_paths = [first_img_path] + similar_img_paths

    first_obj = post_data_img_path_dict[first_img_path]
    (_, sub_name, source_link, visible_tags, invisible_tags, phash) = first_obj
    phash_list.append(phash)
    sub_name_list.append(sub_name)

    total_tag_count = 0  # we need to make sure there is less than 10 tags in the post
    total_tag_count += len(visible_tags)
    total_tag_count += len(invisible_tags)

    total_hidden_tag_list = []  # keep track of already added hidden tags, so we dont add duplicates

    if len(similar_img_paths) == 0:  # only 1 picture (no similar ones)
        display_text = convert_tags_to_vk_string(visible_tags)
        hidden_text = convert_tags_to_vk_string(invisible_tags)

    else:  # more than one picture: only display anime name and hide char name
        try:
            anime_name = visible_tags[0]
        except IndexError:
            anime_name = None
        try:
            char_name = visible_tags[1]
        except IndexError:
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
    for img_path in similar_img_paths:
        post = post_data_img_path_dict[img_path]
        (_, sub_name, source_link, visible_tags, invisible_tags, phash) = post
        phash_list.append(phash)
        sub_name_list.append(sub_name)
        hidden_text = source_link + '\n'
        # get rid of tags that were already used
        invisible_tags = [tag for tag in invisible_tags if tag not in total_hidden_tag_list]
        # add unique ones
        total_hidden_tag_list += invisible_tags
        # check VK tags amount limit
        if total_tag_count + len(invisible_tags) < VK_MAX_TAGS_LIMIT:
            total_tag_count += len(invisible_tags)
            hidden_text += convert_tags_to_vk_string(invisible_tags)
            hidden_text_list.append(hidden_text)

    try:
        post_photos_to_vk(OWNER_ID, res_img_paths, display_text, post_source_link, hidden_text_list, last_post_date)
    except Exception as e:
        raise Exception('Failed to post to vk') from e

    # cleanup

    # add to vk_post table
    conn, _ = connect_to_db()
    for phash, sub_name in zip(phash_list, sub_name_list):
        insert_vk_record(conn, last_post_date, phash)
        set_selected_status_by_phash(conn, None, phash, sub_name)

    conn.close()

    # delete files
    for path in res_img_paths:
        try:
            os.remove(path)
        except Exception:
            print(f"Couldnt delete file {path}")
            pass


if __name__ == '__main__':
    main()
