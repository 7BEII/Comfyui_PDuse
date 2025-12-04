import torch
import transformers
import platform
import sys

# 查看 Python 版本
print(f"Python 版本: {platform.python_version()}")

# 查看 PyTorch 版本
print(f"PyTorch 版本: {torch.__version__}")

# 查看 CUDA 是否可用及版本
print(f"CUDA 是否可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"GPU 设备: {torch.cuda.get_device_name(0)}")

# 查看 Transformers 版本
print(f"Transformers 版本: {transformers.__version__}")

# 查看系统信息
print(f"操作系统: {platform.system()} {platform.release()}")