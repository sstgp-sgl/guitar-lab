import plotly.graph_objects as go
import streamlit as st

from track import render_track

from core import (
    KNOWN_SHAPES, PITCH_NAMES, TUNING_MIDI,
    chord_info, fretboard_positions, identify_chords, note_at, toggle_position, note_to_pc,
)


def draw_board(max_fret: int, highlights: dict, root_pc=None, shape_positions=None):
    shape_positions = shape_positions or set()
    fig = go.Figure()
    for string in range(1, 7):
        fig.add_shape(type="line", x0=-0.3, x1=max_fret + 0.5,
                      y0=string, y1=string, line=dict(color="#8a8a8a", width=2))
    for fret in range(max_fret + 1):
        fig.add_shape(type="line", x0=fret + 0.5, x1=fret + 0.5,
                      y0=0.6, y1=6.4,
                      line=dict(color="#777", width=4 if fret == 0 else 1))

    xs, ys, labels, colors, hover, borders = [], [], [], [], [], []
    for string in range(1, 7):
        for fret in range(max_fret + 1):
            midi = note_at(string, fret)
            selected = (string, fret) in highlights
            borders.append(3 if (string, fret) in shape_positions else 0)
            xs.append(fret)
            ys.append(string)
            labels.append(highlights.get((string, fret), ""))
            is_root = root_pc is not None and midi % 12 == root_pc
            colors.append(("#e45756" if is_root else "#f2b134") if selected else "#dce2e8")
            hover.append(f"{string} 弦 · {fret} 品 · {PITCH_NAMES[midi % 12]}{midi // 12 - 1}")
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=labels,
        marker=dict(size=27, color=colors, line=dict(color="#263849", width=borders)),
        textfont=dict(color="#171717", size=11),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>",
    ))
    fig.update_layout(
        height=360, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="#fff9ed", showlegend=False,
        xaxis=dict(title="品位（0 = 空弦）", tickmode="array",
                   tickvals=list(range(max_fret + 1)),
                   range=[-0.5, max_fret + 0.6], showgrid=False, zeroline=False),
        yaxis=dict(tickmode="array", tickvals=list(range(1, 7)),
                   ticktext=[f"{s} 弦" for s in range(1, 7)],
                   range=[6.6, 0.4], showgrid=False, zeroline=False),
    )
    return fig


st.set_page_config(page_title="Guitar Lab", layout="wide")
st.markdown("""<style>
.st-key-show_chord_track {width:fit-content; border:1px solid #28b7a0;
    border-radius:18px; padding:5px 10px; background:rgba(40,183,160,.16);}
.st-key-show_chord_track p {font-size:13px !important; font-weight:700;}
.st-key-show_chord_track label {min-height:24px;}
</style>""", unsafe_allow_html=True)
st.sidebar.toggle("♫ 和弦轨道", key="show_chord_track")
st.title("Guitar Lab · 和弦与指板")
st.write("从和弦认识指板，也从指板理解和弦。")
st.caption("标准调弦 E A D G B E；图的上方是 1 弦，下方是 6 弦。")
mode = st.radio("选择功能", ["和弦音位置", "常用按法", "反向识别"], horizontal=True)
max_fret = st.slider("显示到第几品", 5, 15, 12)
highlights = {}
shape_positions = set()
root_pc = None

