import random
import comfy.utils

class PD_random_prompt:
    """
    随机提示词生成节点
    能够输入一组提示词文本，按行区分不同输入，批量生成提示词组合
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
    CATEGORY = "Example"
    OUTPUT_IS_LIST = (True,)
    OUTPUT_NODE = True

    def run(self, max_count, mutable_prompt, immutable_prompt, random_sample, seed=0):
        """
        运行函数：生成随机提示词组合
        
        Args:
            max_count: 最大生成数量
            mutable_prompt: 可变提示词（按行分割）
            immutable_prompt: 固定提示词模板
            random_sample: 是否随机采样
            seed: 随机种子
            
        Returns:
            生成的提示词列表
        """
        # 设置随机种子
        if seed != 0:
            random.seed(seed)
        
        # 将可变提示词按行分割并去除空行
        words1 = [word.strip() for word in mutable_prompt.split("\n") if word.strip()]
        
        # 将固定提示词按行分割并去除空行
        words2 = [word.strip() for word in immutable_prompt.split("\n") if word.strip()]
        
        # 创建进度条
        pbar = comfy.utils.ProgressBar(len(words1) * len(words2))
        
        prompts = []
        
        # 组合可变提示词和固定提示词
        for w1 in words1:
            for w2 in words2:
                # 处理固定提示词中的占位符
                if '``' not in w2:
                    if w2 == "":
                        w2 = '``'
                    else:
                        w2 = w2 + ',``'
                
                # 生成组合提示词
                if w1 != '' and w2 != '':
                    prompts.append(w2.replace('``', w1))
                
                pbar.update(1)
        
        # 如果没有生成任何提示词，使用固定提示词
        if len(prompts) == 0:
            prompts.append(immutable_prompt)
        
        # 根据设置决定是否随机采样
        if random_sample == 'enable':
            # 随机从数组中取max_count个元素
            prompts = random.sample(prompts, min(max_count, len(prompts)))
        else:
            # 取前max_count个元素
            prompts = prompts[:min(max_count, len(prompts))]
        
        # 清理提示词（去除空字符串）
        prompts = [elem.strip() for elem in prompts if elem.strip()]
        
        return {"ui": {"prompts": prompts}, "result": (prompts,)}

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PD_random_prompt": PD_random_prompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PD_random_prompt": "PD: Random Prompt",
} 