class PDStringInput:
    """
    @classdesc
    文本输入节点，支持多行字符串输入。
    """
    @classmethod
    def INPUT_TYPES(cls):
        """
        @returns {dict} 节点输入参数类型
        """
        return {
            "required": {
                "value": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "execute"
    CATEGORY = "PD/Logic"

    def execute(self, value):
        """
        * 文本输入节点主函数
        * @param {str} value - 输入的字符串
        * @return {tuple} 输出字符串
        """
        return (value,)

class PDStringConcate:
    """
    @classdesc
    字符串连接节点，将两个字符串用指定分隔符连接。
    """
    @classmethod
    def INPUT_TYPES(cls):
        """
        @returns {dict} 节点输入参数类型
        """
        return {
            "required": {
                "string1": ("STRING", {"default": '', "forceInput": True}),
                "string2": ("STRING", {"default": '', "forceInput": True}),
                "delimiter": ("STRING", {"default": ',', "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("joined_string",)
    FUNCTION = "joinstring"
    CATEGORY = "PD/Logic"

    def joinstring(self, string1, string2, delimiter):
        """
        * 字符串连接主函数
        * @param {str} string1 - 第一个字符串
        * @param {str} string2 - 第二个字符串
        * @param {str} delimiter - 分隔符
        * @return {tuple} 连接后的字符串
        """
        joined_string = string1 + delimiter + string2
        return (joined_string, )

# 节点注册
NODE_CLASS_MAPPINGS = {
    "PDStringInput": PDStringInput,
    "PDStringConcate": PDStringConcate,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PDStringInput": "PD:String",
    "PDStringConcate": "PD:stringconcate",
}