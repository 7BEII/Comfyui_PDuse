import random
import comfy.utils

class PD_random_prompt:
    """
    随机提示词生成节点
    能够输入一组提示词文本，按行区分不同输入，批量生成提示词组合
    修复了空列表导致的 Out of Range 错误，并优化了空行处理逻辑
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "max_count": ("INT", {"default": 9, "min": 1, "max": 1000}),
                "mutable_prompt": ("STRING", 
                         {
                            "multiline": True, 
                            "default": "Swing\nSlide\nClimbing frame\nSandbox\nSee-saw\nMerry-go-round\nJungle gym\nTrampoline\nMonkey bars\nRocking horse\nPlayhouse\nHopscotch\nBalance beam\nSpring rider\nWater play area\nBall pit\nTunnel\nZip line\nBasketball hoop\nBicycle rack\nSpinner\nClimbing wall\nRope ladder\nTetherball\nFlying fox\nSwinging bridge\nSpiral slide\nWater sprinkler\nPedal go-kart\nMiniature golf course"
                          }),
                "immutable_prompt": ("STRING", 
                         {
                            "multiline": True, 
                            "default": 'sticker, Cartoon, ``'
                          }),
                "random_sample": (["enable", "disable"],),
            },
            "optional": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "PDuse/Text"
    OUTPUT_IS_LIST = (True,)
    OUTPUT_NODE = True

    def run(self, max_count, mutable_prompt, immutable_prompt, random_sample, seed=0):
        """
        运行函数：生成随机提示词组合
        """
        # 1. 设置随机种子
        if seed != 0:
            random.seed(seed)
        
        # 2. 处理可变提示词 
        # 使用 splitlines() 兼容不同系统的换行符，并过滤掉空行和纯空格行
        words1 = [line.strip() for line in mutable_prompt.splitlines() if line.strip()]
        
        # 3. 处理固定提示词
        words2 = [line.strip() for line in immutable_prompt.splitlines() if line.strip()]
        
        # 【关键修复1】如果不填固定提示词，默认为占位符
        # 否则 words2 为空会导致下面的双重循环不执行，从而导致输出为空
        if len(words2) == 0:
            words2 = ['``']

        # 创建进度条
        pbar = comfy.utils.ProgressBar(len(words1) * len(words2))
        
        prompts = []
        
        # 4. 组合提示词
        for w1 in words1:
            for w2 in words2:
                # 预处理固定提示词格式
                current_template = w2
                
                # 如果模板中没有反引号占位符，根据是否有内容决定拼接方式
                if '``' not in current_template:
                    if current_template == "":
                        current_template = '``'
                    else:
                        current_template = current_template + ', ``'
                
                # 替换占位符生成最终提示词
                if w1: # 确保 w1 有内容
                    final_prompt = current_template.replace('``', w1)
                    # 再次清理可能产生的多余逗号或空格
                    final_prompt = final_prompt.strip().strip(',')
                    prompts.append(final_prompt)
                
                pbar.update(1)
        
        # 【关键修复2】最后一道防线：防止列表为空导致的 Out of range
        # ComfyUI 的 OUTPUT_IS_LIST=True 必须返回至少包含一个元素的列表
        if len(prompts) == 0:
            prompts = [""] 

        # 5. 采样或截取逻辑
        if random_sample == 'enable':
            # 随机采样，数量不超过列表总长度
            prompts = random.sample(prompts, min(max_count, len(prompts)))
        else:
            # 顺序截取
            prompts = prompts[:min(max_count, len(prompts))]
        
        # 最终输出
        return {"ui": {"prompts": prompts}, "result": (prompts,)}

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_random_prompt": PD_random_prompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_random_prompt": "PD: Random Prompt",
}