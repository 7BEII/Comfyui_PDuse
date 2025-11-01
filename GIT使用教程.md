# Git 使用教程 - Comfyui_PDuse 项目

## ⚡ 超快速参考（记住这个就够了）

```bash
# 💡 只更新1个文件
git add 文件路径/文件名.py
git commit -m "描述你改了什么"
git push

# 💡 更新所有文件
git add .
git commit -m "描述你改了什么"
git push
```

**就这么简单！三行命令搞定！**

---

## 🎯 两种提交方式对比

### 方式一：只更新单个文件 ✅

**使用场景：** 只修改了某一个文件，只想提交这个文件

```bash
# 第1步：添加指定文件（替换成你的文件名）
git add py/image_resize_v1.py

# 第2步：提交这个文件（写清楚改了什么）
git commit -m "优化图像缩放算法"

# 第3步：推送到GitHub
git push
```

---

### 方式二：更新整个项目 ✅

**使用场景：** 修改了多个文件，想一次性全部提交

```bash
# 第1步：添加所有修改的文件（用点表示全部）
git add .

# 第2步：提交所有文件（写清楚改了什么）
git commit -m "更新多个节点和配置文件"

# 第3步：推送到GitHub
git push
```

---

## 📝 提交信息（commit message）怎么写？

### 好的提交信息示例 ✅

```bash
# 添加新功能
git commit -m "添加图像旋转节点"

# 修复bug
git commit -m "修复文件保存路径错误"

# 优化性能
git commit -m "优化图像处理速度"

# 更新文档
git commit -m "更新README安装说明"

# 添加新字体
git commit -m "添加5种新的中文字体"

# 批量更新
git commit -m "更新多个图像处理节点和工作流文件"
```

### 不好的提交信息示例 ❌

```bash
git commit -m "更新"          # 太简单，看不出改了什么
git commit -m "修改"          # 没说修改了什么
git commit -m "aaa"           # 无意义
git commit -m "test"          # 测试？改了啥？
```

### 提交信息模板

```
类型: 具体做了什么

示例：
- 添加: 新增XX功能
- 修复: 解决XX问题  
- 优化: 提升XX性能
- 更新: 更新XX文件
- 删除: 移除XX代码
```

---

## 🎬 完整实战演示

### 场景A：修改了一个Python文件 `py/image_resize_v1.py`

```bash
# 第0步：先看看改了什么（可选）
git status

# 输出会显示：
# modified:   py/image_resize_v1.py  （红色，表示未添加）

# 第1步：添加这个文件
git add py/image_resize_v1.py

# 第2步：提交（写清楚改了什么）
git commit -m "优化图像缩放性能，修复边缘处理bug"

# 第3步：推送到GitHub
git push

# ✅ 完成！只有这一个文件被更新到GitHub
```

---

### 场景B：修改了多个文件，全部提交

```bash
# 第0步：先看看改了什么（可选）
git status

# 输出会显示多个文件：
# modified:   py/image_resize_v1.py
# modified:   py/mask.py
# modified:   README.md
# new file:   fonts/新字体.ttf

# 第1步：添加所有文件（用 . 表示全部）
git add .

# 第2步：提交所有更改
git commit -m "更新图像处理节点，添加新字体，更新文档"

# 第3步：推送到GitHub
git push

# ✅ 完成！所有文件都更新到GitHub
```

---

### 场景C：修改了3个文件，但只想提交其中2个

```bash
# 假设改了：
# - py/image_resize_v1.py  （想提交）
# - py/mask.py             （想提交）
# - config.py              （不想提交，还在测试中）

# 第1步：只添加想提交的文件
git add py/image_resize_v1.py
git add py/mask.py

# 或者一行写完：
git add py/image_resize_v1.py py/mask.py

# 第2步：提交
git commit -m "优化图像缩放和遮罩处理"

# 第3步：推送
git push

# ✅ 完成！只有选中的2个文件被提交，config.py保持未提交状态
```

---

## 📚 详细说明

### 1️⃣ 查看项目状态

```bash
git status
```

**作用：** 查看哪些文件被修改、新增或删除

