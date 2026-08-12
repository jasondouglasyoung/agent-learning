#接下来看看怎么实现循环对话的效果
import os

from dotenv import load_dotenv
from openai import OpenAI

#依旧是加载.env
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

#这个是用列表的方式保存聊天记录
messages = []

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

    #这一步相当于把本次对话的所有聊天记录发给模型，相当于读取上下文
    response =  client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages
    )

    #设置一个变量，取出模型的回答
    ai_reply = response.choices[0].message.content

     
    print("\nai:",ai_reply)

    #把这次的问答内容放进列表
    messages.append({
        "role": "assistant",
        "content": ai_reply
    })
         