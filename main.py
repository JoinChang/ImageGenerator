from io import BufferedReader
from PIL import Image, ImageDraw, ImageFont
import textwrap
import uuid
import yaml
import sys
import os

PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(PATH)

from lib.pilmoji import Pilmoji
from models import Config, Union, List
from exceptions import *

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

    def generate(self, id: str, input_content: List[Union[bytes, str]] = []):
        if not os.path.isdir(f"{PATH}/res/{id}"):
            return {"code": -1} # 资源文件不存在
        if not os.path.isfile(f"{PATH}/res/{id}.yml"):
            return {"code": -2} # 配置文件不存在
        
        config: Config = self.resource_list[id]
        if config.type == "gif":
            return self._generate_gif(config, input_content)
        elif config.type == "jpg":
            return self._generate_jpg(config, input_content)

        return {"code": -3} # 生成类型不支持
    
    def _generate_gif(self, config: Config, input_content: List[Union[bytes, str]]):
        frames = self._generate_frame(config, input_content)
        save_to = f"{PATH}/temp/{uuid.uuid4()}.gif"
        frames[0].save(save_to, save_all=True, optimize=False, append_images=frames[1:], duration=config.duration, loop=0, disposal=2)
        return {
            "code": 1,
            "path": save_to
        }
    
    def _generate_jpg(self, config: Config, input_content: List[Union[bytes, str]]):
        frames = self._generate_frame(config, input_content)
        save_to = f"{PATH}/temp/{uuid.uuid4()}.jpg"
        frames[0].convert("RGB").save(save_to)
        return {
            "code": 1,
            "path": save_to
        }

    def _generate_frame(self, config: Config, input_content: List[Union[bytes, str]]) -> List:
        background_frame = list()
        foreground_frame = list()
        paste_content = list()
        foreground_paste_task = list()

        # 读取输入图片
        for _input_content in input_content:
            if isinstance(_input_content, BufferedReader):
                paste_content.append(Image.open(_input_content).convert("RGBA"))
            elif isinstance(_input_content, str):
                paste_content.append(_input_content)

        # 预生成背景图与前景图
        sequences = list()
        def append_basic_frame(file_name):
            background_frame.append(Image.new("RGBA", (config.output_size[0], config.output_size[1]), config.background_color))
            foreground_frame.append(Image.open(f"{PATH}/res/{config.id}/{file_name}").convert("RGBA"))
        
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
                _image = paste_content[position_id]
                if not isinstance(_image, Image.Image):
                    raise UnmatchedPositionType(position_id, position.type)
                if position.source is not None:
                    _image = paste_content[position.source]
                
                if position.rounded: # 裁剪为圆形
                    _image = self._round_image(_image)
                
                for frame_id, frame in enumerate(position.frames):
                    if frame.size is None:
                        continue
                    image = _image.resize((frame.size[0], frame.size[1]))
                    if frame.rotate is not None:
                        image = image.rotate(
                            frame.rotate[0], center=None if len(frame.rotate) != 3 else (frame.rotate[1], frame.rotate[2]), expand=True)
                        if not position.rounded: # 旋转后需要重新计算位置
                            _position = (int(frame.x - image.width / 2), int(frame.y - image.height / 2))
                        else:
                            _position = (frame.x, frame.y)
                    else:
                        _position = (frame.x, frame.y)
                    if position.target == "background": # 背景图
                        if len(sequences) != 0:
                            for sequence_frame_id, _frame_id in enumerate(sequences):
                                if frame_id == int(_frame_id):
                                    background_frame[sequence_frame_id].paste(image, _position, image)
                        else:
                            background_frame[frame_id].paste(image, _position, image)
                    elif position.target == "foreground": # 前景图
                        if len(sequences) != 0:
                            for sequence_frame_id, _frame_id in enumerate(sequences):
                                if frame_id == int(_frame_id):
                                    foreground_paste_task.append([position, sequence_frame_id, image, _position])
                        else:
                            foreground_paste_task.append([position, frame_id, image, _position])
            elif position.type == "text":
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
                        if is_wrap: # 自动换行
                            _text = "\n".join(textwrap.wrap(_text, width=int(frame.size[0] / font_size)))
                            # 此处只适用于等宽字符，对于英文、数字等非等宽字符会有所影响
                        if position.multiline:
                            w, h = _font.getsize_multiline(_text)
                        else:
                            w, h = _font.getsize(_text)
                        _position = (int(frame.x - w / 2), int(frame.y - h / 2))
                    else:
                        _position = (frame.x, frame.y)
                    kwargs = {
                        "xy": _position,
                        "text": _text,
                        "fill": position.font.color,
                        "font": _font,
                        "align": position.font.align
                    }
                    if position.target == "background": # 背景图
                        if len(sequences) != 0:
                            for sequence_frame_id, _frame_id in enumerate(sequences):
                                if frame_id == int(_frame_id):
                                    draw = ImageDraw.Draw(background_frame[sequence_frame_id])
                                    draw.multiline_text(**kwargs)
                        else:
                            draw = ImageDraw.Draw(background_frame[frame_id])
                            draw.multiline_text(**kwargs)
                    elif position.target == "foreground": # 前景图
                        if len(sequences) != 0:
                            for sequence_frame_id, _frame_id in enumerate(sequences):
                                if frame_id == int(_frame_id):
                                    foreground_paste_task.append([position, sequence_frame_id, kwargs, font_size])
                        else:
                            foreground_paste_task.append([position, frame_id, kwargs, font_size])
        
        # 粘贴前景图
        for frame_id, frame in enumerate(background_frame):
            background_frame[frame_id].paste(foreground_frame[frame_id], (0, 0, config.output_size[0], config.output_size[1]), foreground_frame[frame_id])
        
        # 为了防止被其他图层覆盖，最后处理前景图队列
        for task in foreground_paste_task:
            position = task[0]
            if position.type == "image":
                background_frame[task[1]].paste(task[2], task[3], task[2])
            if position.type == "text":
                draw = ImageDraw.Draw(background_frame[task[1]])
                draw.multiline_text(**task[2])
                '''
                with Pilmoji(background_frame[task[1]], use_microsoft_emoji=True) as pilmoji:
                    # 此处在线下载 Emoji 并渲染到图片中
                    pilmoji.text(**task[2], emoji_position_offset=(0, int(task[3] / 4)), emoji_scale_factor=5)
                '''
        
        return background_frame

    def _round_image(self, image):
        mask = Image.new('L', (image.size[0] * 3, image.size[1] * 3), 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + (image.size[0] * 3, image.size[1] * 3), fill=255)
        mask = mask.resize(image.size, Image.ANTIALIAS)
        image.putalpha(mask)
        return image