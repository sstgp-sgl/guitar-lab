"""Bar-based chord track editor with a beat-aligned timeline."""
import re

import streamlit as st
import plotly.graph_objects as go

from core import resolve_track_chord

METERS = {"4/4": 4, "3/4": 3, "6/8": 6}



def chord_color(item):
    intervals = set(item["intervals"])
    if 6 in intervals or 8 in intervals:
        return "#b76bce"  # altered fifth
    if 4 in intervals and 10 in intervals:
        return "#df8750"  # dominant family
    if 3 in intervals:
        return "#598bd5"  # minor family
    if 4 not in intervals:
        return "#89969c"  # suspended
    return "#32aa91"  # major family


def overview_figures(bars, tonic, mode, meter):
    """Four bars per row; x is onset in beats, y is root in C4–B4."""
    beats = METERS[meter]
    figures = []
    for start in range(0, len(bars), 4):
        fig = go.Figure()
        xs, ys, labels, colors, hover = [], [], [], [], []
        line_x, line_y = [], []
        for local, bar in enumerate(bars[start:start + 4]):
            base = local * beats
            if sum(slot["beats"] for slot in bar["slots"]) > beats:
                fig.add_annotation(x=base + beats / 2, y=6, text="占拍超限", showarrow=False)
                line_x.append(None)
                line_y.append(None)
                continue
            offset = 0
            for slot in bar["slots"]:
                try:
                    item = resolve_track_chord(slot["input"], tonic, mode)
                except ValueError:
                    line_x.append(None)
                    line_y.append(None)
                    offset += slot["beats"]
                    continue
                x, y = base + offset, item["root_pc"]
                xs.append(x)
                ys.append(y)
                labels.append(item["degree_symbol"])
                colors.append(chord_color(item))
                hover.append(f"第 {start + local + 1} 小节 · 第 {offset + 1} 拍 · 占 {slot['beats']} 拍")
                line_x.append(x)
                line_y.append(y)
                fig.add_shape(type="line", x0=x, x1=x + slot["beats"], y0=y, y1=y,
                              line=dict(color=colors[-1], width=5), opacity=.35)
                offset += slot["beats"]
            if offset < beats:
                line_x.append(None)
                line_y.append(None)
        fig.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines",
                                 line=dict(color="#94aaa7", width=1.5), hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, text=labels, mode="markers+text",
                                 marker=dict(size=42, color=colors, line=dict(color="white", width=1)),
                                 textfont=dict(size=11, color="white"),
                                 hovertext=hover, hovertemplate="%{text}<br>%{hovertext}<extra></extra>"))
        for boundary in range(5):
            fig.add_vline(x=boundary * beats, line_width=1, line_color="rgba(130,150,160,.35)")
        fig.update_layout(height=220, margin=dict(l=12, r=24, t=15, b=30), showlegend=False,
                          plot_bgcolor="rgba(120,145,160,.05)", paper_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(range=[-.6, beats * 4 + .5], fixedrange=True, zeroline=False,
                                     tickvals=[i * beats + beats / 2 for i in range(4)],
                                     ticktext=[f"第 {start+i+1} 小节" if start+i < len(bars) else "" for i in range(4)],
                                     showgrid=False),
                          yaxis=dict(range=[-2, 13], visible=False, fixedrange=True))
        figures.append(fig)
    return figures

