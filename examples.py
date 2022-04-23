from main import ImageGenerator
import sys

# ceng, diu 需要两个图片
#generator.generate("cuo", [open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb"), open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb")])

generator = ImageGenerator()
config = generator.search_config("xts")
print(generator.generate(config.id, ["Lxns", open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb")]))