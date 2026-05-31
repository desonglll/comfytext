#!/usr/bin/env python3
"""
ComfyUI 无头执行脚本
用法: python clone_draw.py --prompt "a beautiful landscape" [--negative "bad quality"] [--comfyui-url http://127.0.0.1:8188]
功能: 读取 base_image.json → 替换 prompt → 发送给 ComfyUI → 轮询等待 → 下载图片 → 打印本地路径
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
WORKFLOW_JSON = SCRIPT_DIR / "base_image.json"
OUTPUT_DIR = SCRIPT_DIR / "images"
COMFYUI_URL = "http://127.0.0.1:8188"

# JSON 中正向/负向提示词对应的节点编号
POSITIVE_NODE = "2"
NEGATIVE_NODE = "3"

# 轮询间隔与超时
POLL_INTERVAL = 2  # 秒
POLL_TIMEOUT = 300  # 5 分钟


def load_workflow(path: Path) -> dict:
    """加载 ComfyUI API 格式的工作流 JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def inject_prompt(workflow: dict, positive: str, negative: str) -> dict:
    """向工作流中注入正向和负向提示词"""
    workflow = json.loads(json.dumps(workflow))  # deep copy
    workflow[POSITIVE_NODE]["inputs"]["text"] = positive
    workflow[NEGATIVE_NODE]["inputs"]["text"] = negative
    # 随机 seed，确保每次生成不同
    import random
    workflow["5"]["inputs"]["seed"] = random.randint(0, 2**63 - 1)
    return workflow


def queue_prompt(workflow: dict, server_url: str) -> str:
    """将工作流提交到 ComfyUI 队列，返回 prompt_id"""
    url = f"{server_url}/prompt"
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ ComfyUI 返回错误 {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def wait_for_completion(prompt_id: str, server_url: str) -> dict:
    """轮询 ComfyUI 直到任务完成，返回 history"""
    url = f"{server_url}/history/{prompt_id}"
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        try:
            with urllib.request.urlopen(url) as resp:
                history = json.loads(resp.read().decode("utf-8"))
                if prompt_id in history:
                    return history[prompt_id]
        except urllib.error.URLError:
            pass
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    print(f"❌ 等待超时 ({POLL_TIMEOUT}s)，任务可能仍在执行", file=sys.stderr)
    sys.exit(1)


def download_output_images(history: dict, server_url: str, output_dir: Path) -> list[str]:
    """从 history 中提取并下载所有输出图片，返回本地路径列表"""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    outputs = history.get("outputs", {})
    for node_id, node_output in outputs.items():
        images = node_output.get("images", [])
        for img_info in images:
            filename = img_info["filename"]
            subfolder = img_info.get("subfolder", "")
            img_type = img_info.get("type", "output")

            # 构建 ComfyUI 的图片获取 URL
            params = urllib.parse.urlencode({
                "filename": filename,
                "subfolder": subfolder,
                "type": img_type,
            })
            fetch_url = f"{server_url}/view?{params}"

            # 生成本地文件名（避免冲突）
            unique_name = f"{Path(filename).stem}_{uuid.uuid4().hex[:8]}{Path(filename).suffix}"
            local_path = output_dir / unique_name

            urllib.request.urlretrieve(fetch_url, str(local_path))
            paths.append(str(local_path))

    return paths


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 无头生图脚本")
    parser.add_argument("--prompt", required=True, help="正向提示词（英文）")
    parser.add_argument("--negative", default="bad hand, blurry, low quality, worst quality", help="负向提示词")
    parser.add_argument("--comfyui-url", default=COMFYUI_URL, help="ComfyUI 服务器地址")
    parser.add_argument("--workflow", default=str(WORKFLOW_JSON), help="工作流 JSON 路径")
    args = parser.parse_args()

    print(f"🎨 正在生成图片...")
    print(f"   Prompt: {args.prompt}")

    # 1. 加载工作流
    workflow = load_workflow(Path(args.workflow))

    # 2. 注入提示词
    workflow = inject_prompt(workflow, args.prompt, args.negative)

    # 3. 提交到 ComfyUI
    prompt_id = queue_prompt(workflow, args.comfyui_url)
    print(f"   任务已提交，prompt_id = {prompt_id}")

    # 4. 等待完成
    history = wait_for_completion(prompt_id, args.comfyui_url)
    print(f"   生成完毕，正在下载...")

    # 5. 下载图片
    paths = download_output_images(history, args.comfyui_url, OUTPUT_DIR)

    if paths:
        for p in paths:
            # ✅ 打印图片路径——这是 OpenClaw 会读取的返回值
            print(p)
    else:
        print("❌ 未生成任何图片", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # 需要 urllib.parse，在顶部未导入的场景下兜底
    import urllib.parse
    main()
