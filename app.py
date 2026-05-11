"""
怀旧微电影脚本生成器
Nostalgic Short Film Script Generator

A Streamlit web app that transforms nostalgic themes into
Miyazaki-style 80s/90s Chinese life micro-film scripts.

运行命令 / Run command:
    streamlit run app.py

环境变量 / Environment variable:
    DEEPSEEK_API_KEY=your_key_here streamlit run app.py
"""

import os
import json
import streamlit as st
import pandas as pd
from openai import OpenAI


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
# 【DeepSeek 配置】API 客户端初始化
# Key 通过环境变量读取，绝不硬编码
# ─────────────────────────────────────────────────────────────────────────────

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL    = "deepseek-chat"   # DeepSeek 当前旗舰模型


def _get_client() -> OpenAI:
    """创建并返回指向 DeepSeek API 的 OpenAI 兼容客户端。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "未检测到 DEEPSEEK_API_KEY 环境变量。\n"
            "请先执行：export DEEPSEEK_API_KEY=your_key_here"
        )
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


# ─────────────────────────────────────────────────────────────────────────────
# 【真实 LLM 函数】调用 DeepSeek V4 Pro 生成分镜脚本
# ─────────────────────────────────────────────────────────────────────────────

def llm_generate_script(theme: str) -> list[dict]:
    """
    调用 DeepSeek API，根据主题生成微电影分镜脚本。

    流程：
      1. 从环境变量读取 API Key，构建 OpenAI 兼容客户端
      2. 用 SYSTEM_PROMPT_TEMPLATE 填充用户主题，构建完整 Prompt
      3. 以 JSON 模式请求 DeepSeek，要求模型严格返回 JSON 数组
      4. 解析并做兼容性处理后返回 list[dict]

    Returns:
        list[dict]，每个元素含 shot_id / visual / narration 三个字段
    """
    client = _get_client()
    prompt = SYSTEM_PROMPT_TEMPLATE.format(theme=theme)

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位专业的微电影编剧。"
                    "请严格按照用户要求，以纯 JSON 格式返回分镜脚本，"
                    "不要附加任何解释性文字或 markdown 代码块标记。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.85,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content

    # ── 解析 JSON，兼容模型将数组包裹在不同 key 里的情况 ──────────────────────
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    # 尝试常见 key 名
    for key in ("shots", "script", "scenes", "storyboard", "分镜"):
        if key in data and isinstance(data[key], list):
            return data[key]
    # 兜底：取第一个 list 类型的值
    for v in data.values():
        if isinstance(v, list):
            return v
    raise ValueError(f"无法从 LLM 响应中解析出分镜数组，原始内容：\n{raw}")


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

        with st.spinner("🎞️ 正在连接 DeepSeek，召唤记忆碎片…"):
            try:
                shots = llm_generate_script(theme)
            except EnvironmentError as e:
                st.error(f"🔑 **API Key 未配置**\n\n{e}")
                return
            except Exception as e:
                st.error(f"❌ **生成失败**，请检查网络或 API Key 是否有效。\n\n错误详情：`{e}`")
                return

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

                **当前状态：** 已接入 DeepSeek API（`deepseek-chat` 模型）
                """
            )


if __name__ == "__main__":
    main()
