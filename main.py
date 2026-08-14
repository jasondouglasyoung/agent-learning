#接下来看看怎么实现循环对话的效果
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from tools import calculator

#依旧是加载.env
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

#新增：定义模型可以使用的工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
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
        }
    }
]

#新增：现在，建立工具名等于函数的关系
tool_map = {
    "calculator":calculator
}

#这个是用列表的方式保存聊天记录|新增：保存整个对话历史
messages = [
    {
        "role": "system",
        "content": "你是一个可以使用工具解决问题的AI助手。"
    }
]
#接下来进入到agent最核心的一部分：agent的循环
def run_agent():

    while True:

        # 把目前所有对话历史和工具信息发送给模型
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )

        # 取得模型这一次返回的消息
        message = response.choices[0].message

        # 把模型返回的消息加入历史
        messages.append(message)

#现在我们分类讨论：先看看没有调用工具的情况
        if not message.tool_calls:
            return message.content
#再来看看用了的情况
        for tool_call in message.tool_calls:

            # 模型指定的工具名称
            function_name = tool_call.function.name

            # 模型生成的 JSON 参数
            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\n[Agent] 调用工具：{function_name}")
            print(f"[Agent] 工具参数：{arguments}")

            # 根据工具名找到真正的 Python 函数
            function = tool_map[function_name]

            # 真正执行 Python 函数
            result = function(**arguments)

            print(f"[Agent] 工具结果：{result}")

            # 把工具执行结果加入消息历史
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                }
            )
#接下来，是这个agent的主循环，和前天的一样
print("已进入对话，输入exit退出")
while True:
    user_input = input("\n你：")

    if user_input.lower() == "exit":
        print("对话结束")
        break

    messages.append({
        "role":"user",
        "content":user_input
    })

    # 交给上边那个定义的Agent函数处理，并取出回答
    ai_reply = run_agent()        

    print("\nai:",ai_reply)

     
         