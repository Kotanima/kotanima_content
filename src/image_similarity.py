import os
from PIL import Image
import glob
import cv2
import matplotlib
import pickle

matplotlib.use('Agg')
# https://www.pyimagesearch.com/2014/07/14/3-ways-compare-histograms-using-opencv-python/


def get_hist_for_file(img_path):
    try:
        image = cv2.imread(img_path)
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8],
                            [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
    except Exception:  # broken image
        return None
    return hist


def generate_hist_cache():
    static_folder = './static/*.jpg'
    static_images = glob.glob(static_folder)
    cache_dict = {}
    for img_path in static_images:
        hist = get_hist_for_file(img_path)
        if hist is not None:
            cache_dict[img_path] = hist
        else:  # broken file, get rid of it
            cache_dict.pop(img_path, None)
            try:
                os.remove(img_path)
            except Exception:
                print(f"Couldnt delete file {img_path}")

    with open('cache_dict.pickle', 'wb') as f:
        pickle.dump(cache_dict, f)


def get_similar_imgs_by_histogram_correlation(target_img_path: str, similar_img_paths: list, CORRELATION_LIMIT=0.9, search_amount=2):
    with open('cache_dict.pickle', 'rb') as f:
        hist_dict = pickle.load(f)

    try:
        target_hist = hist_dict[target_img_path]
    except KeyError:
        target_hist = get_hist_for_file(target_img_path)

    result_images = []
    similar_img_paths.remove(target_img_path)  # dont compare against self
    for path in similar_img_paths:
        try:
            current_hist = hist_dict[path]
        except KeyError:
            current_hist = get_hist_for_file(path)

        diff = cv2.compareHist(target_hist, current_hist, cv2.HISTCMP_CORREL)
        if diff > CORRELATION_LIMIT:
            result_images.append(path)
            if len(result_images) == search_amount:
                return result_images

    return result_images


if __name__ == "__main__":
    generate_hist_cache()

    static_folder = './static/*.jpg'
    imgs_in_static_folder = glob.glob(static_folder)
    first_path = str(imgs_in_static_folder[10])
    print(first_path)

    res = get_similar_imgs_by_histogram_correlation(first_path, imgs_in_static_folder)
    print(res)
    if res:
        with Image.open(first_path) as img:
            img.show()

        for path in res:
            with Image.open(path) as img:
                img.show()