def render_track():
    if not st.session_state.get("show_chord_track", False):
        return
    st.divider()
    st.header("和弦轨道")

    def remember(widget, saved):
        st.session_state[saved] = st.session_state[widget]

    defaults = {"track_tonic": "C", "track_mode": "大调", "track_meter": "4/4"}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
        st.session_state[f"edit_{key}"] = st.session_state[key]
    cols = st.columns(3)
    tonics = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]
    tonic = cols[0].selectbox("歌曲主音", tonics, key="edit_track_tonic",
                             on_change=remember, args=("edit_track_tonic", "track_tonic"))
    mode = cols[1].selectbox("调式", ["大调", "自然小调"], key="edit_track_mode",
                            on_change=remember, args=("edit_track_mode", "track_mode"))
    meter = cols[2].selectbox("拍号", list(METERS), key="edit_track_meter",
                             on_change=remember, args=("edit_track_meter", "track_meter"))
    beats = METERS[meter]
    st.caption("在每个模块中输入和弦名或数字标记，按 Enter 或移开焦点后自动换算。例如 Cmaj7 ↔ 1maj7、G7 ↔ 57（5 级 + 7 后缀）。裸数字表示大三和弦，小和弦请写 m。")
    st.caption("换调会重新解释数字输入（随调移调），字母输入保持原和弦。4/4、3/4 的占拍单位为四分音符；6/8 为八分音符，按 3+3 分组。")
    if "track_bars" not in st.session_state:
        tokens = [t for t in re.split(r"[\s,，|｜;；]+", st.session_state.get("track_text", "Cmaj7 Am7 Dm7 G7").strip()) if t]
        st.session_state.track_bars = [
            {"id": i, "slots": [{"id": i, "input": token, "beats": 4}]}
            for i, token in enumerate(tokens)] or [{"id": 0, "slots": []}]
        st.session_state.track_next_id = max(1, len(tokens))

    def new_id():
        value = st.session_state.track_next_id
        st.session_state.track_next_id += 1
        return value

    def add_bar():
        st.session_state.track_bars.append({"id": new_id(), "slots": []})

    def remove_bar(bar_id):
        st.session_state.track_bars = [b for b in st.session_state.track_bars if b["id"] != bar_id]

    def add_slot(bar_id):
        bar = next(b for b in st.session_state.track_bars if b["id"] == bar_id)
        remaining = METERS[st.session_state.track_meter] - sum(s["beats"] for s in bar["slots"])
        bar["slots"].append({"id": new_id(), "input": "", "beats": max(1, remaining)})

    def remove_slot(bar_id, slot_id):
        bar = next(b for b in st.session_state.track_bars if b["id"] == bar_id)
        bar["slots"] = [s for s in bar["slots"] if s["id"] != slot_id]

    def edit_slot(bar_id, slot_id, field, widget):
        bar = next(b for b in st.session_state.track_bars if b["id"] == bar_id)
        slot = next(s for s in bar["slots"] if s["id"] == slot_id)
        slot[field] = st.session_state[widget]

    st.markdown("""<style>
    .st-key-track_lane [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-track_bar_"]) {
        flex-wrap: nowrap !important; overflow-x: auto; padding: 10px 2px 18px;
        align-items: stretch;
    }
    .st-key-track_lane [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-track_bar_"]) > [data-testid="stColumn"] {
        min-width: 360px; flex: 1 0 360px !important;
    }
    [class*="st-key-track_bar_"] {
        border-top: 3px solid #35a594; border-left: 1px solid #8394a5;
        padding: 10px; background: rgba(120,145,160,.06);
    }
    [class*="st-key-track_slots_"] [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; overflow-x: auto;
    }
    [class*="st-key-track_slots_"] [data-testid="stColumn"] {min-width: 150px;}
    [class*="st-key-track_slot_"] {
        border: 1px solid #35a594; border-radius: 8px; padding: 8px;
    }
    </style>""", unsafe_allow_html=True)
    st.caption("直接在下方轨道格子里修改；小节较多时横向滚动。")
    st.button("＋ 添加小节", key="add_track_bar", on_click=add_bar)
    bars = st.session_state.track_bars
    if not bars:
        st.info("点击添加小节，开始编排。")
        return
    with st.container(key="track_lane"):
        bar_columns = st.columns(len(bars), gap="small")
        for number, (bar, column) in enumerate(zip(bars, bar_columns), 1):
            bid = bar["id"]
            with column, st.container(key=f"track_bar_{bid}"):
                st.markdown(f"**第 {number} 小节 · {meter}**")
                st.caption("拍位  " + " ─ ".join(str(i) for i in range(1, beats + 1)))
                total = sum(s["beats"] for s in bar["slots"])
                with st.container(key=f"track_slots_{bid}"):
                    if bar["slots"]:
                        slot_columns = st.columns([s["beats"] for s in bar["slots"]], gap="small")
                        offset = 1
                        for slot, slot_column in zip(bar["slots"], slot_columns):
                            sid = slot["id"]
                            with slot_column, st.container(key=f"track_slot_{sid}"):
                                st.caption(f"第 {offset} 拍起")
                                input_key, beats_key = f"slot_input_{sid}", f"slot_beats_{sid}"
                                st.session_state[input_key] = slot["input"]
                                st.session_state[beats_key] = slot["beats"]
                                st.text_input("和弦名 / 数字", key=input_key,
                                              placeholder="Cmaj7 / 1maj7", label_visibility="collapsed",
                                              on_change=edit_slot, args=(bid, sid, "input", input_key))
                                if slot["input"]:
                                    try:
                                        item = resolve_track_chord(slot["input"], tonic, mode)
                                        st.write(f"**{item['symbol']} ↔ {item['degree_symbol']}**")
                                        st.caption(" · ".join(item["notes"]))
                                        if item["outside_notes"]:
                                            st.caption("调外音：" + "、".join(item["outside_notes"]))
                                    except ValueError:
                                        st.error("无法识别，请输入如 Cmaj7 或 1maj7。")
                                else:
                                    st.caption("输入和弦，自动换算")
                                st.number_input("占拍", min_value=1, max_value=16, step=1,
                                                key=beats_key, on_change=edit_slot,
                                                args=(bid, sid, "beats", beats_key))
                                st.button("删除和弦", key=f"remove_slot_{sid}",
                                          on_click=remove_slot, args=(bid, sid))
                            offset += slot["beats"]
                if total > beats:
                    st.error(f"{total}/{beats} 拍：超出小节，请缩短占拍。")
                elif total < beats:
                    st.caption(f"{total}/{beats} 拍 · 剩余 {beats-total} 拍休止 / 待填")
                else:
                    st.caption(f"{total}/{beats} 拍")
                st.button("＋ 和弦", key=f"add_slot_{bid}", on_click=add_slot, args=(bid,))
                st.button("删除小节", key=f"remove_bar_{bid}", on_click=remove_bar, args=(bid,))
    st.caption("当前为可视编排，尚不播放音频；内容保留在本次会话。")

    st.markdown("**和弦走向 · 数字总览**")
    st.caption("每行四小节；圆点位于起拍，横线长度表示占拍。高度按根音 C4–B4 排列，不代表实际指法八度。空白或无效输入留空，占拍超限的小节暂不绘制。")
    st.caption("绿色：大和弦类 · 蓝色：小和弦类 · 橙色：属七类 · 紫色：增/减五音类 · 灰色：挂留类（颜色表示和弦结构）")
    for index, figure in enumerate(overview_figures(bars, tonic, mode, meter)):
        st.plotly_chart(figure, key=f"track_overview_{index}", width="stretch",
                        config={"displayModeBar": False, "scrollZoom": False})