**输出示例：**
- 红色文件 = 未添加到暂存区（还没执行 git add）
- 绿色文件 = 已添加到暂存区，等待提交（已执行 git add）

---

### 2️⃣ 添加文件到暂存区

```bash
# 添加所有更改
git add .

# 添加指定文件
git add py/文件名.py

# 添加多个指定文件
git add 文件1.py 文件2.py 文件3.py
```

---

### 3️⃣ 提交更改

```bash
git commit -m "描述你做了什么修改"
```

---

### 4️⃣ 推送到 GitHub

```bash
git push
```

---

## 🆕 从 GitHub 拉取最新代码

如果你在其他地方修改了代码（或其他人提交了更新），需要先拉取最新代码：

```bash
git pull
```

---

## 🔧 其他常用命令

### 撤销未提交的修改

```bash
# 撤销单个文件的修改（丢弃更改，恢复到上次提交的状态）
git restore 文件名.py

# 撤销所有修改（谨慎使用！）
git restore .
```

---

### 查看提交历史

```bash
# 查看详细提交记录
git log

# 查看简洁的提交记录（推荐）
git log --oneline

# 按 q 键退出查看
```

---

### 查看文件差异（看具体改了什么内容）

```bash
# 查看某个文件的修改内容
git diff 文件名.py

# 查看所有修改的内容
git diff
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

## 🚨 常见问题解决

### ❌ 推送失败：提示远程有新提交

```bash
git pull        # 先拉取最新代码
git push        # 再推送
```

---

### ❌ 忘记添加某个文件就提交了

```bash
git add 遗漏的文件.py              # 添加遗漏的文件
git commit --amend --no-edit      # 追加到上次提交（不改提交信息）
```

---

### ❌ 提交信息写错了（还没push）

```bash
git commit --amend -m "正确的提交信息"
```

---

### ❌ 不小心添加错了文件

```bash
git reset 文件名.py    # 从暂存区移除（保留修改）
```

---

## 📋 命令速查表

| 命令 | 作用 | 何时使用 |
|------|------|----------|
| `git status` | 查看文件状态 | 想知道改了哪些文件 |
| `git add .` | 添加所有文件 | 提交全部更改 |
| `git add 文件名` | 添加指定文件 | 只提交某个文件 |
| `git commit -m "说明"` | 提交更改 | 添加文件后，写说明 |
| `git push` | 推送到GitHub | 提交后，上传到远程 |
| `git pull` | 拉取最新代码 | 同步远程的更新 |
| `git log --oneline` | 查看提交历史 | 看之前提交记录 |
| `git diff` | 查看修改内容 | 看具体改了什么 |
| `git restore 文件` | 撤销修改 | 放弃某个文件的更改 |

---

## 🔄 标准工作流程

```
1. 修改代码
   ↓
2. git status          (看看改了什么)
   ↓
3. git add .           (添加文件)
   ↓
4. git commit -m "..." (提交并说明)
   ↓
5. git push            (推送到GitHub)
   ↓
✅ 完成！
```

---

## 📌 项目信息

- **仓库地址：** https://github.com/7BEII/Comfyui_PDuse.git
- **本地路径：** E:\pandy_work\github\empty\Comfyui_PDuse
- **分支：** main

---

## 💡 重要提示

### ✅ 好习惯

1. **提交前先看** → 执行 `git status` 确认要提交的文件
2. **提交信息要清楚** → 让别人（和未来的自己）知道你做了什么
3. **小步提交** → 完成一个功能就提交，不要攒一大堆
4. **推送前先拉** → 如果多人协作，先 `git pull` 再 `git push`

### ❌ 要避免

1. ❌ 不要提交 `__pycache__` 等缓存文件（已在 .gitignore 中）
2. ❌ 不要提交 API密钥、密码等敏感信息
3. ❌ 不要用无意义的提交信息（如"更新"、"修改"）
4. ❌ 不要在未测试的情况下就推送到主分支

---

## 🆘 需要帮助？

如果遇到问题，可以：
1. 查看 `git status` 了解当前状态
2. 使用 `git log --oneline` 查看提交历史
3. 参考本教程的"常见问题解决"部分

---

**✨ 祝开发顺利！有问题随时查阅本教程！**

