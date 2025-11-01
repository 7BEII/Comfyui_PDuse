"""
PD节点套件配置文件
管理所有节点的通用设置和常量
"""

import os
from typing import Dict, List, Any

# 版本信息
VERSION = "1.0.0"
AUTHOR = "PD开发团队"
DESCRIPTION = "PD ComfyUI 自定义节点套件"

# 文件路径配置
BASE_DIR = os.path.dirname(__file__)
PY_DIR = os.path.join(BASE_DIR, "py")
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflow")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# 创建必要的目录
os.makedirs(FONTS_DIR, exist_ok=True)

# 支持的图像格式
SUPPORTED_IMAGE_FORMATS = [
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", 
    ".webp", ".gif", ".psd", ".exr", ".hdr"
]

# 张量形状常量
TENSOR_SHAPES = {
    "IMAGE": "B,H,W,C",      # 图像张量形状 (批次, 高度, 宽度, 通道)
    "MASK": "B,H,W",         # 遮罩张量形状 (批次, 高度, 宽度)
    "LATENT": "B,C,H,W",     # 潜在空间张量形状 (批次, 通道, 高度, 宽度)
}

# 默认处理参数
DEFAULT_PARAMS = {
    "BLUR_RADIUS": 2.0,
    "SHARPEN_STRENGTH": 1.5,
    "BRIGHTNESS_FACTOR": 1.2,
    "CONTRAST_FACTOR": 1.1,
    "NOISE_KERNEL_SIZE": 5,
}

# 节点分类
NODE_CATEGORIES = {
    "IMAGE": "PD/图像处理",
    "TOOLS": "PD/工具",
    "TEXT": "PD/文本处理", 
    "UTILITY": "PD/实用工具",
    "IO": "PD/输入输出",
}

# 调试配置
DEBUG_CONFIG = {
    "ENABLE_DEBUG": True,
    "LOG_TENSOR_SHAPES": True,
    "LOG_PROCESSING_TIME": True,
    "VERBOSE_ERRORS": True,
}

def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return globals().get(key, default)

def set_config(key: str, value: Any) -> None:
    """设置配置值"""
    globals()[key] = value

def print_config_info():
    """打印配置信息"""
    print(f"PD节点套件 v{VERSION}")
    print(f"作者: {AUTHOR}")
    print(f"描述: {DESCRIPTION}")
    print(f"基础目录: {BASE_DIR}")
    print(f"支持格式: {len(SUPPORTED_IMAGE_FORMATS)}种")
    print(f"调试模式: {'开启' if DEBUG_CONFIG['ENABLE_DEBUG'] else '关闭'}")

if __name__ == "__main__":
    print_config_info() 