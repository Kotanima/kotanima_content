from imagehash import phash
from PIL import Image

img = Image.open("img.jpg")
img_hash = str(phash(img))
print(img_hash)
