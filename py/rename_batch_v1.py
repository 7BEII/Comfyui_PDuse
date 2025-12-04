#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class BatchRenamer:
    """
    批量重命名工具类
    用于批量重命名文件，支持自定义前缀和输出路径
    """
    def __init__(self):
        """
        初始化GUI界面
        """
        self.window = tk.Tk()
        self.window.title("批量重命名工具")
        self.window.geometry("600x500")
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 源文件夹选择
        ttk.Label(self.main_frame, text="源文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_path = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.source_path, width=50).grid(row=0, column=1, pady=5)
        ttk.Button(self.main_frame, text="浏览", command=self.select_source_folder).grid(row=0, column=2, padx=5)
        
        # 输出文件夹选择
        ttk.Label(self.main_frame, text="输出文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_path = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, pady=5)
        ttk.Button(self.main_frame, text="浏览", command=self.select_output_folder).grid(row=1, column=2, padx=5)
        
        # 前缀输入
        ttk.Label(self.main_frame, text="前缀:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.prefix = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.prefix, width=50).grid(row=2, column=1, pady=5)
        
        # 新文件名输入
        ttk.Label(self.main_frame, text="新文件名:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.new_name = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.new_name, width=50).grid(row=3, column=1, pady=5)

        # math_0输入
        ttk.Label(self.main_frame, text="math_0:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.leading_zeros = tk.StringVar(value="2")  # 默认2个前导零
        ttk.Entry(self.main_frame, textvariable=self.leading_zeros, width=10).grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.main_frame, text="(默认2个0，如001)").grid(row=4, column=1, sticky=tk.E, pady=5)

        # 步长输入
        ttk.Label(self.main_frame, text="序号步长:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.step = tk.StringVar(value="1")  # 默认步长为1
        ttk.Entry(self.main_frame, textvariable=self.step, width=10).grid(row=5, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.main_frame, text="(默认1，如1,2,3)").grid(row=5, column=1, sticky=tk.E, pady=5)

        # 初始序号输入
        ttk.Label(self.main_frame, text="初始序号:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.start_number = tk.StringVar(value="1")  # 默认从1开始
        ttk.Entry(self.main_frame, textvariable=self.start_number, width=10).grid(row=6, column=1, sticky=tk.W, pady=5)
        ttk.Label(self.main_frame, text="(默认1开始)").grid(row=6, column=1, sticky=tk.E, pady=5)
        
        # 执行按钮
        ttk.Button(self.main_frame, text="开始重命名", command=self.rename_files).grid(row=7, column=1, pady=20)
        
        # 状态显示
        self.status_var = tk.StringVar()
        ttk.Label(self.main_frame, textvariable=self.status_var).grid(row=8, column=0, columnspan=3)

    def select_source_folder(self):
        """
        选择源文件夹
        """
        folder = filedialog.askdirectory()
        if folder:
            self.source_path.set(folder)

    def select_output_folder(self):
        """
        选择输出文件夹
        """
        folder = filedialog.askdirectory()
        if folder:
            self.output_path.set(folder)

    def validate_inputs(self):
        """
        验证输入参数
        """
        try:
            leading_zeros = int(self.leading_zeros.get())
            step = int(self.step.get())
            start_number = int(self.start_number.get())
            
            if leading_zeros < 0:
                raise ValueError("math_0不能为负数")
            if step < 1:
                raise ValueError("步长必须大于0")
            if start_number < 0:
                raise ValueError("初始序号不能为负数")
                
            return True
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return False

    def rename_files(self):
        """
        执行重命名操作
        """
        if not self.validate_inputs():
            return

        source_path = self.source_path.get()
        output_path = self.output_path.get()
        prefix = self.prefix.get()
        new_name = self.new_name.get()
        leading_zeros = int(self.leading_zeros.get())
        step = int(self.step.get())
        start_number = int(self.start_number.get())

        if not source_path:
            messagebox.showerror("错误", "请选择源文件夹！")
            return

        # 如果没有指定输出路径，创建默认输出文件夹
        if not output_path:
            current_date = datetime.now().strftime("%Y%m%d")
            base_output_path = os.path.join(os.path.dirname(source_path), f"rename_{current_date}")
            output_path = base_output_path
            count = 1
            # 检查文件夹是否存在，存在则递增后缀
            while os.path.exists(output_path):
                output_path = f"{base_output_path}_{count}"
                count += 1
            os.makedirs(output_path, exist_ok=True)

        try:
            # 获取所有文件并按名称排序
            files = sorted([f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))])
            
            current_number = start_number
            for file in files:
                # 获取文件扩展名
                file_ext = os.path.splitext(file)[1]
                
                # 构建新文件名
                if new_name:
                    # 计算总位数（前导零个数 + 数字本身的位数）
                    total_digits = leading_zeros + len(str(current_number))
                    new_filename = f"{new_name}_{current_number:0{total_digits}d}{file_ext}"
                else:
                    new_filename = file
                
                # 添加前缀（如果有）
                if prefix:
                    new_filename = f"{prefix}_{new_filename}"
                
                # 复制并重命名文件
                source_file = os.path.join(source_path, file)
                target_file = os.path.join(output_path, new_filename)
                shutil.copy2(source_file, target_file)
                
                # 更新序号
                current_number += step
            
            self.status_var.set("已经修改完成！如果不需要使用就删除！")
            
        except Exception as e:
            messagebox.showerror("错误", f"处理过程中出现错误：{str(e)}")

    def run(self):
        """
        运行GUI程序
        """
        self.window.mainloop()

if __name__ == "__main__":
    app = BatchRenamer()
    app.run()

    # ... existing code ... 