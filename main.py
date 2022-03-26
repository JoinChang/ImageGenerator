from PIL import Image, ImageDraw
import uuid
import yaml
import os

from models import GIF, List

PATH = os.path.dirname(os.path.realpath(__file__))

class ImageGenerator:
    def __init__(self):
        self.resource_list = dict()
        for file_name in os.listdir(f"{PATH}/res"):
            if os.path.isfile(f"{PATH}/res/{file_name}"):
                self.resource_list[file_name.replace(".yml", "")] = GIF.parse_obj(
                    yaml.load(open(f"{PATH}/res/{file_name}", "r", encoding="UTF-8").read()))

    def generate(self, id: str, input_file_bytes: List[bytes] = []):
        if not os.path.isdir(f"{PATH}/res/{id}"):
            return {"code": -1} # 资源文件不存在
        if not os.path.isfile(f"{PATH}/res/{id}.yml"):
            return {"code": -2} # 配置文件不存在
        
        config: GIF = self.resource_list[id]
        os.path.split
        if config.type == "gif":
            return self._generate_gif(config, input_file_bytes)

        return {"code": -3} # 生成类型不支持
    
    def _generate_gif(self, config: GIF, input_file_bytes: List[bytes]):
        frames = self._generate_frame(config, input_file_bytes)
        save_to = f"{PATH}/temp/{uuid.uuid4()}.gif"
        frames[0].save(save_to, save_all=True, optimize=False, append_images=frames[1:], duration=config.duration, loop=0, disposal=2)
        return {
            "code": 1,
            "path": save_to
        }

    def _generate_frame(self, config: GIF, input_file_bytes: List[bytes]) -> List:
        background_frame = list()
        foreground_frame = list()
        paste_image = list()
        foreground_paste_task = list()

        # 读取输入图片
        for input_file in input_file_bytes:
            paste_image.append(Image.open(input_file).convert("RGBA"))

        # 预生成背景图与前景图
        file_list = os.listdir(f"{PATH}/res/{config.id}")
        file_list.sort(key=lambda x: int(x[:-4]))
        for file_name in file_list:
            background_frame.append(Image.new("RGBA", (config.output_size[0], config.output_size[1]), config.background_color))
            foreground_frame.append(Image.open(f"{PATH}/res/{config.id}/{file_name}").convert("RGBA"))
        
        # 粘贴内容
        for position_id, position in enumerate(config.positions):
            if position.type == "image":
                _image = paste_image[position_id]
                if position.source is not None:
                    _image = paste_image[position.source]
                if position.rounded:
                    mask = Image.new('L', (_image.size[0] * 3, _image.size[1] * 3), 0)
                    draw = ImageDraw.Draw(mask) 
                    draw.ellipse((0, 0) + (_image.size[0] * 3, _image.size[1] * 3), fill=255)
                    mask = mask.resize(_image.size, Image.ANTIALIAS)
                    _image.putalpha(mask)
                for frame_id, frame in enumerate(position.frames):
                    if frame.size is None:
                        continue
                    image = _image.resize((frame.size[0], frame.size[1]))
                    if frame.rotate is not None:
                        image = image.rotate(
                            frame.rotate[0], center=None if len(frame.rotate) != 3 else (frame.rotate[1], frame.rotate[2]), expand=True)
                        if not position.rounded:
                            _position = (int(frame.x - image.width / 2), int(frame.y - image.height / 2)) # 旋转后需要重新计算位置
                        else:
                            _position = (frame.x, frame.y)
                    else:
                        _position = (frame.x, frame.y)
                    if position.target == "background": # 背景图
                        background_frame[frame_id].paste(image, _position, image)
                    elif position.target == "foreground": # 前景图
                        foreground_paste_task.append([frame_id, image, _position])
        
        # 粘贴前景图
        for frame_id, frame in enumerate(background_frame):
            background_frame[frame_id].paste(foreground_frame[frame_id], (0, 0, config.output_size[0], config.output_size[1]), foreground_frame[frame_id])
        
        # 为了防止被其他图层覆盖，最后处理前景图队列
        for task in foreground_paste_task:
            background_frame[task[0]].paste(task[1], task[2], task[1])
        
        return background_frame

# ceng, diu 需要两个图片
# ImageGenerator().generate("diu", [open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb"), open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb")])