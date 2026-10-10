import os
from getpass import getpass

from langchain.agents import create_agent
from langchain.tools import tool

from core import chord_info, fretboard_positions, identify_chords

@tool
def get_chord_info(symbol: str) -> dict:
    """计算和弦构成音及半音间隔。接受 C、Am、G7、Bbmaj7 等；不接受斜杠输入或九和弦。"""
    try:
        return chord_info(symbol)
    except ValueError as error:
        return {"error": str(error)}

@tool
def locate_chord_notes(symbol: str, max_fret: int=5) -> dict:
    """返回标准调弦吉他上和弦音的所有位置。位置不是自动生成的可弹按法；最大品位范围为 0 到 24。"""
    try:
        return {"positions": fretboard_positions(symbol, max_fret)}
    except ValueError as error:
        return {"error": str(error)}

@tool
def recognize_shape(frets: list[int]) -> dict:
    """识别一组吉他按法。必须传入 6 个整数，按 6 弦到 1 弦排序；-1 表示不弹，0 表示空弦，1 到 24 表示品位。只查完整匹配，可能返回多个名称。"""
    if len(frets) != 6 or any(type(f) is not int or not -1 <= f <= 24 for f in frets):
        return {"error": "请提供 6 个 -1 到 24 的整数，顺序为 6 弦到 1 弦。"}
    positions = [(string, fret) for string, fret in zip(range(6, 0, -1), frets) if fret >= 0]
    return {"candidates": identify_chords(positions)}


if __name__ == "__main__":
    # 先测试工具本身；这一步不调用模型。
    print("工具检查：", get_chord_info.invoke({"symbol": "C"}))
    print("工具检查：", locate_chord_notes.invoke({"symbol": "C", "max_fret": 5}))
    print("工具检查：", recognize_shape.invoke({"frets": [0, 1, 0, 2, 3, 0]}))
    model_id = os.environ.get("LANGCHAIN_MODEL")
    if not model_id:
        raise SystemExit("请先设置 LANGCHAIN_MODEL，格式如 openai:你有权限调用的模型名。")
    if model_id.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = getpass("输入 API key（输入内容不会显示）：")
    agent = create_agent(
        model=model_id,
        tools=[get_chord_info, locate_chord_notes, recognize_shape],
        system_prompt=(
            "你是中文吉他学习助手。查询和弦构成音、指板位置或识别按法时先调用对应工具。"
            "明确区分所有音符位置和可弹按法；保留工具返回的多个候选。"
            "工具未匹配不代表这些音不是和弦；说明当前模板库的限制。"
            "工具不支持的计算应说明限制，不编造工具结果。解释保持简明。"
        ),
    )
    question = input("输入你的问题：")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"recursion_limit": 12},
    )
    print(result["messages"][-1].content)
