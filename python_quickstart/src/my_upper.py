"""
最简单的 Python 外部函数示例
输入一个字符串，返回转为大写的版本
零依赖，纯 Python 标准库
"""
import json

# 装饰器：ClickZetta 框架必需，注册函数签名
def annotate(signature):
    def decorator(cls):
        cls._signature = signature
        return cls
    return decorator

# 兼容 ClickZetta 运行时的导入
try:
    from cz.udf import annotate
except ImportError:
    pass


@annotate("*->string")
class my_upper(object):
    def evaluate(self, s):
        return s.upper() if s else s
