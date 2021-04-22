import os
from PIL import Image
import glob
import cv2
import matplotlib
import pickle
import h5py


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

    with h5py.File('cache_dict.h5', 'w', libver='latest') as f:
        for img_path in static_images:
            hist = get_hist_for_file(img_path)
            if hist is not None:
                try:
                    f.create_dataset('dict/' + str(img_path), data=hist, compression="gzip")
                except ValueError:  # already exists
                    pass
            else:  # broken file, get rid of it
                try:
                    os.remove(img_path)
                except Exception:
                    print(f"Couldnt delete file {img_path}")


def get_similar_imgs_by_histogram_correlation(first_img_name: str, img_names: list, CORRELATION_LIMIT=0.7, search_amount=2):
    with h5py.File("cache_dict.h5", 'r') as h5f:
        h5_arr = h5f['dict']['static']
        try:
            target_hist = h5_arr[first_img_name][:]
        except KeyError:
            target_hist = get_hist_for_file(first_img_name)
            if target_hist is None:
                print(f"Couldnt calc hist for {first_img_name}")
                return

        result_images = []
        try:
            img_names.remove(first_img_name)  # dont compare against self
        except ValueError:
            print("First img name was not found in img_names")

        for img_name in img_names:
            try:
                current_hist = h5_arr[img_name][:]
            except KeyError:
                current_hist = get_hist_for_file(img_name)

            diff = cv2.compareHist(target_hist, current_hist, cv2.HISTCMP_CORREL)
            if diff > CORRELATION_LIMIT:
                result_images.append(img_name)
                if len(result_images) == search_amount:
                    return result_images

        return result_images


if __name__ == "__main__":
    generate_hist_cache()

    static_folder = './static/*.jpg'
    imgs_in_static_folder = glob.glob(static_folder)
    first_path = str(imgs_in_static_folder[1])
    print(first_path)

    res = get_similar_imgs_by_histogram_correlation(first_path, imgs_in_static_folder)
    print(res)
    if res:
        with Image.open(first_path) as img:
            img.show()

        for path in res:
            with Image.open(path) as img:
                img.show()
