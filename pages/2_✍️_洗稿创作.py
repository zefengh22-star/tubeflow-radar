import os
import sys

# ==========================================
# 🧨 终极网络修复：彻底拔掉所有代理管子！
# ==========================================
proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]
for key in proxy_keys:
    if key in os.environ:
        del os.environ[key]

# 💥 核心修复：强制接管 Windows 底层编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
import sqlite3
import pandas as pd
from google import genai
from google.genai import types

# 🔑 全局配置：你的 Gemini API Key
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'radar_v1.db')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# 🌌 强效注入纯黑/暗色系极简科技 UI 风格
# ==========================================

st.markdown("""
    <style>
    .main {background-color: #0d0e15; color: #ffffff;}
    div[data-testid="stRadio"] > div {gap: 1.5rem;}
    /* 强行拉长文本框并优化排版阅读体验 */
    .stTextArea textarea {font-size: 1.05rem !important; line-height: 1.8 !important;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 💾 初始化核心状态缓存
# ==========================================
if "raw_transcript" not in st.session_state:
    st.session_state.raw_transcript = ""
if "final_script" not in st.session_state:
    st.session_state.final_script = ""
if "current_vid" not in st.session_state:
    st.session_state.current_vid = ""

st.title("✍️ youtube文案修改")
st.caption("核心逻辑：双屏对照工作流 | 左侧原文分段管控 -> 右侧人设矩阵裂变 -> 终稿无缝精修")
st.markdown("---")

# ==========================================
# 🔝 顶部控制台：选材与抓取
# ==========================================
video_options = []
video_dict = {}

try:
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT video_id, title, channel_name FROM videos ORDER BY hot_score DESC LIMIT 50", conn)
        conn.close()
        
        for _, row in df.iterrows():
            label = f"[{row['channel_name']}] {row['title']}"
            vid = row['video_id']
            video_options.append(label)
            video_dict[label] = vid
except Exception as e:
    st.error(f"无法读取数据库: {e}")

st.markdown("**📥 参考视频列表：**")
col_select, col_btn = st.columns([4, 1])

with col_select:
    if not video_options:
        st.warning("暂无爆款数据，请先去首页大盘探测一波！")
        selected_label = None
        selected_vid = None
    else:
        selected_label = st.selectbox("选择视频", video_options, label_visibility="collapsed")
        selected_vid = video_dict.get(selected_label)

# 💡 安全获取对象属性的辅助函数
def get_val(item, key, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)

with col_btn:
    if st.button("🔌 提取文案", use_container_width=True):
        if not selected_vid:
            st.warning("请选择有效视频")
        else:
            with st.spinner("正在提取字幕并分析时间轴断句..."):
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
                    
                    try:
                        transcript_list = YouTubeTranscriptApi().list(selected_vid)
                    except AttributeError:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(selected_vid)
                    
                    try:
                        transcript = transcript_list.find_transcript(['zh-CN', 'zh-Hans', 'zh-TW', 'zh-Hant', 'zh'])
                        lang_msg = "✅ 成功提取原生中文字幕！"
                    except:
                        transcript = list(transcript_list)[0]
                        lang_msg = "✅ 成功提取原生外语字幕！"
                        
                    snippets = transcript.fetch()
                    
                    # 💡 方案三：真实“呼吸停顿”切分法
                    formatted_text = ""
                    for i in range(len(snippets)):
                        current = snippets[i]
                        
                        text = str(get_val(current, 'text', '')).replace('\n', ' ').strip()
                        if not text: continue
                        
                        formatted_text += text + " "
                        
                        if i < len(snippets) - 1:
                            next_snippet = snippets[i+1]
                            
                            c_start = float(get_val(current, 'start', 0.0))
                            c_duration = float(get_val(current, 'duration', 0.0))
                            n_start = float(get_val(next_snippet, 'start', 0.0))
                            
                            current_end_time = c_start + c_duration
                            
                            if (n_start - current_end_time) > 1.5:
                                formatted_text += "\n\n"
                    
                    st.session_state.raw_transcript = formatted_text.strip()
                    st.session_state.current_vid = selected_vid
                    st.session_state.final_script = "" 
                    
                    st.toast(lang_msg, icon="🎉")
                    st.rerun()
                
                except TranscriptsDisabled:
                    st.error("🚫 提取失败，该视频无字幕轨道")
                except NoTranscriptFound:
                    st.error("🚫 提取失败：找不到可用的文本流！")
                except Exception as e:
                    st.error(f"⚠️ 遭遇未知底层拦截: {str(e)}")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# ⚖️ 中部双屏工作区：左侧原文 vs 右侧创作
# ==========================================
col_left, col_right = st.columns([1, 1], gap="large")

# -----------------
# 👈 左侧：视频原文案编辑区
# -----------------
with col_left:
    st.subheader("📄 原视文案")
    st.caption("✨ 已根据博主真实停顿频率自动分段。支持按需删减，只保留精华片段。")
    
    edited_raw_text = st.text_area(
        "原文编辑区", 
        value=st.session_state.raw_transcript, 
        height=650, 
        label_visibility="collapsed"
    )
    st.session_state.raw_transcript = edited_raw_text

# -----------------
# 👉 右侧：AI 裂变引擎与终稿区
# -----------------
with col_right:
    st.subheader("🎭 风格修改")
    
    persona_options = {
        "老板流派 (我花了几十万广子费发现...)": """
        你是一个在商业前线摸爬滚打多年的务实老板。说话一针见血，不搞废话，喜欢用“钱”、“成本”、“效率”、“避坑”来切入。
        口头禅：说实话、听懂掌声、底层逻辑。
        目标：把枯燥的技术/知识转化为能赚钱或省钱的商业洞察。
        """,
        "逗比流派 (作为跨境圈一线老忽悠...)": """
        你是一个幽默风趣、带点痞气、喜欢自嘲的行业老油条。经常用搞怪的比喻，说话像说相声。
        口头禅：兄弟们、家人们、我直接好家伙。
        目标：在极度娱乐化的氛围中把硬核干货喂给观众。
        """,
        "技术流派 (很多人不知道网络底层的差别...)": """
        你是一个极其严谨、有代码洁癖的高级工程师。说话逻辑极其严密，喜欢分类、列点（一、二、三）。
        风格：专业名词不离口，但能用最直白的话解释复杂概念。
        目标：建立绝对的专业权威感，让小白觉得“虽然听不懂但大受震撼”。
        """,
        "故事流派 (去年有个客户听了教程结果被封号...)": """
        你是一个擅长讲故事的深夜电台风格博主。永远从一个具体的人、一件具体的惨痛经历开始引入。
        风格：娓娓道来，制造悬念，情绪价值拉满。
        目标：通过故事引发极强的情感共鸣，顺带输出干货。
        """
    }
    
    selected_persona = st.radio("选择人设：", list(persona_options.keys()), label_visibility="collapsed")
    
    context_text = st.text_input("风格上下文（可选）：", placeholder="例如：语气要犀利，节奏要快，开头3秒用冲突句子抓眼球...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- 生成按钮 ---
    if st.button("🚀 根据风格修改文案", type="primary", use_container_width=True):
        
        if not GEMINI_API_KEY:
            st.error("请先在系统环境变量中配置 GEMINI_API_KEY。")
        elif not st.session_state.raw_transcript.strip():
            st.error("🚨 左侧没有可供提取的底稿！请先提取官方字幕或手动粘贴文本。")
        else:
            with st.spinner("🤖 引擎已激活，正在按结构化逻辑流全速重构爆款脚本..."):
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    
                    persona_prompt = persona_options[selected_persona]
                    prompt = f"""
                    你现在是 TubeFlow 的首席内容重构官。
                    
                    【你的人设与语气指令】
                    {persona_prompt}
                    {f'【补充风格要求】: {context_text}' if context_text else ''}
                    
                    【任务目标】
                    这是一段从 YouTube 爆款视频中提取的未经排版的原始字幕流（可能是英文也可能是中文）。
                    如果底稿是外语，请直接将其无缝翻译并重构为中文。
                    你需要完全吸收这篇字幕的*核心信息*和*知识点*，然后完全摒弃原作者的说话方式和结构。
                    用你的人设，重新创作一篇**全新、高爆款率、节奏紧凑**的短视频/中视频文案。
                    
                    【约束条件】
                    1. 绝不允许编造原始字幕中没有的核心事实。
                    2. 开头前5秒（前50个字）必须有极强的钩子（Hook），留住观众。
                    3. 直接输出洗稿后的正文，不要有任何多余的废话和自我介绍。
                    4. 【核心排版与分段要求】：强制采用结构化逻辑流分段（通常顺序为：钩子引入 -> 痛点/背景分析 -> 核心干货步骤/解决方案 -> 结尾呼应）。每段必须保持在 3 到 4 句话左右，段落与段落之间必须空一行（即输出两个换行符）。严禁输出不分段、密密麻麻的文字墙！
                    
                    【待重构原始底稿】
                    {st.session_state.raw_transcript[:15000]} 
                    """
                    
                    fallback_models = [
                        'gemini-2.0-flash', 
                        'gemini-1.5-flash',       
                        'gemini-1.5-flash-002'    
                    ]
                    
                    final_response = None
                    error_logs = []
                    
                    for model_name in fallback_models:
                        try:
                            final_response = client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    safety_settings=[
                                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                                    ]
                                )
                            )
                            break 
                        except Exception as e:
                            error_logs.append(f"[{model_name} 引擎拦截] {str(e)}")
                            continue
                            
                    if final_response:
                        st.session_state.final_script = final_response.text
                        st.rerun() 
                    else:
                        st.error("🚨 核心引擎无响应，诊断日志如下：")
                        for log in error_logs:
                            st.warning(log)
                            
                except Exception as e:
                    st.error(f"系统严重错误: {e}")

    st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # --- 最终输出框 ---
    st.subheader("🎬 最终口播稿")
    
    edited_final_script = st.text_area(
        "最终口播稿区", 
        value=st.session_state.final_script, 
        height=350, 
        label_visibility="collapsed"
    )
    st.session_state.final_script = edited_final_script
