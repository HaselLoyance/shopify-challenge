from typing import Tuple, List
import numpy as np
import base64
import cv2
import lzma
import colorsys


def file_field_to_b64str(file: 'FileField') -> str:
    return base64.b64encode(file.read()).decode('ascii')


def bgr_to_hsv(b: int, g: int, r: int) -> Tuple[int,int,int]:
    hsv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return (int(hsv[0] * 255), int(hsv[1] * 255), int(hsv[2] * 255), )


def is_boring_rgb(r: int, g: int, b: int, margin: int) -> bool:
    # This function basically checks if three color ranges intersect within some margin
    #   or not in O(1)
    r1 = r - margin
    r2 = r + margin
    g1 = g - margin
    g2 = g + margin
    b1 = b - margin
    b2 = b + margin

    # The logic is easier to build when we are just checking if ranges do not overlap.
    #   So we do that and just negate after :)
    return not (
        g2 < r1 or b2 < r1 or r2 < g1 or r2 < b1 or
        r2 < g1 or b2 < g1 or g2 < r1 or g2 < b1 or
        r2 < b1 or g2 < b1 or b2 < r1 or b2 < g1
    )


def compress_bytes(byte_array: bytes) -> bytes:
    return lzma.compress(byte_array, format=lzma.FORMAT_ALONE)


def get_cv_image_from_b64str(b64str: str):
    byte_array = np.frombuffer(base64.b64decode(b64str), np.uint8)
    return cv2.imdecode(byte_array, cv2.IMREAD_COLOR)


def scale_cv_image_to_max_dim(cv_image, max_dim: int, algorithm=cv2.INTER_CUBIC):
    width = cv_image.shape[1]
    height = cv_image.shape[0]

    # If image has adequate size then do nothing
    if width <= max_dim and height <= max_dim:
        return cv_image

    # Calculate how much we need to scale width and height so that the biggest dimension is exactly fixed_dim
    scale = float(max_dim) / (width if width > height else height)
    dimensions = (int(width * scale), int(height * scale),)

    # Resize the image
    return cv2.resize(cv_image, dimensions, algorithm)


def get_cv_image_as_jpeg_bytes(cv_image) -> bytes:
    return cv2.imencode('.jpg', cv_image, )[1].tobytes()


def get_n_dominant_cv_image_colors(cv_image, n: int) -> List[Tuple]:
    # We are doing some kmeans optimization. First, we scale the image down to at most 65px
    #   in the biggest dimensions using nearest neighbor, and only then we do kmeans sampling
    scaled_image = scale_cv_image_to_max_dim(cv_image, 65, cv2.INTER_NEAREST)
    samples = np.float32(scaled_image.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 0.7)

    colors = cv2.kmeans(samples, n, None, criteria, 12, cv2.KMEANS_RANDOM_CENTERS)[2]

    return [ tuple(color) for color in colors ]
