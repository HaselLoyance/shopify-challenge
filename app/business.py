from django.core.files.base import ContentFile
from django.utils import timezone
from app.models import Image
from app.helpers import (
    bgr_to_hsv,
    get_cv_image_from_b64str,
    scale_cv_image_to_max_dim,
    get_n_dominant_cv_image_colors,
    get_cv_image_as_jpeg_bytes,
    compress_bytes,
    is_boring_rgb,
)
import uuid
from typing import List, Union, Tuple

# How big the images' largest dimension should be (pixels)
MAX_DIM = 400

# How many dominant colors we must extract from the picture. Must be at most 4, since that's what the model supports
DOMINANT_COLORS = 4 

# When checking if the color is boring we are comparing R/G/B values to see if all of them are close to each other
#   This constant tells how close they need to be considered boring
BORING_MARGIN = 20


def save_images(data: List[str], is_local=True) -> None:
    images = []

    for image in data:
        added = create_image_instance(image, is_local)

        if added:
            images.append(added)

    Image.objects.bulk_create(images)


def create_image_instance(data: str, is_local=True) -> Union[None, Image]:
    try:
        # Read images and get dominant colors
        cv_image = get_cv_image_from_b64str(data)
        cv_image = scale_cv_image_to_max_dim(cv_image, MAX_DIM)
        dominant_colors_bgr = get_n_dominant_cv_image_colors(cv_image, DOMINANT_COLORS)
        dominant_colors_hsv = [ bgr_to_hsv(color[0], color[1], color[2]) for color in dominant_colors_bgr ]

        # Detect white-black-gray colors. If they are not the only dominant, then just set that
        #   hue to some unreachable value, so they are never reached when querying the database.
        #   If they are the only colors though, then we just skip adding this image
        only_boring = True
        hues = []
        for i in range(len(dominant_colors_hsv)):
            r = dominant_colors_bgr[i][2]
            g = dominant_colors_bgr[i][1]
            b = dominant_colors_bgr[i][0]

            if is_boring_rgb(r,g,b, BORING_MARGIN):
                hues.append(10000)
            else:
                only_boring = False
                hues.append(dominant_colors_hsv[i][0])

        if only_boring:
            return None

        # Compress jpeg bytes
        byte_array = get_cv_image_as_jpeg_bytes(cv_image)
        compressed_bytes = compress_bytes(byte_array)

        # And finally save it in the database, while doing some Django trickery for saving in-memory binary data
        image = Image(is_local=is_local)
        image.file = ContentFile(compressed_bytes)
        image.file.name = str(uuid.uuid4()).replace('-', '') + '.lzma'

        for i in range(len(hues)):
            setattr(image, f'hue{i+1}', hues[i])

        return image
    except:
        pass

    return None


def delete_image(id: int) -> None:
    Image.objects.filter(id=id, effective_to=None).update(effective_to=timezone.now())
