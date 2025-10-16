# Git 使用教程 - Comfyui_PDuse 项目

## 📋 快速命令参考

### 🔄 日常更新项目流程（三步走）

```bash
# 1. 添加所有更改的文件
git add .

# 2. 提交更改（附带描述信息）
git commit -m "你的提交描述"

# 3. 推送到 GitHub
git push
```

---

## 📚 详细说明

### 1️⃣ 查看项目状态

```bash
git status
```

**作用：** 查看哪些文件被修改、新增或删除

**输出示例：**
- 红色文件 = 未添加到暂存区
- 绿色文件 = 已添加到暂存区，等待提交

---

### 2️⃣ 添加文件到暂存区

```bash
# 添加所有更改
git add .

# 或添加指定文件
git add 文件名.py
```

**作用：** 把你修改的文件标记为"准备提交"

---

### 3️⃣ 提交更改

```bash
git commit -m "描述你做了什么修改"
```

**提交信息建议：**
- ✅ 好的示例：
  - `git commit -m "添加新的图像裁切节点"`
  - `git commit -m "修复文件保存路径bug"`
  - `git commit -m "更新README文档"`
  
- ❌ 不好的示例：
  - `git commit -m "更新"`
  - `git commit -m "改了一些东西"`

---

### 4️⃣ 推送到 GitHub

```bash
git push
```

**作用：** 将本地的提交上传到 GitHub，让其他人可以看到你的更改

---

## 🆕 从 GitHub 拉取最新代码

如果你在其他地方修改了代码（或其他人提交了更新），需要先拉取最新代码：

```bash
git pull
```

---

## 🔧 常用场景

### 场景1：修改了代码后提交

```bash
# 查看修改了什么
git status

# 添加所有修改
git add .

# 提交
git commit -m "优化图像处理性能"

# 推送
git push
```

---

### 场景2：撤销未提交的修改

```bash
# 撤销单个文件的修改
git restore 文件名.py

# 撤销所有修改（谨慎使用！）
git restore .
```

---

### 场景3：查看提交历史

```bash
# 查看提交记录
git log

# 查看简洁的提交记录
git log --oneline

# 按 q 键退出
```

---

### 场景4：创建新分支（用于开发新功能）

```bash
# 创建并切换到新分支
git checkout -b 新功能分支名

# 开发完成后切回主分支
git checkout main

# 合并分支
git merge 新功能分支名
```

---

## ⚙️ 一次性配置（首次使用时）

如果是第一次使用 Git，需要配置用户信息：

```bash
# 设置用户名
git config --global user.name "你的名字"

# 设置邮箱
git config --global user.email "你的邮箱@example.com"
```

---

## 🚨 常见问题

### 问题1：推送失败 - 远程有新提交

```bash
# 先拉取远程更新
git pull

# 如果有冲突，手动解决冲突后
git add .
git commit -m "解决冲突"

# 再次推送
git push
```

---

### 问题2：忘记添加文件就提交了

```bash
# 添加遗漏的文件
git add 遗漏的文件.py

# 修补上一次提交（不创建新提交）
git commit --amend --no-edit
```

---

### 问题3：提交信息写错了

```bash
# 修改最后一次提交的信息
git commit --amend -m "正确的提交信息"
```

---

## 📝 工作流总结

```
修改代码
   ↓
git status (检查状态)
   ↓
git add . (添加文件)
   ↓
git commit -m "描述" (提交)
   ↓
git push (推送到GitHub)
   ↓
完成！✅
```

---

## 🎯 快捷命令（一行搞定）

```bash
# PowerShell 一行命令完成添加、提交、推送
git add . ; git commit -m "快速提交" ; git push
```

---

## 📌 项目信息

- **仓库地址：** https://github.com/7BEII/Comfyui_PDuse.git
- **本地路径：** E:\pandy_work\github\empty\Comfyui_PDuse
- **分支：** main

---

## 💡 小贴士

1. **频繁提交：** 不要等到做了很多修改才提交，建议每完成一个小功能就提交一次
2. **清晰描述：** 提交信息要清晰，方便以后查找
3. **先拉后推：** 推送前先 `git pull` 确保本地代码是最新的
4. **备份重要文件：** 在做重大修改前，可以先创建新分支

---

**✨ 祝编码愉快！**

