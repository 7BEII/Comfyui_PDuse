#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 自动同步工具
用法: python gitrun.py [命令]

命令说明:
  push         - 强制推送本地到远程-覆盖
  pull         - 强制拉取远程到本地-覆盖
  sync         - 智能同步（先拉取合并，再推送）
  status       - 查看本地与远程的差异（显示文件变更统计）
  log          - 查看提交历史并支持快速回退版本（输入数字选择）
  history      - 查看完整提交历史
  config       - 配置远程仓库地址

重要说明: 所有历史提交都保存在 .git 目录中，永不丢失
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

CONFIG_FILE = Path.home() / '.gitrun_config.json'


class GitSyncTool:
    def __init__(self):
        self.config = self.load_config()
        self.repo_path = os.getcwd()
        
    def load_config(self):
        """加载配置文件"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        """保存配置文件"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def run_command(self, cmd, check=True, silent=False):
        """执行命令并返回结果"""
        try:
            # Windows 上使用 GBK 编码，其他系统使用 UTF-8
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding=encoding,
                errors='ignore'  # 忽略无法解码的字符
            )
            if check and result.returncode != 0:
                if not silent:
                    print(f"❌ 命令执行失败: {cmd}")
                    if result.stderr:
                        print(f"错误信息: {result.stderr}")
                return None
            return result
        except Exception as e:
            if not silent:
                print(f"❌ 执行命令时出错: {e}")
            return None
    
    def is_git_repo(self):
        """检查当前目录是否是 Git 仓库"""
        result = self.run_command("git rev-parse --is-inside-work-tree", check=False, silent=True)
        return result and result.returncode == 0
    
    def get_current_branch(self):
        """获取当前分支名"""
        result = self.run_command("git branch --show-current", silent=True)
        return result.stdout.strip() if result else None
    
    def has_changes(self):
        """检查是否有未提交的更改"""
        result = self.run_command("git status --porcelain", silent=True)
        return bool(result and result.stdout.strip())
    
    def get_remote_url(self):
        """获取远程仓库地址"""
        result = self.run_command("git remote get-url origin", check=False, silent=True)
        return result.stdout.strip() if result and result.returncode == 0 else None
    
    def config_remote(self):
        """配置远程仓库地址"""
        print("🔧 配置远程仓库地址")
        
        # 检查是否是 Git 仓库，如果不是则初始化
        if not self.is_git_repo():
            print("⚠️  当前目录不是 Git 仓库")
            init = input("是否初始化为 Git 仓库? (y/n): ").strip().lower()
            if init == 'y':
                result = self.run_command("git init")
                if result:
                    print("✅ Git 仓库初始化成功")
                else:
                    print("❌ Git 仓库初始化失败")
                    return
            else:
                print("❌ 操作已取消")
                return
        
        current_url = self.get_remote_url()
        if current_url:
            print(f"当前远程仓库: {current_url}")
            change = input("是否修改? (y/n): ").strip().lower()
            if change != 'y':
                return
        
        remote_url = input("请输入远程仓库地址 (如: https://github.com/username/repo.git): ").strip()
        
        if not remote_url:
            print("❌ 远程仓库地址不能为空")
            return
        
        # 检查是否已有 origin
        if current_url:
            result = self.run_command(f"git remote set-url origin {remote_url}")
        else:
            result = self.run_command(f"git remote add origin {remote_url}")
        
        if result:
            print(f"✅ 远程仓库配置成功: {remote_url}")
            
            # 保存到配置文件
            repo_name = os.path.basename(self.repo_path)
            if repo_name not in self.config:
                self.config[repo_name] = {}
            self.config[repo_name]['remote_url'] = remote_url
            self.save_config()
            
            # 询问是否设置默认分支
            print("\n💡 提示: 首次推送前需要设置默认分支")
            set_branch = input("是否设置默认分支为 main? (y/n): ").strip().lower()
            if set_branch == 'y':
                # 检查当前分支
                current_branch = self.get_current_branch()
                if not current_branch:
                    # 创建初始提交
                    print("\n📝 创建初始提交...")
                    self.run_command("git add .")
                    self.run_command('git commit -m "Initial commit" --allow-empty')
                    self.run_command("git branch -M main")
                    print("✅ 默认分支已设置为 main")
                elif current_branch != 'main':
                    self.run_command("git branch -M main")
                    print("✅ 分支已重命名为 main")
                else:
                    print("✅ 当前分支已是 main")
    
    def commit_changes(self, message=None):
        """提交本地更改"""
        if not self.has_changes():
            print("ℹ️  没有需要提交的更改")
            return True
        
        print("\n📝 检测到以下更改:")
        self.run_command("git status --short")
        
        if message is None:
            message = input("\n请输入提交信息: ").strip()
        
        if not message:
            print("❌ 提交信息不能为空")
            return False
        
        # 添加所有更改
        print("\n📦 正在暂存所有更改...")
        result = self.run_command("git add -A")
        if not result:
            return False
        
        # 提交更改
        print(f"💾 正在提交: {message}")
        result = self.run_command(f'git commit -m "{message}"')
        if result:
            print(f"✅ 提交成功")
            return True
        return False
    
    def force_push(self):
        """纯粹的本地覆盖远程（不拉取，直接强制推送）"""
        print("🚀 强制推送本地到远程")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        if not branch:
            print("❌ 无法获取当前分支")
            return
        
        print(f"📍 当前分支: {branch}")
        
        # 检查远程仓库
        remote_url = self.get_remote_url()
        if not remote_url:
            print("⚠️  未配置远程仓库")
            self.config_remote()
            remote_url = self.get_remote_url()
            if not remote_url:
                return
        
        print(f"🌐 远程仓库: {remote_url}")
        
        # 提交本地更改
        print()
        if not self.commit_changes():  # 改为交互式提交，不自动
            print("❌ 提交失败，推送中止")
            return
        
        # 强制推送（不拉取远程）
        print(f"\n⬆️  正在强制推送到远程 ({branch})...")
        result = self.run_command(f"git push -f origin {branch}")
        
        if result:
            print(f"\n✅ 推送成功!")
        else:
            print("\n❌ 推送失败")
    
    def force_pull(self):
        """纯粹的远程覆盖本地（不保留本地未推送的修改）"""
        print("⬇️  强制拉取远程到本地")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        if not branch:
            print("❌ 无法获取当前分支")
            return
        
        print(f"📍 当前分支: {branch}")
        
        # 检查远程仓库
        remote_url = self.get_remote_url()
        if not remote_url:
            print("⚠️  未配置远程仓库")
            self.config_remote()
            return
        
        print(f"🌐 远程仓库: {remote_url}")
        
        # 检查本地更改
        if self.has_changes():
            print("\n⚠️  检测到未提交的本地更改，这些更改将会被丢弃")
            self.run_command("git status --short")
        
        # 先获取远程最新信息
        print(f"\n📡 正在获取远程仓库信息...")
        self.run_command("git fetch origin")
        
        # 强制重置到远程版本
        print(f"⬇️  正在强制拉取远程 ({branch})...")
        self.run_command(f"git reset --hard origin/{branch}")
        self.run_command("git clean -fd")
        
        print(f"\n✅ 拉取成功!")
    
    def smart_sync(self):
        """智能同步（先拉取合并，再推送）"""
        print("🔄 智能同步")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        if not branch:
            print("❌ 无法获取当前分支")
            return
        
        print(f"📍 当前分支: {branch}")
        
        # 检查远程仓库
        remote_url = self.get_remote_url()
        if not remote_url:
            print("⚠️  未配置远程仓库")
            self.config_remote()
            return
        
        print(f"🌐 远程仓库: {remote_url}")
        
        # 提交本地更改
        print()
        if self.has_changes():
            if not self.commit_changes():  # 改为交互式提交
                print("❌ 提交失败")
                return
        
        # 拉取远程更改
        print(f"\n⬇️  正在拉取远程更新 ({branch})...")
        result = self.run_command(f"git pull origin {branch}", check=False)
        
        if result and result.returncode != 0:
            # 如果有冲突
            if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
                print("\n⚠️  检测到合并冲突!")
                print("\n冲突文件:")
                self.run_command("git diff --name-only --diff-filter=U")
                
                choice = input("\n选择操作:\n1. 保留本地版本\n2. 保留远程版本\n3. 手动解决后继续\n请选择 (1/2/3): ").strip()
                
                if choice == '1':
                    self.run_command("git checkout --ours .")
                    self.run_command("git add -A")
                    self.run_command('git commit --no-edit')
                    print("✅ 已保留本地版本")
                elif choice == '2':
                    self.run_command("git checkout --theirs .")
                    self.run_command("git add -A")
                    self.run_command('git commit --no-edit')
                    print("✅ 已保留远程版本")
                else:
                    print("ℹ️  请手动解决冲突后执行: git add . && git commit")
                    return
            else:
                print("❌ 拉取失败")
                return
        else:
            print("✅ 拉取成功")
        
        # 推送到远程
        print(f"\n⬆️  正在推送到远程 ({branch})...")
        push_result = self.run_command(f"git push origin {branch}")
        
        if push_result:
            print(f"\n✅ 同步成功!")
        else:
            print("⚠️  推送失败或无新内容需要推送")
    
    def show_status(self):
        """查看本地与远程仓库的差异"""
        print("📊 本地与远程仓库差异")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        if not branch:
            print("❌ 无法获取当前分支")
            return
        
        # 检查远程仓库
        remote_url = self.get_remote_url()
        if not remote_url:
            print("⚠️  未配置远程仓库")
            return
        
        print(f"🌐 仓库地址: {remote_url}")
        
        # 获取远程最新信息
        self.run_command("git fetch origin", check=False, silent=True)
        
        # 获取远程最新提交时间
        remote_time_result = self.run_command(f"git log -1 --format=%ci origin/{branch}", check=False, silent=True)
        if remote_time_result and remote_time_result.returncode == 0 and remote_time_result.stdout.strip():
            print(f"📅 远程更新时间: {remote_time_result.stdout.strip()}")
        
        # 获取本地当前时间（工作区最后修改时间）
        print(f"📅 本地当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 直接对比当前工作区与远程仓库的差异（包括未提交的更改）
        print("\n📝 变更统计 (本地相对于远程):")
        print("   说明: (+) 代表本地新增的内容，(-) 代表本地已删除的内容")
        
        # 使用 --stat 只显示文件统计，不显示具体内容
        diff_result = self.run_command(f"git diff --stat origin/{branch}", check=False, silent=True)
        if diff_result and diff_result.stdout.strip():
            print(diff_result.stdout)
        else:
            print("✅ 本地与远程完全同步，无差异")
    
    def show_log(self, num=10):
        """查看提交历史并支持直接回退"""
        print(f"📋 最近 {num} 次提交历史")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        print(f"📍 当前分支: {branch}\n")
        
        # 使用 git log 的简单格式，然后解析
        result = self.run_command(f'git log -{num} --format="COMMIT_START%nHASH:%H%nSUBJECT:%s%nAUTHOR:%an%nDATE:%ar%nCOMMIT_END"')
        
        if not result:
            return
        
        commits = result.stdout.strip().split('COMMIT_START')
        commit_hashes = []
        idx = 1
        
        for commit in commits:
            if not commit.strip():
                continue
                
            lines = commit.strip().split('\n')
            commit_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    commit_info[key] = value.strip()
            
            if 'HASH' in commit_info:
                hash_full = commit_info['HASH']
                hash_short = hash_full[:7]
                subject = commit_info.get('SUBJECT', '')
                date = commit_info.get('DATE', '')
                
                commit_hashes.append(hash_full)
                print(f"{idx}. [{hash_short}] {subject} -- {date}")
                idx += 1
        
        # 询问是否回退
        print()
        choice = input("是否回退版本? (输入数字1-10回退，直接回车或输入0跳过): ").strip()
        
        if not choice or choice == '0':
            print("✅ 未进行回退")
            return
        
        # 判断是数字还是哈希值
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(commit_hashes):
                commit_hash = commit_hashes[idx][:7]
            else:
                print(f"❌ 无效的数字，请输入 1-{len(commit_hashes)}")
                return
        else:
            commit_hash = choice
        
        # 验证提交是否存在
        verify = self.run_command(f"git cat-file -t {commit_hash}", check=False, silent=True)
        if not verify or verify.returncode != 0:
            print(f"❌ 提交 {commit_hash} 不存在")
            return
        
        # 显示目标提交信息
        print(f"\n📍 即将回退到: {commit_hash}")
        
        # 选择回退方式
        print("\n回退方式:")
        print("1. 软回退 (保留工作区和暂存区的更改)")
        print("2. 混合回退 (保留工作区更改，清空暂存区) [推荐]")
        print("3. 硬回退 (完全回退，丢弃所有更改)")
        
        mode_choice = input("\n请选择 (1/2/3，直接回车默认选2): ").strip()
        
        if not mode_choice:
            mode_choice = '2'
        
        mode_map = {
            '1': ('--soft', '软回退'),
            '2': ('--mixed', '混合回退'),
            '3': ('--hard', '硬回退')
        }
        
        if mode_choice not in mode_map:
            print("❌ 无效选择")
            return
        
        mode, mode_name = mode_map[mode_choice]
        
        # 执行回退
        print(f"\n⏮️  正在执行{mode_name}...")
        result = self.run_command(f"git reset {mode} {commit_hash}")
        
        if result:
            print(f"\n✅ {mode_name}成功!")
            print(f"📍 已回退到: {commit_hash}\n")
            self.run_command("git status --short")
        else:
            print(f"\n❌ 回退失败")
    
    def show_full_history(self):
        """查看完整提交历史"""
        print("📚 完整提交历史")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        branch = self.get_current_branch()
        print(f"📍 当前分支: {branch}\n")
        
        # 显示完整历史（简化格式以兼容 Windows）
        self.run_command("git log --graph --oneline --decorate --all")
    
    def rollback(self):
        """回退到指定版本"""
        print("⏮️  版本回退")
        
        if not self.is_git_repo():
            print("❌ 当前目录不是 Git 仓库")
            return
        
        # 显示最近10次提交
        print("📋 最近10次提交:\n")
        result = self.run_command("git log -10 --pretty=format:%H|%s|%an|%ar")
        
        if not result:
            return
        
        lines = result.stdout.strip().split('\n')
        commits = []
        
        for i, line in enumerate(lines, 1):
            if '|' in line:
                hash_full, subject, author, date = line.split('|', 3)
                hash_short = hash_full[:7]
                commits.append(hash_full)
                print(f"{i}. [{hash_short}] {subject}")
                print(f"   作者: {author} | 时间: {date}\n")
        
        print()
        
        # 获取用户输入
        choice = input("请输入要回退到的版本 (输入数字1-10，或输入提交哈希值，q 取消): ").strip()
        
        if not choice or choice.lower() == 'q':
            print("❌ 操作已取消")
            return
        
        # 判断是数字还是哈希值
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(commits):
                commit_hash = commits[idx][:7]
            else:
                print(f"❌ 无效的数字，请输入 1-{len(commits)}")
                return
        else:
            commit_hash = choice
        
        # 验证提交是否存在
        verify = self.run_command(f"git cat-file -t {commit_hash}", check=False, silent=True)
        if not verify or verify.returncode != 0:
            print(f"❌ 提交 {commit_hash} 不存在")
            return
        
        # 显示目标提交信息
        print(f"\n📍 即将回退到:")
        self.run_command(f"git log -1 {commit_hash} --pretty=format:[%h] %s%n作者: %an | 时间: %ar")
        
        # 选择回退方式
        print("\n\n回退方式:")
        print("1. 软回退 (保留工作区和暂存区的更改)")
        print("2. 混合回退 (保留工作区更改，清空暂存区) [推荐]")
        print("3. 硬回退 (完全回退，丢弃所有更改)")
        
        mode_choice = input("\n请选择 (1/2/3，输入 q 取消): ").strip()
        
        if mode_choice.lower() == 'q':
            print("❌ 操作已取消")
            return
        
        mode_map = {
            '1': ('--soft', '软回退'),
            '2': ('--mixed', '混合回退'),
            '3': ('--hard', '硬回退')
        }
        
        if mode_choice not in mode_map:
            print("❌ 无效选择")
            return
        
        mode, mode_name = mode_map[mode_choice]
        
        # 执行回退
        print(f"\n⏮️  正在执行{mode_name}...")
        result = self.run_command(f"git reset {mode} {commit_hash}")
        
        if result:
            print(f"\n✅ {mode_name}成功!")
            print(f"📍 已回退到: {commit_hash}\n")
            self.run_command("git status --short")
        else:
            print(f"\n❌ 回退失败")


def main():
    tool = GitSyncTool()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'push':
        tool.force_push()
    elif command == 'pull':
        tool.force_pull()
    elif command == 'sync':
        tool.smart_sync()
    elif command == 'status':
        tool.show_status()
    elif command == 'log':
        tool.show_log(5)
    elif command == 'history':
        tool.show_full_history()
    elif command == 'rollback':
        tool.rollback()
    elif command == 'config':
        tool.config_remote()
    else:
        print(f"❌ 未知命令: {command}")
        print(__doc__)


if __name__ == '__main__':
    main()