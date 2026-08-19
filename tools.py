#我们先简单写一个加减法的工具，不用很复杂
def calculator(a : float , b : float) -> float:
    return a+b

#今天，我们再加一些新的工具
#比如，获取时间的
def get_current_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#比如，读取文件的
def read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        #意思是：只读，按utf-8解码，打开文件暂时交给变量file
        return file.read()


#现在，我们再加入一个可以写入文本文件的工具
#这个工具只有在Agent真正调用它的时候才会修改文件
#这里使用w模式，如果文件不存在就创建，如果文件已经存在就覆盖原来的内容
def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    #工具执行完成以后返回一个简单的结果，让Agent知道写入已经成功
    return f"文件 {filename} 写入成功"


#接下来，我们让注册统一化

tool_registry = [
    {
        "name": "calculator",
        "function": calculator,
        "description": "计算两个数字的加法",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "第一个数字"
                },
                "b": {
                    "type": "number",
                    "description": "第二个数字"
                }
            },
            "required": ["a", "b"]
        }
    },

    {
        "name": "get_current_time",
        "function": get_current_time,
        "description": "获取当前电脑的本地日期和时间",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    {
        "name": "read_file",
        "function": read_file,
        "description": "读取本地文本文件的内容",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "需要读取的文件名或文件路径"
                }
            },
            "required": ["filename"]
        }
    },

    #现在把刚刚新增的write_file也加入统一注册表
    #只需要在这里注册一次，下面的tools和tool_map都会自动生成
    {
        "name": "write_file",
        "function": write_file,
        "description": "把指定文本内容写入本地文本文件。只有在用户明确要求创建或修改文件时才应该调用这个工具",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "需要写入的文件名或文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "需要写入文件的文本内容"
                }
            },
            "required": ["filename", "content"]
        }
    }
]


#现在，使用统一推导式规范化
tools = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }
    }
    for tool in tool_registry
]


# 根据统一注册表，自动生成工具名和 Python 函数之间的映射
tool_map = {
    tool["name"]: tool["function"]
    for tool in tool_registry
}