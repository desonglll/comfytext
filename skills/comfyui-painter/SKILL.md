---
name: comfyui_painter
description: 调用本地 ComfyUI 引擎进行图像生成，用于文图混排配图
---

# ComfyUI 画笔工具

### Description
当用户要求你生成图片、插图、视觉原画，或者需要为文章进行文图混排配图时，调用此工具。
该工具会启动本地的 ComfyUI 渲染引擎生成图像，并返回图像保存在本地的路径。

### Parameters
- `prompt` (string, required): 极其详细的英文画面描述（Prompt）。由于底层是 Stable Diffusion 架构，请务必将用户的中文意图转化为高质量的英文描述。

### Command
uv run python {baseDir}/../../clone_draw.py --prompt "$prompt"
