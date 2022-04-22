# ImageGenerator

LxBot 图片生成模块。

## 支持的功能
- JPG、GIF 格式图片生成。
- 向背景、前景粘贴多图层内容。
- 自定义 GIF 帧序列。
- 粘贴图层（文本、图片），支持的操作：
  - 裁剪为圆形（仅图片）
  - 旋转
  - 缩放
  - 变形
- 粘贴文本，支持的操作：
  - 自定义字体（`./fonts`）
  - 自定义、自适应字体大小
  - 字体颜色
  - 文本对齐
  - 自动换行
  - Emoji（未完全支持）

## 配置文件示例
```yaml
id: ceng # 表情 ID
name: 蹭 # 表情名
type: gif # 表情类型
duration: 1 # 单帧持续时间 (ms)
background_color: "rgb(255,255,255)" # 背景颜色
positions: # 图层组
  - type: image # 图层类型，目前仅支持图片
    target: foreground # 渲染层，此处为前景
    frames: # 帧数
      - id: 0 # 支持空内容
      - id: 1
        x: 46 # 坐标位置（左上为起点）
        y: 100
        size: # 缩放大小
          - 75
          - 77
        rotate: # 旋转
          - 90 # 旋转角度
          - 0 # 下面两个为旋转中心（x、y），一般不需要这项，默认为图片中心
          - 0
  - type: image # 支持多图层
    target: background # 渲染层，此处为背景
    rounded: true # 是否裁剪为圆形
    source: 0 # 默认为 1，此处使用第一个图层
    frames:
      ...
output_size: # GIF 输出大小（宽、高）
  - 240
  - 240
```
详细参数参见 `./res` 中的配置文件或 `models.py`。
