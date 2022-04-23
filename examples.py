from main import ImageGenerator

# ceng, diu 需要两个图片
#generator.generate("cuo", [open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb"), open(r"D:\Documents\约稿\风神chino\2022头像.jpg", "rb")])

generator = ImageGenerator()
config = generator.search_config("喜报")
generator.generate(config.id, ["寄"])