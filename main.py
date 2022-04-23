from io import BufferedReader
from PIL import Image, ImageDraw, ImageFont
from typing import Union, List
import uuid
import yaml
import sys
import os

PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(PATH)

from models import Config
from exceptions import *
from utils import *

class ImageGenerator:
    def __init__(self):
        self.resource_list = dict()
        for file_name in os.listdir(f"{PATH}/res"):
            if os.path.isfile(f"{PATH}/res/{file_name}"):
                self.resource_list[file_name.replace(".yml", "")] = Config.parse_obj(
                    yaml.load(
                        open(f"{PATH}/res/{file_name}", "r", encoding="UTF-8").read(), Loader=yaml.FullLoader))
        
        if not os.path.isdir(f"{PATH}/temp"):
            os.mkdir(f"{PATH}/temp")

    def search_config(self, name: str) -> Config:
        """
        搜索配置
        `name`: 关键词
        """
        for key, value in self.resource_list.items():
            if name.lower() in [value.name, key.lower()]:
                return value 
        return None

    def generate(self, id: str, sources: List[Union[BufferedReader, str]] = []):
        """
        生成图片
        `id`: 配置 ID
        `sources`: 输入内容
        """
        if not os.path.isfile(f"{PATH}/res/{id}.yml"):
            return {"code": -1} # 配置文件不存在
        
        config: Config = self.resource_list[id]

        for source_id, _source in enumerate(config.sources):
            if _source.type == "image":
                if not isinstance(sources[source_id], BufferedReader):
                    return {
                        "code": -2,
                        "type": "image"
                    } # 输入内容不正确
            elif _source.type == "text":
                if not isinstance(sources[source_id], str):
                    return {
                        "code": -2,
                        "type": "text"
                    } # 输入内容不正确
        
        if config.type == "gif":
            return self._generate_gif(config, sources)
        elif config.type == "jpg":
            return self._generate_jpg(config, sources)

        return {"code": -3} # 生成类型不支持
    
    def _generate_gif(self, config: Config, sources: List[Union[BufferedReader, str]]):
        frames = self._generate_frame(config, sources)
        save_to = f"{PATH}/temp/{uuid.uuid4()}.gif"
        frames[0].save(save_to, save_all=True, optimize=False, append_images=frames[1:], duration=config.duration, loop=0, disposal=2)
        return {
            "code": 1,
            "path": save_to
        }
    
    def _generate_jpg(self, config: Config, sources: List[Union[BufferedReader, str]]):
        frames = self._generate_frame(config, sources)
        save_to = f"{PATH}/temp/{uuid.uuid4()}.jpg"
        frames[0].convert("RGB").save(save_to)
        return {
            "code": 1,
            "path": save_to
        }

    def _generate_frame(self, config: Config, sources: List[Union[BufferedReader, str]]) -> List:
        background_frame = list()
        foreground_frame = list()
        paste_content = list()
        foreground_paste_task = list()

        # 读取输入图片
        for _source in sources:
            if isinstance(_source, BufferedReader):
                paste_content.append(Image.open(_source).convert("RGBA"))
            elif isinstance(_source, str):
                paste_content.append(_source)

        # 预生成背景图与前景图
        def append_basic_frame(file_name):
            background_frame.append(Image.new("RGBA", (config.output_size[0], config.output_size[1]), config.background_color))
            foreground_frame.append(Image.open(f"{PATH}/res/{config.id}/{file_name}").convert("RGBA"))
        
        sequences = list()
        if os.path.isdir(f"{PATH}/res/{config.id}"):
            file_list = os.listdir(f"{PATH}/res/{config.id}")
            file_list.sort(key=lambda x: int(x[:-4]))
            if config.sequence is not None: # 自定义队列
                sequences = config.sequence.replace(" ", "").split(",")
                for sequence in sequences:
                    append_basic_frame(f"{int(sequence)}.png")
            else:
                for file_name in file_list:
                    append_basic_frame(file_name)
        
        # 粘贴内容
        for position_id, position in enumerate(config.positions):
            if position.type == "image":
                if position.source is not None:
                    _image = paste_content[position.source]
                else:
                    _image = paste_content[position_id]
                if not isinstance(_image, Image.Image):
                    raise UnmatchedPositionType(position_id, position.type)
                
                if position.rounded: # 裁剪为圆形
                    _image = round_image(_image)
            elif position.type == "text":
                if position.readonly: # 只读
                    _text = position.content
                else:
                    if position.content is not None:
                        for _position_id in range(len(paste_content)):
                            if isinstance(paste_content[_position_id], str):
                                _text = position.content.replace(f"${_position_id}", paste_content[_position_id])
                    else:
                        _text = paste_content[position_id]
                if not isinstance(_text, str):
                    raise UnmatchedPositionType(position_id, position.type)
                for frame_id, frame in enumerate(position.frames):
                    is_wrap = True
                    if isinstance(position.font.size, int):
                        font_size = position.font.size
                        _font = ImageFont.truetype(f"{PATH}/fonts/{position.font.name}", font_size)
                    else: # 自动调整大小
                        min_size = 0
                        max_size = min(*frame.size)
                        if isinstance(position.font.min_size, int):
                            min_size = position.font.min_size
                        if isinstance(position.font.max_size, int):
                            max_size = position.font.max_size
                        _font = ImageFont.truetype(f"{PATH}/fonts/{position.font.name}", min_size)
                        font_size = min_size
                        w, h = _font.getsize(_text)
                        while w < frame.size[0] and h < frame.size[1] and font_size < max_size:
                            # 图片太大会很吃配置，需要减小精细度
                            font_size += int(max_size / 100) if max_size >= 100 else 1
                            w, h = _font.getsize(_text)
                            _font = ImageFont.truetype(f"{PATH}/fonts/{position.font.name}", font_size)
                        if font_size != min_size:
                            is_wrap = False
                    if position.font.align == "center":
                        if is_wrap and position.multiline: # 自动换行
                            _text = "\n".join(wrap_text(_text, font=_font, max_width=frame.size[0]))
                            w, h = _font.getsize_multiline(_text)
                        else:
                            w, h = _font.getsize(_text)
                    _position = (frame.x, frame.y)
                    ascent, descent = _font.getmetrics() # 基线到最低轮廓点的距离，用于防止文字溢出
                    _image = Image.new("RGBA", (w, h + descent), "rgba(0,0,0,0)")
                    draw = ImageDraw.Draw(_image)
                    draw.multiline_text(**{
                        "xy": (0, 0), # _position
                        "text": _text,
                        "fill": position.font.color,
                        "font": _font,
                        "align": position.font.align
                    })
                    frame_x = _position[0]
                    frame_y = _position[1]
                
            for frame_id, frame in enumerate(position.frames):
                if frame.size is None:
                    continue

                if position.type != "text":
                    frame_x = frame.x
                    frame_y = frame.y
                    image = _image.resize((frame.size[0], frame.size[1]))
                else:
                    image = _image
                    if is_wrap: # 本来应该自动换行，但是没有 multiline 参数，所以自动压缩宽度
                        image = image.resize((frame.size[0], h + descent))
                
                if position.perspective: # 变形
                    _ = position.perspective
                    points = list()
                    for point in [_.lt, _.rt, _.rb, _.lb]:
                        points.append(tuple(point))
                    image = perspective_image(image, points)
                
                if frame.rotate is not None:
                    image = image.rotate(
                        frame.rotate[0], center=None if len(frame.rotate) != 3 else (frame.rotate[1], frame.rotate[2]), expand=True)
                    if not position.rounded: # 旋转后需要重新计算位置
                        _position = (int(frame_x - image.width / 2), int(frame_y - image.height / 2))
                    else:
                        _position = (frame_x, frame_y)
                else:
                    if position.type != "text":
                        _position = (frame_x, frame_y)
                    else:
                        _position = (int(frame_x - image.width / 2), int(frame_y - image.height / 2))
                
                if position.target == "background": # 背景图
                    if len(sequences) != 0:
                        for sequence_frame_id, _frame_id in enumerate(sequences):
                            if frame_id == int(_frame_id):
                                if sequence_frame_id >= len(background_frame) - 1:
                                    background_frame.append(Image.new("RGBA", tuple(config.output_size), config.background_color))
                                background_frame[sequence_frame_id].paste(image, _position, image)
                    else:
                        if frame_id >= len(background_frame) - 1:
                            background_frame.append(Image.new("RGBA", tuple(config.output_size), config.background_color))
                        background_frame[frame_id].paste(image, _position, image)
                elif position.target == "foreground": # 前景图
                    if len(sequences) != 0:
                        for sequence_frame_id, _frame_id in enumerate(sequences):
                            if frame_id == int(_frame_id):
                                foreground_paste_task.append([sequence_frame_id, image, _position])
                    else:
                        foreground_paste_task.append([frame_id, image, _position])
        
        # 粘贴前景图
        for frame_id, frame in enumerate(background_frame):
            if frame_id >= len(foreground_frame) - 1:
                foreground_frame.append(Image.new("RGBA", tuple(config.output_size), config.background_color))
            background_frame[frame_id].paste(foreground_frame[frame_id], (0, 0), foreground_frame[frame_id])
        
        # 为了防止被其他图层覆盖，最后处理前景图队列
        for task in foreground_paste_task:
            if frame_id >= len(background_frame) - 1:
                background_frame.append(Image.new("RGBA", tuple(config.output_size), config.background_color))
            background_frame[task[0]].paste(task[1], task[2], task[1])
            '''
            from lib.pilmoji import Pilmoji
            
            with Pilmoji(background_frame[task[1]], use_microsoft_emoji=True) as pilmoji:
                # 此处在线下载 Emoji 并渲染到图片中
                pilmoji.text(**task[2], emoji_position_offset=(0, int(task[3] / 4)), emoji_scale_factor=5)
            '''
        
        return background_frame