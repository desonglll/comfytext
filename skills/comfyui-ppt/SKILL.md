---
name: comfyui_ppt
description: 生成带有 AI 配图的 PowerPoint 演示文稿，使用本地 ComfyUI 引擎生成横版图片
---

# PPT 演示文稿生成器

### Description
根据 JSON 规格文件生成 PowerPoint 演示文稿（.pptx）。在调用此工具之前，你需要先使用 ComfyUI 生成所需的横版配图，然后将所有内容整理为 JSON 规格文件。

### Parameters
- `spec` (string, required): JSON 规格文件的绝对路径。规格文件描述演示文稿的所有幻灯片内容、布局和图片路径。
- `output` (string, required): 输出 .pptx 文件的绝对路径。

### Command
uv run python {baseDir}/../../make_ppt.py --spec "$spec" --output "$output"
