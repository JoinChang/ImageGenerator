from pydantic import BaseModel
from typing import List, Optional

class Frame(BaseModel):
    id: int
    x: Optional[int]
    y: Optional[int]
    size: Optional[List[int]] # 缩放: [宽, 高]
    rotate: Optional[List[int]] # 旋转: [角度, 中心 x, 中心 y]

class Position(BaseModel):
    type: str # 物件类型: image
    target: str # 目标渲染层: background, foreground
    rounded: Optional[bool] # 裁剪为圆形 (仅 image)
    source: Optional[int] # 指定图片序号
    frames: List[Frame]

class GIF(BaseModel):
    id: str
    name: str
    type: str
    duration: float # 单帧持续时间 (ms)
    background_color: str # 背景颜色
    positions: List[Position]
    output_size: List[int] # [宽, 高]