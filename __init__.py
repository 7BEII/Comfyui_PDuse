"""
Comfyui_PDuse - PD ComfyUI 自定义节点套件
包含多种实用的图像处理和工具节点
"""

import importlib
import os
import sys

# 设置Web目录，用于加载前端资源
WEB_DIRECTORY = "web"


# 初始化节点映射
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def get_ext_dir(subpath=None, mkdir=False):
    """获取扩展目录路径"""
    dir = os.path.dirname(__file__)
    if subpath is not None:
        dir = os.path.join(dir, subpath)
    return os.path.abspath(dir)

def safe_import_module(module_path, file_name):
    """安全导入模块，避免导入错误导致崩溃"""
    try:
        imported_module = importlib.import_module(module_path)
        
        # 检查模块是否包含所需的映射
        if hasattr(imported_module, 'NODE_CLASS_MAPPINGS'):
            NODE_CLASS_MAPPINGS.update(imported_module.NODE_CLASS_MAPPINGS)
            print(f"✅ 成功加载模块: {file_name}")
        
        if hasattr(imported_module, 'NODE_DISPLAY_NAME_MAPPINGS'):
            NODE_DISPLAY_NAME_MAPPINGS.update(imported_module.NODE_DISPLAY_NAME_MAPPINGS)
            
        return True
        
    except Exception as e:
        print(f"❌ 加载模块 {file_name} 失败: {e}")
        return False

# 动态扫描并加载 py/ 目录下的所有模块
py_dir = get_ext_dir("py")

if os.path.exists(py_dir):
    files = os.listdir(py_dir)
    
    for file in files:
        if not file.endswith(".py") or file.startswith("_"):
            continue
        
        module_name = os.path.splitext(file)[0]
        module_path = f"{__name__}.py.{module_name}"
        
        safe_import_module(module_path, file)
else:
    print(f"警告: py目录不存在: {py_dir}")

# 显示加载信息
if NODE_CLASS_MAPPINGS:
    print("=" * 50)
    print("🎨 Comfyui_PDuse 节点套件加载完成")
    print("=" * 50)
    print(f"📦 总计加载节点数量: {len(NODE_CLASS_MAPPINGS)}")
    print("📋 已加载的节点:")
    for name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
        print(f"  • {display_name}")
    print("=" * 50)
else:
    print("⚠️  警告: 没有找到任何可用的节点")

# 导出变量
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
