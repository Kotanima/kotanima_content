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


def main():
    add_metadata_to_approved_posts()
    generate_hist_cache()  # for finding similar images in the future

    OWNER_ID = int(os.environ.get("VK_KOTANIMA_OWNER_ID"))

    last_post_date, postponed_posts_amount = get_latest_post_date_and_total_post_count(
        OWNER_ID
    )

    conn = connect_to_db()
    mal_ids = aggregate_approved_mal_id_counts(conn)

    try:
        mal_ids.remove((0, None))
    except ValueError:
        pass
    mal_ids_cycler = cycle(mal_ids[1])  # cycle through anime postss

    while postponed_posts_amount <= 75:

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_original_posts(conn)
        if posts:
            generate_vk_post(OWNER_ID, last_post_date, posts)
            postponed_posts_amount += 1
        else:
            print("No approved original posts")

        # alternate between most popular posts and random posts

        try:
            mal_id = next(mal_ids_cycler)
        except StopIteration:
            print("No approved anime posts left")
            continue

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_anime_posts(conn, mal_id=mal_id)
        generate_vk_post(OWNER_ID, last_post_date, posts)
        postponed_posts_amount += 1

        try:
            mal_id = random.choice(mal_ids)[1]
        except IndexError:
            print("No approved anime posts left")
            continue

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_anime_posts(conn, mal_id=mal_id)
        generate_vk_post(OWNER_ID, last_post_date, posts)
        postponed_posts_amount += 1

        try:
            mal_id = next(mal_ids_cycler)
        except StopIteration:
            print("No approved anime posts left")
            continue

        last_post_date = get_random_time_next_hour(last_post_date)
        posts = get_approved_anime_posts(conn, mal_id=mal_id)
        generate_vk_post(OWNER_ID, last_post_date, posts)
        postponed_posts_amount += 1

    conn.close()


def generate_vk_post(OWNER_ID, last_post_date, reddit_posts):
    """Select first image from post, find similar ones
    Add tags to them, post to vk
    """
    post_data_img_path_dict = {}
    img_names = []
    phash_list = []  # so we can add these to vk_table later
    sub_name_list = []

    for post in reddit_posts:
        (post_id, sub_name, source_link, visible_tags, invisible_tags, _) = post
        img_name = f"{sub_name}_{post_id}.jpg"
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
        set_selected_status_by_phash(conn, None, phash, sub_name)

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
