from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont
from typing import List, Tuple
import numpy as np

def wrap_text(text: str, font: FreeTypeFont, max_width: float, **kwargs) -> List[str]:
    """
    文本自动换行
    `text`: 文本
    `font`: 字体
    `max_width`: 最大宽度
    `kwargs`: 其他参数
    """
    line = ""
    lines = []
    for t in text:
        if t == "\n":
            lines.append(line)
            line = ""
        elif font.getsize_multiline(line + t, **kwargs)[0] > max_width:
            lines.append(line)
            line = t
        else:
            line += t
    lines.append(line)
    return lines

def round_image(image: Image) -> Image:
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

def perspective_image(image: Image, points: List[Tuple[float, float]]) -> Image:
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
