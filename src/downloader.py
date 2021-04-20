import glob
import os
import pathlib
import subprocess
from pathlib import Path

from PIL import Image, ImageFile

from image_similarity import generate_hist_cache
from postgres import (connect_to_db, get_disliked_posts,
                      set_selected_status_by_phash)

ImageFile.LOAD_TRUNCATED_IMAGES = True  # else OsError


STATIC_FOLDER_PATH = './static'


MEGABYTE = 1000000
GIGABYTE = 1000000000

FOLDER_SIZE_LIMIT = 2.5 * GIGABYTE


def get_reddit_post_data(cursor, limit: int):
    # TODO get safe subs from server
    query = f"""SELECT post_id, author, created_utc, title, url, phash, sub_name FROM my_app_redditpost 
              WHERE sub_name IN ('awwnime','fantasymoe','patchuu','awenime','moescape')
              AND phash NOT IN (SELECT phash FROM my_app_vkpost)
              AND wrong_format=false
              AND dislike is NULL
              AND selected is NULL
              ORDER BY RANDOM()
              LIMIT {limit}"""

    cursor.execute(query)
    data = cursor.fetchall()
    return data


def download_pic_from_url(url: str, folder: str, limit: int = 1) -> bool:
    """

    Args:
        url (str): url to the picture
        folder (str) : folder to download into
        limit (int): when dealing with albums load only first N items

    Returns:
        bool: True if picture loaded
    """
    try:
        result = subprocess.check_output(['gallery-dl',
                                          '--dest', folder + "/",
                                          '--http-timeout', '7',
                                          '--sleep', '1',
                                          '--range', f'{limit}',
                                          '--filter', "extension in ('jpg', 'png', 'jpeg', 'PNG', 'JPEG')",
                                          '--config', '../gallery-dl.conf',
                                          f"{str(url)}"])

        if len(result) == 0:
            return False

    except subprocess.CalledProcessError:
        return False

    return True


def optimize_image(file_path: str):
    try:
        result = subprocess.check_output(['optimize-images', file_path])

        if len(result) == 0:
            return False

    except subprocess.CalledProcessError:
        return False

    return True


def rename_latest_file_in_folder(folder: str, new_filename: str):
    """Gallery-dl loads images with random names, rename the latest downloaded one
    to {new_filename} + {.ext}

    Args:
        new_filename (str): {created_utc} + '_' + {post.id}

    Returns:
        [type]: new path to renamed file
    """
    file_path = get_latest_filename_in_folder(folder)
    if not file_path:
        print("No file path found")
        return
    old_ext = file_path.suffix
    old_path = Path(file_path).resolve().parent
    new_path = Path(old_path, new_filename + old_ext)
    file_path.rename(new_path)
    return new_path


def get_latest_filename_in_folder(folder: str) -> Path:
    download_folder = str(Path(folder + "/*").absolute())
    try:
        last_file = max(glob.glob(download_folder), key=os.path.getctime)
    except ValueError:
        print("Couldnt find a file")
        return

    return Path(last_file)


def optimize_latest_file(file_name: str):
    """If input file extension isnt jpg, convert it to jpg. Optimize image.

    Args:
        file_name (str): path to image file
    """
    p = Path(file_name)
    extensions = "".join(p.suffixes)
    if extensions != '.jpg':
        try:
            img = Image.open(file_name).convert('RGB')
        except OSError:
            print(f"Couldnt open image {file_name}")
            try:
                p.unlink()
            except FileNotFoundError:
                pass
            return False

        new_file_name = str(file_name).removesuffix(extensions) + '.jpg'
        img.save(new_file_name)
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    file_name = file_name or new_file_name
    optimize_image(file_name)
    return True


def get_static_folder_size():
    # this is non recursive
    root_directory = Path(STATIC_FOLDER_PATH)
    return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())


def download_more(amount):
    # get N random entries from db
    # download them, rename, optimize size
    connection, _ = connect_to_db()
    with connection:
        with connection.cursor() as cursor:
            posts = get_reddit_post_data(cursor, amount)
    for post in posts:
        (post_id, author, created_utc, title, url, phash, sub_name) = post

        did_load = download_pic_from_url(url, folder=STATIC_FOLDER_PATH, limit=1)
        if not did_load:
            print("Couldnt download file, with ", f"{url=}")
            continue
        else:
            file_path = rename_latest_file_in_folder(
                STATIC_FOLDER_PATH, f"{sub_name}_{post_id}")

        did_optimize = optimize_latest_file(file_path)

        # mark as selected in db
        if did_optimize:
            set_selected_status_by_phash(connection, status=False, table_name=sub_name, phash=phash)

    connection.close()
    generate_hist_cache()  # for finding similar images in the future


def delete_disliked_posts():
    # also unselect them!
    conn, _ = connect_to_db()
    disliked_posts = get_disliked_posts(conn)
    for post in disliked_posts:
        (sub_name, post_id, phash) = post
        set_selected_status_by_phash(conn, None, phash, sub_name)
        filename = pathlib.Path(STATIC_FOLDER_PATH, f"{sub_name}_{post_id}.jpg")

        try:
            filename.unlink()
        except Exception:
            print(f"Couldnt delete file {filename}")
            pass

    conn.close()


def main():
    folder_size = get_static_folder_size()
    print(folder_size / (1024 * 1024))

    delete_disliked_posts()
    if folder_size > FOLDER_SIZE_LIMIT:
        print("Enough files")
    else:
        print("Downloading more")
        download_more(25)


if __name__ == '__main__':
    main()
