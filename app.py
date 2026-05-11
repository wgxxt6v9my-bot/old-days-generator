"""
怀旧微电影脚本生成器
Nostalgic Short Film Script Generator

A Streamlit web app that transforms nostalgic themes into
Miyazaki-style 80s/90s Chinese life micro-film scripts.

运行命令 / Run command:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# 【核心配置】系统级 Prompt 模板
# 这里定义了整个生成任务的"灵魂"设定
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """
你是一位专注于中国城市记忆与生活烟火气的微电影编剧，同时深受宫崎骏治愈风格的熏陶。

你的任务是：根据用户提供的怀旧主题，创作一个微电影分镜脚本。

【风格要求】
- 画风：宫崎骏式治愈美学 —— 柔和的光晕、颗粒感的胶片质地、温暖的暖黄色调
- 年代感：80/90年代中国城市与乡镇日常生活，真实的市井烟火气
- 情感基调：治愈、温柔、带有淡淡的乡愁，让观众能闻到当时的气息
- 细节要求：每个镜头的视觉描述必须足够具体，可以直接作为 AI 绘图的 Prompt

【输出格式】
严格以 JSON 数组返回，每个元素包含：
- shot_id: 镜头序号（例如："01"）
- visual: 画面视觉描述（详细的 AI 绘图提示词，英文优先，包含光线、构图、色调）
- narration: 旁白或人物台词（中文，不超过 40 字）

【用户主题】
{theme}

请生成至少 4 个分镜头。
"""


# ─────────────────────────────────────────────────────────────────────────────
# 【MOCK 函数】模拟 LLM 返回数据，用于本地预览界面
#
# ⚠️  TODO: 接入真实 LLM 的位置在这里！
#    将 `mock_generate_script(theme)` 函数替换为下方的
#    `llm_generate_script(theme)` 函数即可。
#    支持的接入方式：
#      - OpenAI API:    client.chat.completions.create(...)
#      - Claude API:    anthropic.Anthropic().messages.create(...)
#      - 本地 Ollama:   requests.post("http://localhost:11434/api/chat", ...)
# ─────────────────────────────────────────────────────────────────────────────

def mock_generate_script(theme: str) -> list[dict]:
    """
    【Mock 函数】返回硬编码的假数据，用于点亮界面和验证布局。
    主题参数会被嵌入到第一行台词中，让演示更真实。
    """
    return [
        {
            "shot_id": "01",
            "visual": (
                "Wide shot, a narrow alley in a Chinese city circa 1990. "
                "An old man operates a popcorn cannon machine (爆米花机) on the street corner. "
                "Warm golden late-afternoon sunlight filters through plane trees, "
                "casting dappled shadows. Film grain texture, Studio Ghibli color palette, "
                "soft bokeh background of brick walls and clotheslines. 4:3 aspect ratio."
            ),
            "narration": f"那年夏天，{theme}的香气飘满了整条胡同。",
        },
        {
            "shot_id": "02",
            "visual": (
                "Close-up, a child's bare feet standing on warm concrete pavement. "
                "Worn plastic sandals beside them. A 5-jiao coin clutched in small fingers. "
                "Shallow depth of field, warm amber tones, nostalgic film grain, "
                "Miyazaki-style delicate line quality in background details."
            ),
            "narration": "手心里攥着妈妈给的五毛钱，心跳得很快。",
        },
        {
            "shot_id": "03",
            "visual": (
                "Medium shot, a group of neighborhood children crowding around the vendor, "
                "eyes wide with anticipation. Vintage Chinese thermos bottles and enamel basins "
                "visible in doorways. Dust particles float in golden light beams. "
                "Warm sepia overlay, hand-painted feel, early 1990s Beijing hutong atmosphere."
            ),
            "narration": "\"砰！\"的一声，白色的烟雾像云朵一样散开来。",
        },
        {
            "shot_id": "04",
            "visual": (
                "Slow pull-back aerial-style shot, the alley stretching into the distance "
                "at dusk. Paper lanterns beginning to glow in shop fronts. A cat sitting "
                "on a low wall watches the children run home. Sky painted in violet and orange. "
                "Dreamy Ghibli twilight, nostalgic vignette, 16mm film emulation."
            ),
            "narration": "多年以后，我才明白，那不只是爆米花的香气，是整个童年。",
        },
        {
            "shot_id": "05",
            "visual": (
                "Extreme close-up, a small hand holding a brown paper bag of popcorn. "
                "Steam rising gently. Soft focus background of the alley fading to memory. "
                "Warm cream and golden tones, timeless nostalgic feel, "
                "Studio Ghibli still-frame quality, subtle lens flare."
            ),
            "narration": "（画外音）有些味道，是回不去的时光。",
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 【TODO 模板】未来接入真实 LLM 时，用这个函数替换上面的 mock_generate_script
# ─────────────────────────────────────────────────────────────────────────────

# def llm_generate_script(theme: str) -> list[dict]:
#     """
#     真实 LLM 调用函数。
#     步骤：
#       1. 用 SYSTEM_PROMPT_TEMPLATE 构建完整 Prompt
#       2. 调用 LLM API（OpenAI / Claude / Ollama 等）
#       3. 解析返回的 JSON 字符串为 Python list[dict]
#       4. 返回结构化数据
#     """
#     import os, json
#     from openai import OpenAI  # pip install openai
#
#     client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
#     prompt = SYSTEM_PROMPT_TEMPLATE.format(theme=theme)
#
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "你是一位专业的微电影编剧。"},
#             {"role": "user",   "content": prompt},
#         ],
#         response_format={"type": "json_object"},
#         temperature=0.85,
#     )
#
#     raw = response.choices[0].message.content
#     data = json.loads(raw)
#     # LLM 可能把数组包在某个 key 里，做一层兼容处理
#     if isinstance(data, list):
#         return data
#     return data.get("shots") or data.get("script") or list(data.values())[0]


