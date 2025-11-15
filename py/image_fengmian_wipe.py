import os
import math
import numpy as np
import torch
from PIL import Image
import folder_paths
import cv2


class PD_ImageFengMianWipe:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 上层图像（被擦除的那张）
                "top_image": ("IMAGE",),
                # 底层图像（被露出来的那张）
                "bottom_image": ("IMAGE",),
                # 过渡总帧数
                "num_frames": ("INT", {"default": 30, "min": 2, "max": 600, "step": 1}),
                # 线条角度（度），0 为水平从左到右
                "angle_deg": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0, "step": 1.0}),
                # 渐变带宽度（像素），0 表示硬边
                "smooth_width": ("INT", {"default": 20, "min": 0, "max": 4096, "step": 1}),
                # 边缘锐化程度（值越大边缘越明显）
                "edge_sharpness": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                # 边缘白线粗细（0表示没有白线，支持小数）
                "edge_line_width": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                # 边缘线颜色（十六进制，如#ffffff）
                "edge_line_color": ("STRING", {"default": "#ffffff"}),
                # 是否反向（反转时间方向）
                "reverse": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                # 可选：边缘线上的图标图像
                "liner_image": ("IMAGE",),
                # 可选：边缘线图标的遮罩
                "liner_image_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("frames",)
    FUNCTION = "generate_wipe_frames"
    CATEGORY = "PDuse/Image"

    def generate_wipe_frames(
        self,
        top_image,
        bottom_image,
        num_frames,
        angle_deg,
        smooth_width,
        edge_sharpness,
        edge_line_width,
        edge_line_color,
        reverse,
        liner_image=None,
        liner_image_mask=None,
    ):
        # 基本检查
        if not isinstance(top_image, torch.Tensor) or not isinstance(bottom_image, torch.Tensor):
            raise ValueError("top_image and bottom_image must be tensors")
        if top_image.dim() != 4 or bottom_image.dim() != 4:
            raise ValueError("top_image and bottom_image must have shape [B, H, W, C]")
        if top_image.shape != bottom_image.shape:
            raise ValueError("top_image and bottom_image must have the same shape")

        b, h, w, c = top_image.shape
        if b < 1:
            raise ValueError("batch size must be at least 1")

        # 只使用 batch 中的第 1 张图
        top = top_image[0].detach().cpu().numpy()  # [H, W, C], 0-1
        bottom = bottom_image[0].detach().cpu().numpy()
        
        # 解析十六进制颜色值
        def parse_hex_color(hex_color):
            """解析十六进制颜色值，返回RGB (0-1范围)"""
            # 移除 # 号
            hex_color = hex_color.strip()
            if hex_color.startswith('#'):
                hex_color = hex_color[1:]
            
            # 处理3位和6位十六进制
            if len(hex_color) == 3:
                # #fff -> #ffffff
                hex_color = ''.join([c*2 for c in hex_color])
            
            # 转换为RGB
            try:
                r = int(hex_color[0:2], 16) / 255.0
                g = int(hex_color[2:4], 16) / 255.0
                b = int(hex_color[4:6], 16) / 255.0
                return r, g, b
            except:
                # 如果解析失败，返回白色
                return 1.0, 1.0, 1.0
        
        # 解析边缘线颜色
        edge_color_r, edge_color_g, edge_color_b = parse_hex_color(edge_line_color)
        
        # 处理可选的liner_image和mask
        liner_img = None
        liner_mask = None
        if liner_image is not None:
            liner_img = liner_image[0].detach().cpu().numpy()  # [H, W, C], 0-1
        if liner_image_mask is not None:
            liner_mask = liner_image_mask[0].detach().cpu().numpy()  # [H, W], 0-1

        # 角度 -> 方向向量
        theta = angle_deg * math.pi / 180.0
        u = math.cos(theta)
        v = math.sin(theta)

        # 整幅图的 s 坐标网格
        xs = np.arange(w, dtype=np.float32)
        ys = np.arange(h, dtype=np.float32)
        X, Y = np.meshgrid(xs, ys)  # X, Y shape: [H, W]
        s_grid = X * u + Y * v

        # 通过四个角估计 s_min, s_max
        corners = np.array(
            [
                [0.0, 0.0],
                [float(w - 1), 0.0],
                [0.0, float(h - 1)],
                [float(w - 1), float(h - 1)],
            ],
            dtype=np.float32,
        )
        s_corners = corners[:, 0] * u + corners[:, 1] * v
        s_min = float(s_corners.min())
        s_max = float(s_corners.max())
        if abs(s_max - s_min) < 1e-6:
            s_max = s_min + 1e-6

        # 处理 smooth_width
        if smooth_width < 0:
            smooth_width = 0

        frame_list = []
        last_frame = None

        for f in range(num_frames):
            # 归一化时间 t
            if num_frames == 1:
                t = 0.0
            else:
                t = float(f) / float(num_frames - 1)
            if reverse:
                t = 1.0 - t

            # 当前帧的边界位置
            edge = s_min + t * (s_max - s_min)

            # 计算顶图权重 alpha_top
            if smooth_width == 0:
                # 硬边
                alpha_top = (s_grid >= edge).astype(np.float32)
            else:
                half = float(smooth_width) / 2.0
                d = s_grid - edge
                # 线性插值到 [0, 1]
                alpha_top = (d + half) / float(smooth_width)
                alpha_top = np.clip(alpha_top, 0.0, 1.0)
                
                # 应用边缘锐化：使用幂函数让边缘更明显
                # edge_sharpness = 1.0: 保持线性
                # edge_sharpness > 1.0: 边缘更锐利（S型曲线更陡峭）
                # edge_sharpness < 1.0: 边缘更柔和
                if edge_sharpness != 1.0:
                    # 使用 sigmoid 风格的锐化
                    # 将 [0,1] 映射到 [-1,1]，应用幂函数，再映射回 [0,1]
                    alpha_centered = alpha_top * 2.0 - 1.0  # [0,1] -> [-1,1]
                    # 保持符号，对绝对值应用幂函数
                    alpha_sharpened = np.sign(alpha_centered) * np.power(np.abs(alpha_centered), 1.0 / edge_sharpness)
                    alpha_top = (alpha_sharpened + 1.0) / 2.0  # [-1,1] -> [0,1]
                    alpha_top = np.clip(alpha_top, 0.0, 1.0)

            # [H, W] -> [H, W, 1]
            alpha_top_3 = alpha_top[..., None]
            # 线性混合：顶图权重 alpha_top，底图权重 1-alpha_top
            frame = alpha_top_3 * top + (1.0 - alpha_top_3) * bottom

            # 添加边缘白线
            if edge_line_width > 0 and smooth_width > 0:
                # 计算距离边缘中心的距离（alpha = 0.5 的位置）
                # alpha_top = 0.5 表示正好在过渡中心
                distance_from_edge = np.abs(alpha_top - 0.5)
                
                # 白线的半宽度（像素）
                half_line_width = float(edge_line_width) / 2.0
                
                # 创建白线遮罩：距离边缘中心小于半宽度的像素
                # 需要将距离从 [0, 0.5] 范围映射到像素距离
                # alpha 变化范围是 smooth_width 像素对应 0到1
                # 所以 alpha 变化 0.5 对应 smooth_width/2 像素
                pixel_distance = distance_from_edge * float(smooth_width)
                
                # 白线遮罩：在白线范围内的像素
                line_mask = (pixel_distance <= half_line_width).astype(np.float32)
                
                # 可选：让白线边缘有轻微羽化（1像素过渡）
                feather_range = 1.0
                if edge_line_width >= 2:
                    # 在 (half_line_width, half_line_width + feather_range) 范围内羽化
                    feather_zone = np.logical_and(
                        pixel_distance > half_line_width,
                        pixel_distance <= half_line_width + feather_range
                    )
                    feather_alpha = 1.0 - (pixel_distance - half_line_width) / feather_range
                    line_mask = np.where(feather_zone, feather_alpha, line_mask)
                
                # [H, W] -> [H, W, 1]
                line_mask_3 = line_mask[..., None]
                
                # 创建用户指定颜色的线 [H, W, C]
                line_color = np.ones_like(frame)
                line_color[:, :, 0] = edge_color_r
                line_color[:, :, 1] = edge_color_g
                line_color[:, :, 2] = edge_color_b
                
                # 将彩色线混合到帧中：line_mask 控制颜色的强度
                frame = frame * (1.0 - line_mask_3) + line_color * line_mask_3
                
                # 如果提供了liner_image，叠加到白线上
                if liner_img is not None and liner_mask is not None:
                    # 获取liner_image的尺寸
                    liner_h, liner_w = liner_img.shape[:2]
                    
                    # 计算边缘中心线的位置
                    # 对于每个像素，找到距离边缘中心最近的位置
                    # 边缘中心是 s_grid == edge 的位置
                    
                    # 创建一个遮罩，标记边缘中心附近的区域
                    center_mask = (np.abs(alpha_top - 0.5) < 0.01).astype(np.float32)
                    
                    # 找到边缘中心线的像素位置
                    center_pixels = np.where(center_mask > 0)
                    
                    if len(center_pixels[0]) > 0:
                        # 计算边缘中心线的中心点
                        # 使用所有中心线像素的质心
                        center_y = int(np.mean(center_pixels[0]))
                        center_x = int(np.mean(center_pixels[1]))
                        
                        # 计算liner_image的放置位置（居中对齐）
                        start_y = center_y - liner_h // 2
                        start_x = center_x - liner_w // 2
                        end_y = start_y + liner_h
                        end_x = start_x + liner_w
                        
                        # 确保不超出边界
                        # 计算实际可以放置的区域
                        src_start_y = max(0, -start_y)
                        src_start_x = max(0, -start_x)
                        src_end_y = min(liner_h, h - start_y)
                        src_end_x = min(liner_w, w - start_x)
                        
                        dst_start_y = max(0, start_y)
                        dst_start_x = max(0, start_x)
                        dst_end_y = min(h, end_y)
                        dst_end_x = min(w, end_x)
                        
                        # 检查是否有有效区域
                        if (dst_end_y > dst_start_y and dst_end_x > dst_start_x and
                            src_end_y > src_start_y and src_end_x > src_start_x):
                            
                            # 提取liner_image和mask的有效区域
                            liner_patch = liner_img[src_start_y:src_end_y, src_start_x:src_end_x]
                            mask_patch = liner_mask[src_start_y:src_end_y, src_start_x:src_end_x]
                            
                            # 扩展mask维度以匹配颜色通道
                            mask_patch_3 = mask_patch[..., None]
                            
                            # 提取目标区域
                            target_patch = frame[dst_start_y:dst_end_y, dst_start_x:dst_end_x]
                            
                            # Alpha混合：liner_image叠加到frame上
                            blended_patch = target_patch * (1.0 - mask_patch_3) + liner_patch * mask_patch_3
                            
                            # 放回frame
                            frame[dst_start_y:dst_end_y, dst_start_x:dst_end_x] = blended_patch

            # 添加当前帧到列表
            last_frame = frame
            frame_list.append(frame.astype(np.float32))

        # 兜底：如果循环中没有写入 last_frame，就用顶图
        if last_frame is None:
            last_frame = top

        if len(frame_list) == 0:
            frame_list.append(last_frame.astype(np.float32))

        frames_np = np.stack(frame_list, axis=0).astype(np.float32)  # [B, H, W, C]

        # 转回 torch 张量并加 batch 维
        frames_tensor = torch.from_numpy(frames_np)

        return (frames_tensor,)


