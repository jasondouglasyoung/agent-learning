#现在，我们把main.py重写一遍，只保留最基本的loop

from agent import run_agent, messages
#这里让main可以调用agent.py里的东西


#接下来，是这个agent的主循环，和前天的一样
print("已进入对话，输入exit退出")

while True:
    user_input = input("\n你：")

    if user_input.lower() == "exit":
        print("对话结束")
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    # 交给agent.py里的Agent函数处理，并取出回答
    ai_reply = run_agent()

    print("\nai:", ai_reply)