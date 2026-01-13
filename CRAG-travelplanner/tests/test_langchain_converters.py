"""
测试LangChain官方的消息转换方法
================================
验证 convert_to_messages 和 message_to_dict 是否可用
"""


def test_convert_to_messages():
    """测试 dict → BaseMessage 转换"""
    try:
        from langchain_core.messages.utils import convert_to_messages

        # 测试1: 单个dict消息
        dict_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        messages = convert_to_messages(dict_messages)

        print("\n✅ convert_to_messages 方法存在!")
        print(f"输入类型: {type(dict_messages)}")
        print(f"输出类型: {type(messages)}")
        print(f"输出长度: {len(messages)}")
        print(f"第1条消息类型: {type(messages[0])}")
        print(f"第1条消息类名: {messages[0].__class__.__name__}")
        print(f"第1条消息内容: {messages[0].content}")

        # 验证类型
        from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

        assert isinstance(messages[0], BaseMessage)
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)

        return True

    except ImportError as e:
        print(f"\n❌ convert_to_messages 方法不存在: {e}")
        return False


def test_message_to_dict():
    """测试 BaseMessage → dict 转换"""
    try:
        from langchain_core.messages import AIMessage, HumanMessage
        from langchain_core.messages.base import message_to_dict, messages_to_dict

        # 创建消息对象
        msg1 = HumanMessage(content="Hello")
        msg2 = AIMessage(content="Hi there!")

        # 测试单个消息转换
        dict_msg = message_to_dict(msg1)

        print("\n✅ message_to_dict 方法存在!")
        print(f"输入类型: {type(msg1)}")
        print(f"输出类型: {type(dict_msg)}")
        print(f"输出内容: {dict_msg}")

        # 测试多个消息转换
        dict_messages = messages_to_dict([msg1, msg2])

        print("\n✅ messages_to_dict 方法存在!")
        print(f"输出类型: {type(dict_messages)}")
        print(f"输出长度: {len(dict_messages)}")
        print(f"第1条消息: {dict_messages[0]}")

        return True

    except ImportError as e:
        print(f"\n❌ message_to_dict 方法不存在: {e}")
        return False


def test_message_dict_method():
    """测试 BaseMessage.dict() 方法 (Pydantic)"""
    try:
        from langchain_core.messages import HumanMessage

        msg = HumanMessage(content="Hello", name="User")

        # 测试 .dict() 方法 (Pydantic v1)
        try:
            dict_msg = msg.dict()
            print("\n✅ BaseMessage.dict() 方法存在! (Pydantic v1)")
            print(f"输出: {dict_msg}")
            return True
        except AttributeError:
            pass

        # 测试 .model_dump() 方法 (Pydantic v2)
        try:
            dict_msg = msg.model_dump()
            print("\n✅ BaseMessage.model_dump() 方法存在! (Pydantic v2)")
            print(f"输出: {dict_msg}")
            return True
        except AttributeError:
            pass

        print("\n❌ BaseMessage 没有 .dict() 或 .model_dump() 方法")
        return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_practical_usage():
    """测试实际使用场景"""
    print("\n" + "=" * 60)
    print("实际使用场景测试")
    print("=" * 60)

    try:
        from langchain_core.messages.base import messages_to_dict
        from langchain_core.messages.utils import convert_to_messages

        # 场景1: State中的dict消息 → LangChain对象
        state_messages = [
            {"role": "user", "content": "我想去杭州旅游"},
            {"role": "assistant", "content": "好的，请问您计划玩几天呢？"},
            {"role": "user", "content": "3天"},
        ]

        # 转换为LangChain对象
        langchain_messages = convert_to_messages(state_messages)

        print("\n📝 场景1: State dict → LangChain对象")
        print(f"输入: {state_messages[0]}")
        print(f"输出: {langchain_messages[0]}")
        print(f"输出类型: {type(langchain_messages[0]).__name__}")

        # 场景2: LangChain对象 → dict (回写State)
        dict_messages = messages_to_dict(langchain_messages)

        print("\n📝 场景2: LangChain对象 → State dict")
        print(f"输入: {langchain_messages[0]}")
        print(f"输出: {dict_messages[0]}")

        # 验证往返转换的一致性
        assert dict_messages[0]["data"]["content"] == state_messages[0]["content"]
        print("\n✅ 往返转换一致性验证通过!")

        return True

    except Exception as e:
        print(f"\n❌ 实际使用测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LangChain官方消息转换方法验证")
    print("=" * 60)

    results = {
        "convert_to_messages": test_convert_to_messages(),
        "message_to_dict": test_message_to_dict(),
        "dict() method": test_message_dict_method(),
        "practical_usage": test_practical_usage(),
    }

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25s} : {status}")

    # 返回总体结果
    all_passed = all(results.values())
    exit(0 if all_passed else 1)
