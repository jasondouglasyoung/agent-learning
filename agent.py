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


#随着Agent的功能越来越多，输出的运行信息也会越来越多
#所以这里把Agent的日志输出统一封装起来
#以后如果想关闭日志、增加时间或者把日志写入文件，只需要修改这里
def log(message):
    print(f"[Agent] {message}")


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


#随着对话越来越长，messages里的历史消息也会越来越多
#如果一直保留所有历史，每次请求模型时都会发送越来越多的内容
#所以这里加入一个最简单的短期记忆管理，只保留最近几轮用户对话
def trim_messages(max_user_turns=6):

    #这里先找出所有用户消息在messages里的位置
    user_indexes = []

    for index, message in enumerate(messages):

        #messages里既可能有普通字典，也可能有模型返回的消息对象
        #所以这里分别获取它们的role
        if isinstance(message, dict):
            role = message.get("role")
        else:
            role = getattr(message, "role", None)

        if role == "user":
            user_indexes.append(index)

    #如果当前用户对话轮数还没有超过限制，就不需要删除
    if len(user_indexes) <= max_user_turns:
        return

    #找到需要保留的最早一条用户消息
    start_index = user_indexes[-max_user_turns]

    #system提示词必须一直保留
    system_message = messages[0]

    #从最近几轮对话的第一条user消息开始保留
    recent_messages = messages[start_index:]

    #原地修改messages，避免main.py里引用的messages变成另一个列表
    messages[:] = [system_message] + recent_messages

    log(f"已整理短期记忆，目前保留最近 {max_user_turns} 轮用户对话")


# Agent Loop

def run_agent():

    #agent loop的对话次数不应该是没有限制的
    # 比如这里，Agent 最多允许执行 10 轮
    max_steps = 10

    #每次开始处理新的用户任务之前，先整理一次对话历史
    #这样不会在一次正在执行的工具调用过程中突然删除消息
    trim_messages()

    for step in range(max_steps):
        #再加一个标志显示循环次数
        log(f"Step {step + 1}")

        # 把对话历史和工具信息发送给模型
        #接下来再加一层异常处理，因为模型请求本身也可能失败
        #比如断网、API Key错误、请求超时或者模型服务异常
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools
            )

        #如果模型请求失败，就不要让整个程序直接报错退出
        #而是把错误信息返回给main.py，让用户可以看到发生了什么
        except Exception as e:
            return f"模型请求失败：{e}"

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

            # 现在加上有变化的一点：尝试解析模型生成的 JSON 参数
            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

            #接下来的部分是新增的，用于解决解析失败的问题
            except json.JSONDecodeError as e:
                result = f"工具参数解析失败：{e}"

                log(f"调用工具：{function_name}")
                log(f"工具结果：{result}")

                # 把错误结果也返回给模型
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    }
                )

                # 跳过这一次工具执行，继续处理后面的流程
                continue

            #现在Agent运行过程中需要显示的信息都通过log函数输出
            log(f"调用工具：{function_name}")
            log(f"工具参数：{arguments}")

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

            log(f"工具结果：{result}")

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