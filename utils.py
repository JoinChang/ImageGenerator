from PIL import Image, ImageDraw
from typing import List, Tuple
import numpy as np

def round_image(image: Image):
    """
    图片圆角处理
    `image`: 原始图片
    """

    mask = Image.new('L', (image.size[0] * 3, image.size[1] * 3), 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + (image.size[0] * 3, image.size[1] * 3), fill=255)
    mask = mask.resize(image.size, Image.ANTIALIAS)
    image.putalpha(mask)
    return image

def perspective_image(image: Image, points: List[Tuple[float, float]]):
    """
    图片透视变换
    `image`: 原始图片
    `points`: 四点坐标（左上、右上、右下、左下）
    """

    def find_coeffs(pa: List[Tuple[float, float]], pb: List[Tuple[float, float]]):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
        A = np.matrix(matrix, dtype=np.float32)
        B = np.array(pb).reshape(8)
        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    img_w, img_h = image.size
    points_w = [p[0] for p in points]
    points_h = [p[1] for p in points]
    new_w = int(max(points_w) - min(points_w))
    new_h = int(max(points_h) - min(points_h))
    p = [(0, 0), (img_w, 0), (img_w, img_h), (0, img_h)]
    coeffs = find_coeffs(points, p)
    return image.transform((new_w, new_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
