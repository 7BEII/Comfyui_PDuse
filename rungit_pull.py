#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git 自动推送脚本（智能合并版本）
功能：自动执行 git add, commit, push 操作
特性：遇到冲突时自动拉取并合并远程更改，保留所有历史记录
      冲突时优先使用本地版本，确保新版本能够推送
使用：python rungit_pull.py [提交信息]
"""

import subprocess
import sys
import re
from datetime import datetime


def run_command(command, shell=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def get_branch_info():
    """获取当前分支信息"""
    code, stdout, _ = run_command("git branch --show-current")
    return stdout.strip() if code == 0 else "未知"


def get_remote_info():
    """获取远程仓库信息"""
    code, stdout, _ = run_command("git remote -v")
    return stdout.strip() if code == 0 else "未配置"


def check_git_status():
    """检查 Git 状态"""
    code, stdout, _ = run_command("git status --short")
    return code == 0, stdout.strip()


def get_detailed_diff():
    """获取详细的文件修改信息"""
    code, stdout, _ = run_command("git diff --cached --numstat")
    if code != 0 or not stdout.strip():
        return []
    
    files = []
    for line in stdout.strip().split('\n'):
        parts = line.split('\t')
        if len(parts) == 3:
            added = parts[0]
            deleted = parts[1]
            filename = parts[2]
            files.append({
                'file': filename,
                'added': added if added != '-' else '0',
                'deleted': deleted if deleted != '-' else '0'
            })
    return files


def get_file_changes():
    """获取每个文件的具体行改动"""
    code, stdout, _ = run_command("git diff --cached --unified=0")
    if code != 0 or not stdout.strip():
        return {}
    
    changes = {}
    current_file = None
    
    for line in stdout.split('\n'):
        # 检测文件名
        if line.startswith('+++'):
            # 提取文件名 (去掉 b/ 前缀)
            current_file = line[6:] if line.startswith('+++ b/') else line[4:]
            if current_file not in changes:
                changes[current_file] = []
        # 检测修改的行号范围
        elif line.startswith('@@') and current_file:
            # 格式: @@ -oldstart,oldcount +newstart,newcount @@
            match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                if old_count == 0:  # 纯新增
                    changes[current_file].append({
                        'type': '新增',
                        'lines': f"{new_start}-{new_start + new_count - 1}" if new_count > 1 else str(new_start),
                        'count': new_count
                    })
                elif new_count == 0:  # 纯删除
                    changes[current_file].append({
                        'type': '删除',
                        'lines': f"{old_start}-{old_start + old_count - 1}" if old_count > 1 else str(old_start),
                        'count': old_count
                    })
                else:  # 修改
                    changes[current_file].append({
                        'type': '修改',
                        'lines': f"{new_start}-{new_start + new_count - 1}" if new_count > 1 else str(new_start),
                        'count': new_count
                    })
    
    return changes


def main():
    # 获取分支信息
    current_branch = get_branch_info()
    
    # 检查远程仓库
    remote_info = get_remote_info()
    if remote_info == "未配置":
        print("❌ 错误: 未配置远程仓库")
        return
    
    # 检查是否有更改
    success, status = check_git_status()
    
    if not success:
        print("❌ 错误: 无法获取 Git 状态，请确保当前目录是 Git 仓库")
        return
    
    if not status:
        # 检查是否有未推送的提交
        code, stdout, _ = run_command(f"git log origin/{current_branch}..HEAD --oneline")
        if stdout.strip():
            print(f"📤 推送未提交...")
            code, stdout, stderr = run_command(f"git push origin {current_branch}")
            
            if code == 0:
                print(f"✅ 推送成功!")
            else:
                if "rejected" in stderr or "non-fast-forward" in stderr:
                    print("⚠️ 冲突，正在合并...")
                    code, stdout, stderr = run_command(f"git pull --rebase -X ours origin {current_branch}")
                    if code == 0:
                        code, stdout, stderr = run_command(f"git push origin {current_branch}")
                        if code == 0:
                            print(f"✅ 推送成功!")
                        else:
                            print(f"❌ 推送失败: {stderr}")
                    else:
                        print(f"❌ 合并失败: {stderr}")
                else:
                    print(f"❌ 推送失败: {stderr}")
        else:
            print("✅ 已是最新")
        return
    
    # 添加所有更改
    code, stdout, stderr = run_command("git add .")
    if code != 0:
        print(f"❌ 添加失败: {stderr}")
        return
    
    # 显示修改信息
    print(f"\n📝 更新文件 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    file_stats = get_detailed_diff()
    if file_stats:
        for stat in file_stats:
            filename = stat['file']
            added = int(stat['added']) if stat['added'] != '-' else 0
            deleted = int(stat['deleted']) if stat['deleted'] != '-' else 0
            
            changes = []
            if added > 0:
                changes.append(f"+{added}")
            if deleted > 0:
                changes.append(f"-{deleted}")
            
            change_str = " ".join(changes) if changes else "修改"
            print(f"  • {filename} ({change_str})")
    else:
        print("  • 无具体修改详情")
    
    # 提交更改
    if len(sys.argv) > 1:
        commit_message = " ".join(sys.argv[1:])
    else:
        commit_message = f"自动提交 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    code, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    
    if code != 0 and "nothing to commit" not in stderr:
        print(f"❌ 提交失败: {stderr}")
        return
    
    # 推送到远程
    print(f"\n📤 推送中...")
    code, stdout, stderr = run_command(f"git push origin {current_branch}")
    
    if code == 0:
        print(f"✅ 推送成功!")
    else:
        # 检查是否需要设置上游分支
        if "set-upstream" in stderr or "no upstream" in stderr:
            code, stdout, stderr = run_command(f"git push -u origin {current_branch}")
            if code == 0:
                print(f"✅ 推送成功!")
            else:
                if "rejected" in stderr or "non-fast-forward" in stderr:
                    print("⚠️ 冲突，正在合并...")
                    run_command("git fetch origin")
                    code, stdout, stderr = run_command(f"git pull --rebase -X ours origin {current_branch}")
                    if code == 0:
                        code, stdout, stderr = run_command(f"git push -u origin {current_branch}")
                        if code == 0:
                            print(f"✅ 推送成功!")
                        else:
                            print(f"❌ 推送失败: {stderr}")
                            return
                    else:
                        print(f"❌ 合并失败: {stderr}")
                        return
                else:
                    print(f"❌ 推送失败: {stderr}")
                    return
        elif "rejected" in stderr or "non-fast-forward" in stderr:
            print("⚠️ 冲突，正在合并...")
            code, stdout, stderr = run_command(f"git pull --rebase -X ours origin {current_branch}")
            if code == 0:
                code, stdout, stderr = run_command(f"git push origin {current_branch}")
                if code == 0:
                    print(f"✅ 推送成功!")
                else:
                    print(f"❌ 推送失败: {stderr}")
                    return
            else:
                print(f"❌ 合并失败: {stderr}")
                return
        else:
            print(f"❌ 推送失败: {stderr}")
            return
    
    # 显示提交历史
    print(f"\n📜 提交历史 (最近3条):")
    code, stdout, _ = run_command("git log --oneline -3")
    if code == 0 and stdout.strip():
        for line in stdout.strip().split('\n'):
            print(f"  • {line}")
    
    print(f"\n✅ 完成! [{current_branch}]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)