if mode == "反向识别":
    st.write("点击指板选择音符；同弦换位会替换，再次点击取消。0 为空弦，未选中的弦不弹。")
    if "selected_positions" not in st.session_state:
        st.session_state.selected_positions = {}

    def click_position(string, fret):
        st.session_state.selected_positions = toggle_position(
            st.session_state.selected_positions, string, fret)

    def load_shape(symbol=None):
        st.session_state.selected_positions = (
            {s: f for s, f in zip(TUNING_MIDI, KNOWN_SHAPES[symbol]) if f is not None}
            if symbol else {})

    controls = st.columns(3)
    controls[0].button("清空指板", on_click=load_shape)
    controls[1].button("示例 C", on_click=load_shape, args=("C",))
    controls[2].button("示例 Am", on_click=load_shape, args=("Am",))
    settings = st.columns(2)
    root_choice = settings[0].selectbox(
        "根音", ["自动判断", "C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"],
        key="analysis_root")
    allow_omissions = settings[1].checkbox("允许省略音", key="allow_omissions")
    st.caption("根音可以不在选音中；最低音由实际按法决定。允许省略音时，仅考虑省略根音或纯五音，保留三音、七音及扩展音。")
    selected = st.session_state.selected_positions
    hidden = [f"{s} 弦 {f} 品" for s, f in selected.items() if f > max_fret]
    if hidden:
        st.warning("显示范围外仍有选音：" + "、".join(hidden) + "。扩大品位范围可编辑，或清空指板。")

    # Native buttons support mouse, touch, keyboard and Streamlit session state.
    with st.container(border=True):
        header = st.columns([1.4] + [1] * (max_fret + 1))
        header[0].caption("弦 / 品")
        for fret, col in enumerate(header[1:]):
            col.caption("0 空弦" if fret == 0 else str(fret))
        for string in range(1, 7):
            row = st.columns([1.4] + [1] * (max_fret + 1))
            row[0].write(f"{string} 弦 · {PITCH_NAMES[note_at(string, 0) % 12]}")
            for fret, col in enumerate(row[1:]):
                name = PITCH_NAMES[note_at(string, fret) % 12]
                col.button(name, key=f"fret_{string}_{fret}",
                           type="primary" if selected.get(string) == fret else "secondary",
                           width="stretch", on_click=click_position, args=(string, fret))
    st.caption("高亮按钮 = 已选音；每行代表一根弦，每列代表一个品位。")
    positions = sorted(selected.items(), reverse=True)
    st.write("6 弦 → 1 弦：" + " · ".join(str(selected.get(s, "X")) for s in TUNING_MIDI))
    chosen_root = None if root_choice == "自动判断" else root_choice
    candidates = identify_chords(positions, root=chosen_root, allow_omissions=allow_omissions)
    if not positions:
        st.info("点击指板开始，或载入示例。")
    else:
        played = sorted({note_at(s, f) % 12 for s, f in positions})
        st.write("所选音（合并八度重复）：" + "、".join(PITCH_NAMES[pc] for pc in played))
        st.caption("计算各音相对候选根音的半音差（对 12 取余），与和弦公式比较。九、十一、十三音按和弦功能标注，不要求实际弹在高八度。")
        if candidates:
            exact = [c for c in candidates if c["match_type"] == "exact"]
            partial = [c for c in candidates if c["match_type"] == "omitted"]
            for label, group in [("完整匹配", exact), ("含省略音的可能解释", partial)]:
                if group:
                    st.write(f"**{label}**：" + "、".join(c["display_name"] for c in group))
            candidate_names = [c["display_name"] for c in candidates]
            chosen_name = st.selectbox("查看候选的音程分析", candidate_names)
            item = candidates[candidate_names.index(chosen_name)]
            with st.container(border=True):
                st.subheader(item["display_name"])
                st.write(" → ".join(
                    f"{tone['note']}（{tone['interval']}）" for tone in item["analysis"] if tone["present"]))
                st.table([{"音名": tone["note"], "音程度数": tone["degree"],
                           "音程关系": tone["interval"], "半音差（mod 12）": tone["semitones"],
                           "状态": "已选" if tone["present"] else "省略"}
                          for tone in item["analysis"]])
                st.write(f"根音：{item['notes'][0]} · 实际最低音：{item['bass']}")
                if item["missing_notes"]:
                    st.warning("可能解释，省略了：" + "、".join(item["missing_notes"]) + "。这些音未实际弹奏，不能据此唯一确定和弦。")
                else:
                    st.success("所选音完整匹配 " + item["symbol"])
            st.caption("同一组音可能有多个名称，需要结合音乐上下文判断；斜杠后的音名表示实际最低音。候选优先完整匹配，其次省略音更少、根音在低音的解释；排序不是准确率。")
        else:
            st.info("当前条件下没有匹配。可以检查根音、开启省略音，或调整选音；未匹配不代表这些音不能构成和弦。")
            roots = [(chosen_root, note_to_pc(chosen_root))] if chosen_root else [(PITCH_NAMES[pc], pc) for pc in played]
            for name, root in roots:
                distances = sorted((pc - root) % 12 for pc in played)
                st.write(f"以 {name} 为根音：" + "、".join(map(str, distances)) + " 半音")

else:
    symbol = st.text_input("输入和弦名称", "C")
    try:
        info = chord_info(symbol)
    except ValueError as error:
        st.error(str(error))
        render_track()
        st.stop()
    root_pc = info["root_pc"]
    st.write(f"**{info['symbol']}** 的构成音：{'、'.join(info['notes'])}")
    st.caption("相对根音的半音距离：" + " · ".join(str(i) for i in info["intervals"]))
    highlights = {(p["string"], p["fret"]): p["note"]
                  for p in fretboard_positions(info["symbol"], max_fret)}
    if mode == "和弦音位置":
        st.caption("这些是可选位置；选择常用按法可查看一组同时弹奏的位置。")
    else:
        shape = KNOWN_SHAPES.get(info["symbol"])
        if shape is None:
            st.info("暂未收录这个和弦的常用按法；下方仍显示全部构成音位置。")
        else:
            shape_positions = {(s, f) for s, f in zip(TUNING_MIDI, shape) if f is not None}
            st.write("6 弦 → 1 弦：" + " · ".join("X" if f is None else str(f) for f in shape))
            st.caption("X = 不弹；0 = 空弦；其余数字 = 按住对应品位。")
            if info["symbol"] == "C":
                st.write("C 的常用手指安排：食指按 2 弦 1 品，中指按 4 弦 2 品，无名指按 5 弦 3 品；6 弦不弹，3 弦和 1 弦空弦。")
            if info["symbol"] == "F":
                st.write("F 的这组按法需要食指横按 1 品，再按住 3 弦 2 品、5 弦 3 品和 4 弦 3 品。")

if mode != "反向识别":
    st.plotly_chart(draw_board(max_fret, highlights, root_pc, shape_positions), width="stretch",
                    config={"displayModeBar": False, "scrollZoom": False})
    st.caption("黄色 = 和弦的其他构成音；红色 = 根音。悬停标签统一使用升号等音名。")
    if mode == "常用按法":
        st.caption("深色描边 = 常用按法的位置（含空弦）；所有彩色音符都是可选位置，无需同时按下。")

with st.expander("当前版本支持什么？"):
    st.write("支持大、小、减、增三和弦，sus2、sus4、7、maj7、m7、6、m6、m7b5、dim7、add9、madd9、9、maj9、m9、11、m11、13；例如 C、Am、G7、Bbmaj7。")
    st.write("常用按法目前收录 C、G、D、A、E、Am、Em、Dm、F。其他和弦可以查看构成音的全部位置。")
    st.write("反向识别支持指定根音、完整匹配及可选的根音/纯五音省略匹配，允许八度重复；不忽略额外音。十三和弦默认完整公式，六根弦无法弹全，需开启省略音。暂不支持斜杠和弦输入、自定义调弦和自动生成指法。")


render_track()
