from pydantic import BaseModel
from typing import List, Union, Optional

class Frame(BaseModel):
    id: int
    x: Optional[int]
    y: Optional[int]
    size: Optional[List[int]] # 仅 image, 缩放: [宽, 高]
    rotate: Optional[List[int]] # 仅 image, 旋转: [角度, 中心 x, 中心 y]

class Font(BaseModel):
    name: str # 字体名, 带后缀
    size: Optional[int] # 字体大小, 为空时根据 frame.size 自动调整
    max_size: Optional[int] # 自动调整时的最大字体大小
    min_size: Optional[int] # 自动调整时的最小字体大小
    color: Optional[str] = "black" # 字体颜色
    align: Optional[str] = "center" # 对齐方式, center 时为中心坐标

class Position(BaseModel):
    type: str # 物件类型: image, text
    target: str # 目标渲染层: background, foreground
    source: Optional[int] # 指定 input_content
    rounded: Optional[bool] = False # 裁剪为圆形 (仅 image)
    multiline: Optional[bool] = False # 换行 (仅 text)
    font: Optional[Font] # 字体 (仅 text)
    frames: List[Frame]

class Config(BaseModel):
    id: str
    name: str
    type: str
    positions: List[Position]
    output_size: List[int] # [宽, 高]
    background_color: Optional[str] # 背景颜色
    duration: Optional[float] # 仅 GIF, 单帧持续时间 (ms)