# ─────────────────────────────────────────────────────────────────────────────
# 【主函数】Streamlit 页面渲染逻辑
# ─────────────────────────────────────────────────────────────────────────────

def render_script_table(shots: list[dict]) -> None:
    """将分镜数据渲染为 Streamlit 表格"""
    rows = []
    for shot in shots:
        rows.append(
            {
                "镜头序号": f"🎬 #{shot['shot_id']}",
                "画面视觉描述（AI绘图提示词）": shot["visual"],
                "旁白 / 台词": shot["narration"],
            }
        )
    df = pd.DataFrame(rows)
    # 用 st.dataframe 支持列宽自适应和横向滚动
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "镜头序号": st.column_config.TextColumn(width="small"),
            "画面视觉描述（AI绘图提示词）": st.column_config.TextColumn(width="large"),
            "旁白 / 台词": st.column_config.TextColumn(width="medium"),
        },
        hide_index=True,
    )


def main():
    # ── 页面基础配置 ──────────────────────────────────────────────────────────
    st.set_page_config(
        page_title="怀旧微电影脚本生成器",
        page_icon="🎞️",
        layout="wide",
    )

    # ── 自定义样式：让整体更温暖、更有年代感 ──────────────────────────────────
    st.markdown(
        """
        <style>
        /* 全局字体与背景 */
        html, body, [class*="css"] {
            font-family: 'STKaiti', 'KaiTi', 'SimSun', serif;
        }
        /* 标题装饰线 */
        .main-title {
            text-align: center;
            color: #5c3d1e;
            font-size: 2.4rem;
            letter-spacing: 0.1em;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            text-align: center;
            color: #9e7b50;
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        /* 按钮颜色 */
        div.stButton > button {
            background-color: #c8864a;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            font-size: 1.05rem;
            letter-spacing: 0.08em;
            transition: background-color 0.2s;
        }
        div.stButton > button:hover {
            background-color: #a0652e;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── 页面标题 ──────────────────────────────────────────────────────────────
    st.markdown('<h1 class="main-title">🎞️ 怀旧微电影脚本生成器</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-title">宫崎骏式治愈画风 × 80/90年代中国生活烟火气</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── 输入区域 ──────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        theme = st.text_input(
            label="✏️ 输入你的怀旧主题",
            placeholder="例如：胡同口的爆米花、夏天的冰棍、供销社的糖果、黑白电视机前的春晚…",
            help="输入一个能唤起童年记忆的具体事物或场景，生成器将为你创作 5 个分镜头脚本。",
        )

        generate_btn = st.button("🎬 开始生成流水线", use_container_width=True)

    st.divider()

    # ── 生成逻辑 ──────────────────────────────────────────────────────────────
    if generate_btn:
        if not theme.strip():
            st.warning("⚠️ 请先输入一个怀旧主题，再点击生成按钮。")
            return

        with st.spinner("🎞️ 正在调取记忆碎片，构建分镜脚本…"):
            # ──────────────────────────────────────────────────────────────────
            # ⚠️  【LLM 接入点】
            # 当前调用的是 Mock 函数，返回假数据。
            # 当你准备好接入真实 LLM 时：
            #   1. 取消注释上方的 `llm_generate_script` 函数
            #   2. 将下面这行改为：shots = llm_generate_script(theme)
            # ──────────────────────────────────────────────────────────────────
            shots = mock_generate_script(theme)

        # ── 结果展示 ──────────────────────────────────────────────────────────
        st.success(f"✅ 脚本生成完毕！共 {len(shots)} 个分镜头")
        st.subheader(f"📽️ 主题：「{theme}」—— 微电影分镜脚本")

        render_script_table(shots)

        st.markdown(
            """
            ---
            > 💡 **下一步**：将「画面视觉描述」列的内容复制到 [Midjourney](https://www.midjourney.com)、
            > [DALL·E](https://openai.com/dall-e-3) 或 [Stable Diffusion](https://stability.ai) 中，
            > 即可生成对应的分镜概念图。
            """
        )

    else:
        # 未点击按钮时显示使用说明
        st.info(
            "👆 在上方输入一个能唤起童年记忆的主题，然后点击「开始生成流水线」按钮，"
            "即可获得一份完整的宫崎骏风格怀旧微电影分镜脚本。"
        )
        with st.expander("📖 关于这个工具", expanded=False):
            st.markdown(
                """
                **怀旧微电影脚本生成器** 是一个基于 LLM 的创意辅助工具，帮助你将一个模糊的童年记忆，
                转化为可以立刻付诸实践的微电影分镜脚本。

                **工作流程：**
                1. 🖊️ 输入怀旧主题（一个具体的事物或场景）
                2. 🤖 系统构建专业的编剧级 Prompt，注入宫崎骏美学设定
                3. 📋 以表格形式输出每个分镜的视觉描述和台词
                4. 🎨 将视觉描述复制到 AI 绘图工具，生成概念图

                **当前状态：** Mock 演示模式（可一键切换为真实 LLM）
                """
            )


if __name__ == "__main__":
    main()
