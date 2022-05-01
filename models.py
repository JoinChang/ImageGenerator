from pydantic import BaseModel
from typing import List, Optional

class Frame(BaseModel):
    id: int
    x: Optional[int] = 0
    y: Optional[int] = 0
    size: Optional[List[int]] # image 为缩放: [宽, 高], text 为宽度: [宽]
    rotate: Optional[List[int]] # 旋转: [角度, 中心 x, 中心 y]

class Font(BaseModel):
    name: str # 字体名, 带后缀
    size: Optional[int] # 字体大小, 为空时根据 frame.size 自动调整
    max_size: Optional[int] # 自动调整时的最大字体大小
    min_size: Optional[int] # 自动调整时的最小字体大小
    color: Optional[str] = "black" # 字体颜色
    align: Optional[str] = "center" # 对齐方式, center 时为中心坐标

class Perspective(BaseModel):
    lt: Optional[List[int]] = [0, 0]
    rt: Optional[List[int]] = [0, 0]
    rb: Optional[List[int]] = [0, 0]
    lb: Optional[List[int]] = [0, 0]

class Position(BaseModel):
    type: str # 物件类型: image, text
    target: str # 目标渲染层: background, foreground
    source: Optional[int] # 指定 input_content
    rounded: Optional[bool] = False # 裁剪为圆形
    perspective: Optional[Perspective] # 变形
    readonly: Optional[bool] = False # 只读
    multiline: Optional[bool] = False # 换行 (仅 text)
    max_line: Optional[int] # 最大行数 (仅 text)
    font: Optional[Font] # 字体 (仅 text)
    content: Optional[str] # 内容 (仅 text), 使用 ${source} 替换
    frames: List[Frame]

class Source(BaseModel):
    type: str # 内容类型
    # image
    is_avatar: Optional[bool] = False # 是否为头像, 没有特定
    is_sender_avatar: Optional[bool] = False # 是否是发送者头像
    is_target_avatar: Optional[bool] = False # 是否是目标头像
    # text
    is_username: Optional[bool] = False # 是否为用户名, 没有特定
    is_sender_username: Optional[bool] = False # 是否是发送者名称
    is_target_username: Optional[bool] = False # 是否是目标名称
    is_custom_text: Optional[bool] = False # 是否是自定义文本

class Config(BaseModel):
    id: str
    name: str
    type: str
    positions: List[Position]
    output_size: List[int] # [宽, 高]
    background_color: Optional[str] # 背景颜色
    duration: Optional[float] # 仅 GIF, 单帧持续时间 (ms)
    sequence: Optional[str] # 序列
    sources: List[Source] # 输入内容