class PD_ImageListToGif:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "frame_rate": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 60.0, "step": 1.0}),
                "loop_count": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
                "filename_prefix": ("STRING", {"default": "FengMian"}),
                "output_folder": ("STRING", {"default": "imagefengmian_gif"}),
                "format": (["gif", "webp", "mp4"], {"default": "gif"}),
                "pingpong": ("BOOLEAN", {"default": False}),
                "save_output": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepath",)
    FUNCTION = "image_list_to_gif"
    CATEGORY = "PDuse/Image"
    OUTPUT_NODE = True

    def image_list_to_gif(
        self,
        images,
        frame_rate,
        loop_count,
        filename_prefix,
        output_folder,
        format,
        pingpong,
        save_output,
    ):
        if not isinstance(images, torch.Tensor):
            raise ValueError("images must be a tensor")
        if images.dim() != 4:
            raise ValueError("images must have shape [B, H, W, C]")

        frames_np = images.detach().cpu().numpy()
        if frames_np.shape[0] == 0:
            raise ValueError("images tensor has no frames")

        frame_list = []
        for i in range(frames_np.shape[0]):
            arr = np.clip(frames_np[i] * 255.0, 0.0, 255.0).astype(np.uint8)
            frame_list.append(Image.fromarray(arr))

        if pingpong and len(frame_list) > 1:
            pingpong_frames = frame_list + frame_list[-2:0:-1]
        else:
            pingpong_frames = frame_list

        if not save_output:
            return {"ui": {}, "result": ("",)}

        output_root = folder_paths.get_output_directory()
        save_dir = os.path.join(output_root, output_folder)
        os.makedirs(save_dir, exist_ok=True)

        # 确定文件扩展名
        if format == "gif":
            ext = "gif"
        elif format == "webp":
            ext = "webp"
        else:  # mp4
            ext = "mp4"

        index = 1
        while True:
            filename = f"{filename_prefix}_{index:04d}.{ext}"
            file_path = os.path.join(save_dir, filename)
            if not os.path.exists(file_path):
                break
            index += 1

        if frame_rate <= 0:
            frame_rate = 8.0

        # 处理MP4格式
        if format == "mp4":
            # 应用pingpong效果
            if pingpong and len(frame_list) > 1:
                video_frames = frame_list + frame_list[-2:0:-1]
            else:
                video_frames = frame_list
            
            # 获取第一帧的尺寸
            first_np = np.array(video_frames[0])
            h, w = first_np.shape[:2]
            
            # 尝试使用H.264编码器（更兼容）
            # 优先尝试 avc1（H.264），如果失败则使用 mp4v
            fourcc_options = [
                cv2.VideoWriter_fourcc(*'avc1'),  # H.264 (最兼容)
                cv2.VideoWriter_fourcc(*'mp4v'),  # MPEG-4
            ]
            
            video_writer = None
            for fourcc in fourcc_options:
                video_writer = cv2.VideoWriter(file_path, fourcc, frame_rate, (w, h))
                if video_writer.isOpened():
                    print(f"Using fourcc: {fourcc}")
                    break
                video_writer.release()
                video_writer = None
            
            if video_writer is None or not video_writer.isOpened():
                raise RuntimeError("Failed to create video writer with any codec")
            
            # 写入所有帧
            for pil_frame in video_frames:
                # PIL RGB -> OpenCV BGR
                frame_bgr = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
                video_writer.write(frame_bgr)
            
            video_writer.release()
            
            # 验证文件是否成功创建
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise RuntimeError(f"Failed to create MP4 file: {file_path}")
        else:
            # GIF/WebP格式
            duration = int(1000.0 / frame_rate)
            first_frame = pingpong_frames[0]
            append_frames = pingpong_frames[1:] if len(pingpong_frames) > 1 else []

            if format == "gif":
                first_frame.save(
                    file_path,
                    save_all=True,
                    append_images=append_frames,
                    duration=duration,
                    loop=loop_count,
                )
            else:  # webp
                first_frame.save(
                    file_path,
                    save_all=True,
                    append_images=append_frames,
                    duration=duration,
                    loop=loop_count,
                    format="WEBP",
                )

        # 构建相对路径（相对于output目录）
        relative_path = os.path.join(output_folder, filename).replace("\\", "/")
        
        # 返回UI预览信息，模仿VideoHelperSuite的格式
        # MP4使用video/mp4，GIF/WebP使用image/格式
        if format == "mp4":
            format_type = "video/mp4"
        else:
            format_type = f"image/{format}"
            
        preview = {
            "filename": filename,
            "subfolder": output_folder,
            "type": "output",
            "format": format_type,
        }
        
        return {"ui": {"gifs": [preview]}, "result": (file_path,)}


NODE_CLASS_MAPPINGS = {
    "PD_ImageFengMianWipe": PD_ImageFengMianWipe,
    "PD_ImageListToGif": PD_ImageListToGif,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_ImageFengMianWipe": "PD:Image FengMian Wipe",
    "PD_ImageListToGif": "PD:Image List To Gif/Video",
}
