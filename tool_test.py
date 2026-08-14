#这是一个用于测试工具的脚本
import os
#接下来依旧是引入读取env的工具和sdk,并读取相关apikey 
from dotenv import load_dotenv
from openai import OpenAI
#接下来，引入我们编写的工具和json
import json
from tools import calculator

load_dotenv()
#接下来就是创建客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com"
)
#接下来这一步可以说是这个脚本的核心：告诉模型有什么工具，让模型根据这里的信息，自己决定要不要调用这个工具
tools = [
    {
        "type":"function",
        "function":{
            "name":"calculator",
            "description":"计算两个数字的加法",
            #对于这个工具的描述
            "parameters":{
                "type":"object",
                "properties":{
                    "a":{
                        "type":"number",
                        "description":"第一个数字",

                    },
                    "b":{
                        "type":"number",
                        "description":"第二个数字",
                                            
                    }
                    #以上是定义描述数据的类型
                },
                #最后，描述什么是必备的
                "required":["a" , "b"]
            }
        }
    }
]#这里和下边的tool_calls是对应的

#接下来，我们构造一个用于测试的对话消息，相关的详细原理可以看本系列第一期的第一版的main.py代码
messages = [
    {
        "role":"user",
        "content":"帮我计算123加上456"
    }
]

#接下来是最要紧的一点：把工具说明的部分连带这个测试消息一起发出来
response = client.chat.completions.create(
    model = "deepseek-chat",
    messages = messages,
    tools = tools
)

#最后，获取并打印模型返回消息
message = response.choices[0].message
print(message)
#这里打印的是：模型这一次返回了什么
tool_call = message.tool_calls[0]
#上一行表示取出模型提出的第一个工具调用
function_name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)

print("模型决定调用的工具：", function_name)
print("模型提供的参数：", arguments)
#接下来这个if判断就是对于工具的调用：如果大模型给出的结论是需要，那就用
if function_name == "calculator":
    result = calculator(
        arguments["a"],
        arguments["b"]
    )

    print("工具执行结果：", result)
#接下来是把这个对话加入历史
messages.append(message)
#把真正的工具执行结果交回模型
messages.append(
    {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": str(result)
    }
) 

# 第二次调用大模型
#这次模型已经能够看到工具执行结果
final_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )

#获取模型最终回答
final_message = final_response.choices[0].message

print("AI最终回答：", final_message.content)
#最后，在你的vscode终端运行：python tool_test.py，来查看这个脚本的效果

