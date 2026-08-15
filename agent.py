#接下来，我们要把main.py这个文件分拆一下，把其中一部分拆到这个agent.py里边

import os
import json

from dotenv import load_dotenv
from openai import OpenAI

 #接下来这个也是分拆的一部分，引入
from tools import tools, tool_map
#这样就不再需要之前的import了
# 加载.env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


 


# 保存整个对话历史
messages = [
    {
        "role": "system",
        #现在，让我们优化一下系统提示词，给这个模型和agent一些限制，以防止其做出一些类似于未经同意删改文件的事情
        "content":  """
你是一个可以使用工具解决问题的 AI 助手。

请遵守以下规则：

1. 当用户的问题需要工具才能获得可靠结果时，应调用合适的工具。
2. 不需要工具就能回答的问题，可以直接回答，不要为了调用工具而调用工具。
3. 不要编造工具执行结果。
4. 如果工具执行失败，应根据工具返回的错误信息向用户说明情况，或者尝试其他可行的方法。
5. 如果一个任务需要多个工具，可以连续调用多个工具，直到任务完成。
"""
    }
]


# Agent Loop

def run_agent():

    #agent loop的对话次数不应该是没有限制的
    # 比如这里，Agent 最多允许执行 10 轮
    max_steps = 10

    for step in range(max_steps):
        #再加一个标志显示循环次数
        print(f"\n[Agent] Step {step + 1}")
        # 把对话历史和工具信息发送给模型
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )

        # 取得模型返回的消息
        message = response.choices[0].message

        # 加入历史记录
        messages.append(message)

        # 如果模型没有调用工具，说明已经得到最终回答
        if not message.tool_calls:
            return message.content

        # 如果模型调用了工具
        for tool_call in message.tool_calls:

            # 模型指定的工具名称
            function_name = tool_call.function.name

            # 模型生成的 JSON 参数
            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\n[Agent] 调用工具：{function_name}")
            print(f"[Agent] 工具参数：{arguments}")

            # 检查工具是否存在
            if function_name not in tool_map:
                result = f"错误：不存在名为 {function_name} 的工具"

            else:
                # 找到真正的 Python 函数
                function = tool_map[function_name]

                # 尝试执行工具
                try:
                    result = function(**arguments)

                except Exception as e:
                    result = f"工具执行失败：{e}"

            print(f"[Agent] 工具结果：{result}")

            # 把工具结果加入消息历史
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                }
            )

    # 如果循环了 max_steps 次还没有产生最终回答，就强制停止
    return f"Agent 已达到最大执行轮数 {max_steps}，本次任务已停止。"