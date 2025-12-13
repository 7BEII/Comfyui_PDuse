"""
文件批量重命名工具
使用说明：
1. 修改下方的配置参数
2. 运行脚本即可

配置说明：
- SOURCE_DIR: 源文件夹路径（包含要重命名的文件）
- TARGET_DIR: 目标文件夹路径（处理后的文件保存位置）
- OLD_KEYWORD: 要被替换的关键词
- NEW_KEYWORD: 替换后的关键词
"""

# ==================== 配置区域 ====================
# 请根据需要修改以下参数

SOURCE_DIR = r"E:\pandy_work\01-测试开发\AITOOLS\宠物_宫廷\Qwen宠物训练\fix"  # 源文件夹路径
TARGET_DIR = r"E:\pandy_work\01-测试开发\AITOOLS\宠物_宫廷\Qwen宠物训练\fix\新建文件夹"  # 目标文件夹路径
OLD_KEYWORD = "T"  # 要被替换的关键词
NEW_KEYWORD = "R"  # 替换后的关键词

# ==================== 代码区域 ====================
# 以下代码无需修改

import os
import shutil

def batch_rename_files(source_dir, target_dir, old_keyword, new_keyword):
    """
    批量重命名文件函数
    
    参数:
        source_dir (str): 源文件夹路径
        target_dir (str): 目标文件夹路径
        old_keyword (str): 要被替换的关键词
        new_keyword (str): 替换后的关键词
    """
    # 检查源文件夹是否存在
    if not os.path.exists(source_dir):
        print(f"❌ 错误：源文件夹 '{source_dir}' 不存在！")
        return False
    
    # 创建目标文件夹（如果不存在）
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"✅ 已创建目标文件夹: {target_dir}")
    
    # 统计处理结果
    total_files = 0
    renamed_files = 0
    skipped_files = 0
    
    print(f"\n🔍 开始扫描文件夹: {source_dir}")
    print(f"📝 替换规则: '{old_keyword}' -> '{new_keyword}'")
    print("-" * 50)
    
    # 遍历源文件夹中的所有文件
    for filename in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, filename)
        
        # 只处理文件，跳过文件夹
        if os.path.isfile(source_file_path):
            total_files += 1
            
            # 检查文件名是否包含要替换的关键词
            if old_keyword in filename:
                # 执行关键词替换
                new_filename = filename.replace(old_keyword, new_keyword)
                target_file_path = os.path.join(target_dir, new_filename)
                
                try:
                    # 复制文件到目标位置
                    shutil.copy2(source_file_path, target_file_path)
                    print(f"✅ {filename} -> {new_filename}")
                    renamed_files += 1
                except Exception as e:
                    print(f"❌ 处理失败 {filename}: {e}")
            else:
                print(f"⏭️  跳过: {filename} (不包含关键词 '{old_keyword}')")
                skipped_files += 1
    
    # 显示处理结果统计
    print("-" * 50)
    print(f"📊 处理完成!")
    print(f"   总文件数: {total_files}")
    print(f"   已重命名: {renamed_files}")
    print(f"   已跳过: {skipped_files}")
    print(f"   输出目录: {target_dir}")
    
    return True

if __name__ == "__main__":
    print("🚀 文件批量重命名工具启动")
    print("=" * 50)
    print(f"源文件夹: {SOURCE_DIR}")
    print(f"目标文件夹: {TARGET_DIR}")
    print(f"替换规则: '{OLD_KEYWORD}' -> '{NEW_KEYWORD}'")
    print("=" * 50)
    
    # 执行批量重命名
    batch_rename_files(SOURCE_DIR, TARGET_DIR, OLD_KEYWORD, NEW_KEYWORD)
    
    input("\n按回车键退出...")
