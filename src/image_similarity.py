"""
Find similar images using opencv by using correlation between color histograms
"""
import glob
import os
from typing import Optional

import cv2
import h5py
import matplotlib
from dotenv import find_dotenv, load_dotenv
from PIL import Image

load_dotenv(find_dotenv(raise_error_if_not_found=True))
STATIC_PATH = os.getenv("STATIC_FOLDER_PATH")


matplotlib.use("Agg")
# https://www.pyimagesearch.com/2014/07/14/3-ways-compare-histograms-using-opencv-python/


def _get_hist_for_file(img_path):
    """Get histogram for an image path"""
    try:
        image = cv2.imread(img_path)
        hist = cv2.calcHist(
            [image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
        )
        hist = cv2.normalize(hist, hist).flatten()
    except Exception:  # broken image
        return None
    return hist


import pathlib


def generate_hist_cache() -> None:
    """Store histograms in an HDF5 storage for future re-use during similar image search.
    This was necessary because i was running into memory errors otherwise.
    """
    static_folder = "./static/*.jpg"
    static_images = glob.glob(static_folder)

    with h5py.File("cache_dict.h5", "a", libver="latest") as f:
        for img_path in static_images:
            p = pathlib.Path(img_path)
            file_name = p.name
            hist = _get_hist_for_file(str(img_path))
            if hist is not None:
                try:
                    f.create_dataset(
                        "dict/" + str(file_name), data=hist, compression="gzip"
                    )
                except ValueError:  # already exists
                    pass
            else:  # broken file, get rid of it
                try:
                    os.remove(img_path)
                except OSError:
                    print(f"Couldnt delete file {img_path}")


def get_similar_imgs_by_histogram_correlation(
    img_names: list, CORRELATION_LIMIT=0.85, search_amount=2
) -> Optional[list[str]]:
    """Takes first image in img_names list and finds similar ones.

    Args:
        img_names (list):
        CORRELATION_LIMIT (float, optional): Images with correlation below the threshold will get filtered. Defaults to 0.85.
        search_amount (int, optional): THe function stops after finding N similar images. Defaults to 2.

    Returns:
        list[str]: list that includes base image and best matches
    """
    try:
        first_img_name = img_names[0]
    except IndexError:
        raise FileNotFoundError

    first_img_path = str(pathlib.Path(STATIC_PATH, first_img_name))
    if not os.path.isfile(first_img_path):
        raise FileNotFoundError

    with h5py.File("cache_dict.h5", "r") as h5f:
        h5_arr = h5f["dict"]
        try:
            target_hist = h5_arr[first_img_name][:]
        except KeyError:
            target_hist = _get_hist_for_file(first_img_path)
            if target_hist is None:
                print(f"Couldnt calc hist for {first_img_path}")
                return

        result_images = []
        try:
            img_names.remove(first_img_name)  # dont compare against self
        except ValueError:
            print("First img name was not found in img_names")

        for img_name in img_names:
            img_path = str(pathlib.Path(STATIC_PATH, img_name))
            try:
                current_hist = h5_arr[img_name][:]
            except KeyError:
                current_hist = _get_hist_for_file(img_path)

            try:
                diff = cv2.compareHist(target_hist, current_hist, cv2.HISTCMP_CORREL)
            except cv2.error:
                print("Compare hist error")
                continue

            if diff > CORRELATION_LIMIT and diff != 1:
                result_images.append(img_name)
                if len(result_images) == search_amount:
                    return [first_img_name] + result_images

        return [first_img_name] + result_images


if __name__ == "__main__":
    generate_hist_cache()

    static_folder = "./static/*.jpg"
    imgs_in_static_folder = glob.glob(static_folder)
    first_path = str(imgs_in_static_folder[1])
    print(first_path)

    res = get_similar_imgs_by_histogram_correlation(imgs_in_static_folder)
    print(res)
    if res:
        with Image.open(first_path) as img:
            img.show()

        for path in res:
            with Image.open(path) as img:
                img.show()
