import streamlit as st
import yt_dlp
import sqlite3
import pandas as pd
import numpy as np
import os
import re
import time
import random
from datetime import datetime, timedelta
import concurrent.futures

# ==========================================
# 强效注入纯黑/暗色系极简科技 UI 风格
# ==========================================
st.set_page_config(page_title="TubeFlow Radar 1.0", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #0d0e15; color: #ffffff;}
    .stDataFrame {font-size: 1.05rem;}
    div[data-testid="stRadio"] > div {gap: 2rem;}
    div[data-testid="stExpander"] {background-color: #161923; border: 1px solid #262936;}
    </style>
    """, unsafe_allow_html=True)

# 🚀 页面秒开，直接渲染标题！
st.title("TubeFlow Radar 1.0 —— 爆款中控首页")
st.caption("同步机制：手动极速巡航对标账号 | 完美对齐 VidIQ 爆发倍数算法")
st.markdown("---")

# ==========================================
# 数据库自动建表与防锁死脏数据清洗
# ==========================================
db_dir = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(db_dir): os.makedirs(db_dir)
db_path = os.path.join(db_dir, 'radar_v1.db')

conn = sqlite3.connect(db_path, timeout=20)
c = conn.cursor()

c.execute("PRAGMA journal_mode=WAL;") 

c.execute('''CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY, title TEXT, channel_name TEXT, 
                views INTEGER, channel_avg_views REAL DEFAULT 0, outlier_score REAL DEFAULT 1.0, 
                vph REAL, hot_score REAL, url TEXT, publish_time TEXT, 
                transcript TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

try:
    c.execute("DELETE FROM videos WHERE publish_time = '未知' OR publish_time IS NULL")
    conn.commit()
except sqlite3.OperationalError:
    pass

# ==========================================
# 出海短视频、技术与 AI 矩阵究极对标库
# ==========================================
TARGET_CHANNELS = {
    "安格视界": "https://www.youtube.com/@Ange-Digital-Life", "IT咖啡馆": "https://www.youtube.com/@it-coffee",
    "搞机零距离": "https://www.youtube.com/@gaojilingjuli", "零度解说": "https://www.youtube.com/@lingdujieshuo",
    "秋芝2046": "https://www.youtube.com/@qiuzhi2046", "Alchain花生": "https://www.youtube.com/@Alchain",
    "技术爬爬虾": "https://www.youtube.com/@tech-shrimp", "林粒粒呀": "https://www.youtube.com/@linliliya",
    "P & H": "https://www.youtube.com/@PH-WorkFlow", "数字指南针": "https://www.youtube.com/@realshuzi",
    "李厂长来了": "https://www.youtube.com/@lichangzhanglaile", "追日Gucci": "https://www.youtube.com/@GuccixAI", 
    "陶渊小明": "https://www.youtube.com/@a--yuan", "學長Ethan": "https://www.youtube.com/@TikTokEthan", 
    "木子不写代码": "https://www.youtube.com/@木子不写代码", "七七行銷筆记": "https://www.youtube.com/@77MediaBook", 
    "简单了解": "https://www.youtube.com/@chen-r2l", "科技lion": "https://www.youtube.com/@kejilion", 
    "大时叔叔": "https://www.youtube.com/@spacenw", "泛科學院": "https://www.youtube.com/@panscischool", 
    "大有牧森": "https://www.youtube.com/@austinchou888", "老蓝": "https://www.youtube.com/@bluesocks152", 
    "Jeff Su": "https://www.youtube.com/@JeffSu", "3cTim哥": "https://www.youtube.com/@3ctim", 
    "嚕嚕科技": "https://www.youtube.com/@LuluTechnology1", "卢菁博士": "https://www.youtube.com/@人工智能AI卢菁博士", 
    "小in分享": "https://www.youtube.com/@xiaoinfx", "漢克蔡": "https://www.youtube.com/@ainthology", 
    "木子AI研究所": "https://www.youtube.com/@muziailab", "电丸科技AK": "https://www.youtube.com/@VideoTalkAK", 
    "极客湾": "https://www.youtube.com/@Geekerwan", "司马评测": "https://www.youtube.com/@simapingce", 
    "影视飓风": "https://www.youtube.com/@MediaStorm", "科技美学": "https://www.youtube.com/@kejimeixue", 
    "王天禹": "https://www.youtube.com/@wongtianyu", "小红书跨境老兵": "https://www.youtube.com/@xiaohongshukuajing", 
    "跨境零距离": "https://www.youtube.com/@kuajinglingjuli", "AI自动化工坊": "https://www.youtube.com/@aiazautomation", 
    "矩阵通": "https://www.youtube.com/@juzhengtong", "出海老白": "https://www.youtube.com/@chuhailaobai", 
    "独立站大兵": "https://www.youtube.com/@dulizhandabing", "流量密码": "https://www.youtube.com/@liuliangmima", 
    "TikTok一哥": "https://www.youtube.com/@tiktokyige", "网赚极客": "https://www.youtube.com/@wangzhuanjike", 
    "海外黑马站": "https://www.youtube.com/@haiwaiheima", "信息差套利指南": "https://www.youtube.com/@xinxichataoli", 
    "自动化神兵": "https://www.youtube.com/@automationgod", "AI短视频搞钱": "https://www.youtube.com/@aishortvideo", 
    "出海操盘手": "https://www.youtube.com/@chuhaicaopanshou",
    
    "IPCheese": "https://www.youtube.com/@IPCheese",
    "ToolShark": "https://www.youtube.com/@toolshark",
    "数字游鱼": "https://www.youtube.com/@DigitalNomadFish", 
    "傅云飞飞": "https://www.youtube.com/@fuyunfeifei",
    "kookeey-小沙日记": "https://www.youtube.com/@kookeey",
    "小黑TIME": "https://www.youtube.com/@xiaoheitime",
    "Hacker闪电": "https://www.youtube.com/@hackershandian",
    "在下小曾。": "https://www.youtube.com/@zaixiaxiaozeng",
    "Porter科技迷": "https://www.youtube.com/@PorterTech",
    "出海指南针": "https://www.youtube.com/@chuhai_compass",
    "Metics Media": "https://www.youtube.com/@MeticsMedia",
    "科技分享": "https://www.youtube.com/@kejifenxiang",
    "PAPAYA電腦教室": "https://www.youtube.com/@papayaclass",
    "小白AI笔记": "https://www.youtube.com/@xiaobaiaibiji",
    "松小鼠呀": "https://www.youtube.com/@songxiaoshu",
    "黄思平": "https://www.youtube.com/@huang_siping",
    "科技加工坊": "https://www.youtube.com/@tech_workshop",
    "AI超元域": "https://www.youtube.com/@aichaoyuanyu"
}
TARGET_NAMES = list(TARGET_CHANNELS.keys())

def extract_date_from_str(date_str):
    if not date_str: return None
    try:
        return datetime.strptime(re.sub(r'\D', '', str(date_str))[:8], "%Y%m%d")
    except: return None

# ==========================================
# 核心下钻引擎
# ==========================================
def get_real_channel_avg(channel_url, fallback_subs, cache_dict, channel_name):
    if channel_name in cache_dict: return cache_dict[channel_name]
    if channel_name in TARGET_CHANNELS: channel_url = TARGET_CHANNELS[channel_name]
    baseline_views = max(fallback_subs * 0.02, 1000) if fallback_subs else 1000

    if not channel_url: return baseline_views
    ydl_opts_fast = {"quiet": True, "extract_flat": "in_playlist", "playlist_items": "1-12", "no_warnings": True, "socket_timeout": 8}
    
    try:
        time.sleep(random.uniform(0.5, 1.5))
        with yt_dlp.YoutubeDL(ydl_opts_fast) as ydl_temp:
            target_url = channel_url if channel_url.endswith("/videos") else f"{channel_url}/videos"
            c_info = ydl_temp.extract_info(target_url, download=False)
            v_list = [v.get('view_count') for v in list(c_info.get('entries', [])) if v and v.get('view_count') is not None]
            if v_list: 
                avg = np.median(v_list)
                cache_dict[channel_name] = avg
                return avg
    except: pass
    
    cache_dict[channel_name] = baseline_views
    return baseline_views

def process_target_channel(ch_name, ch_url, one_year_ago):
    ydl_opts = {
        "quiet": True, "extract_flat": False, "playlist_items": "1-12", "no_warnings": True,
        "socket_timeout": 12, "extractor_args": {"youtube": {"skip": ["hls", "dash"]}}
    }
    results = []
    try:
        time.sleep(random.uniform(0.2, 1.5))
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            target_url = ch_url if ch_url.endswith("/videos") else f"{ch_url}/videos"
            c_info = ydl.extract_info(target_url, download=False)
            entries = c_info.get("entries", [])
            
            valid_views = [e.get("view_count") for e in entries if e and e.get("view_count") is not None]
            real_avg = np.median(valid_views) if valid_views else 1000
            
            for e in entries:
                if not e: continue
                views, vid = e.get("view_count") or 0, e.get("id")
                
                pub_date = None
                if e.get("timestamp"): pub_date = datetime.fromtimestamp(e.get("timestamp"))
                elif e.get("upload_date"): pub_date = extract_date_from_str(e.get("upload_date"))
                
                if not pub_date or pub_date < one_year_ago: continue
                
                hours_passed = max((datetime.now() - pub_date).total_seconds() / 3600, 1.0)
                outlier_score = views / real_avg if real_avg > 0 else 1.0
                vph = views / hours_passed
                score = (outlier_score * 50) + (np.log1p(vph) * 10)
                
                results.append((vid, e.get("title"), ch_name, views, real_avg, outlier_score, vph, score, f"https://www.youtube.com/watch?v={vid}", pub_date.strftime("%Y-%m-%d")))
    except: pass
    return results

def process_single_search_entry(e, one_year_ago, cache_dict):
    vid, title, channel = e.get("id"), e.get("title"), e.get("uploader")
    if not title or not vid: return None

    ydl_opts_detail = {
        "quiet": True, "skip_download": True, "extract_flat": False, "no_warnings": True,
        "socket_timeout": 8, "retries": 1, "extractor_args": {"youtube": {"skip": ["hls", "dash"]}}
    }
    try:
        time.sleep(random.uniform(0.1, 0.8))
        with yt_dlp.YoutubeDL(ydl_opts_detail) as ydl:
            v_info = ydl.extract_info(vid, download=False)
            
        views = v_info.get("view_count") or e.get("view_count") or 0
        pub_date = None
        if v_info.get("timestamp"): pub_date = datetime.fromtimestamp(v_info.get("timestamp"))
        elif v_info.get("upload_date"): pub_date = extract_date_from_str(v_info.get("upload_date"))

        if not pub_date or pub_date < one_year_ago: return None

        subs = v_info.get("channel_follower_count") or 0
        c_url = v_info.get("channel_url") or v_info.get("uploader_url") or e.get("uploader_url")
        
        real_avg = get_real_channel_avg(c_url, subs, cache_dict, channel)
        
        hours_passed = max((datetime.now() - pub_date).total_seconds() / 3600, 1.0)
        outlier_score = views / real_avg if real_avg > 0 else 1.0
        vph = views / hours_passed
        score = (outlier_score * 50) + (np.log1p(vph) * 10)

        return (vid, title, channel, views, real_avg, outlier_score, vph, score, f"https://www.youtube.com/watch?v={vid}", pub_date.strftime("%Y-%m-%d"))
    except: return None

# ==========================================
# 🚀 爆发指数高亮颜色引擎 (保留)
# ==========================================
def color_outbreak_index(val):
    """根据爆发指数赋予视觉颜色，直击爆款"""
    try:
        num = float(val)
        if num >= 10.0:
            return 'color: #FF4B4B; font-weight: bold; background-color: rgba(255, 75, 75, 0.1);'
        elif num >= 3.0:
            return 'color: #FFA500; font-weight: bold;'
        elif num >= 1.0:
            return 'color: #00FA9A;'
        else:
            return 'color: #808080;'
    except:
        return ''

# ==========================================
# 宽屏大盘高级渲染模块 (保留变色)
# ==========================================
def render_ranking_table(df, empty_msg):
    if df.empty:
        st.info(f"{empty_msg}")
        return
    
    display_df = df.rename(columns={
        'title': '爆款选题', 'channel_name': '账号名称', 'publish_time': '发布日期',
        'views': '播放量', 'channel_avg_views': '频道均播', 'outlier_score': '爆发倍数', 
        'vph': '时效VPH', 'url': '链接'
    }).sort_values("发布日期", ascending=False)
    
    
    cols_to_show = ['爆款选题', '账号名称', '发布日期', '播放量', '频道均播', '爆发倍数', '时效VPH', '链接']
    sliced_df = display_df[cols_to_show]
    
    # 🎨 核心渲染：应用 Pandas 样式
    styled_df = sliced_df.style.map(color_outbreak_index, subset=['爆发倍数'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        column_config={
            "链接": st.column_config.LinkColumn("链接", display_text="观看原片"),
            "爆发倍数": st.column_config.NumberColumn("爆发倍数", format="%.2fx"),
            "频道均播": st.column_config.NumberColumn("频道均播", format="%d"),
            "时效VPH": st.column_config.NumberColumn("时效VPH", format="%.1f")
        }, hide_index=True
    )

# ==========================================
# 🔄 独立提取的核心更新函数 (仅供手动点击)
# ==========================================
def update_target_channels():
    with st.spinner("战术降频防封锁开启 (10线程)！正在精准提取 Median 中位数权重..."):
        c.execute(f"DELETE FROM videos WHERE channel_name IN ({','.join(['?'] * len(TARGET_NAMES))})", TARGET_NAMES)
        conn.commit()

        one_year_ago = datetime.now() - timedelta(days=365)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_target_channel, name, url, one_year_ago) for name, url in TARGET_CHANNELS.items()]
            for future in concurrent.futures.as_completed(futures):
                result_list = future.result()
                if result_list:
                    c.executemany("""INSERT OR REPLACE INTO videos (video_id, title, channel_name, views, channel_avg_views, outlier_score, vph, hot_score, url, publish_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", result_list)
        conn.commit()

# ==========================================
# 中控调节面板
# ==========================================
time_options = {"近1个月": 30, "近3个月": 90, "近6个月": 180, "近1年": 365}
st.write("### 时间过滤器")

time_choice = st.radio("仅显示以下时间段内发布的视频：", list(time_options.keys()), index=0, horizontal=True)
cutoff_date = (datetime.now() - timedelta(days=time_options[time_choice])).strftime("%Y-%m-%d")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 榜单板块 1：油管对标账号选题库
# ==========================================
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.subheader("油管对标账号选题库")
with col_btn:
    if st.button("🔄 更新视频 (耗时较长)", use_container_width=True):
        update_target_channels()
        st.rerun()

# 🚀 网页秒开：直接读取数据库里的旧数据，带上华丽的变色渲染！
query_target = f"SELECT title, channel_name, publish_time, views, channel_avg_views, outlier_score, vph, url FROM videos WHERE channel_name IN ({','.join(['?'] * len(TARGET_NAMES))}) AND publish_time >= '{cutoff_date}' LIMIT 50"
render_ranking_table(pd.read_sql_query(query_target, conn, params=TARGET_NAMES), f"在【{time_choice}】内，对标账号暂无数据。请点击右侧按钮抓取！")

st.markdown("<hr style='margin: 3rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 榜单板块 2：全网搜索视频排行 
# ==========================================
col_table, col_search = st.columns([3, 1])

with col_search:
    st.markdown("### 实时热点搜索")
    st.caption("防风控引擎 | 单次透传真实 Median 均播")
    search_kw = st.text_input("输入检索关键词", "claude code", label_visibility="collapsed")
    search_limit = st.slider("数据扫描深度", 10, 50, 20)
    
    if st.button("开始并发极速扫描", use_container_width=True, type="primary"):
        with st.spinner("防风控 10 线程突围中！深度剥离残存野怪并提取真实播放..."):
            
            c.execute(f"DELETE FROM videos WHERE channel_name NOT IN ({','.join(['?'] * len(TARGET_NAMES))})", TARGET_NAMES)
            conn.commit()

            one_year_ago = datetime.now() - timedelta(days=365)
            all_captured = []
            
            ydl_opts_search = {"quiet": True, "extract_flat": "in_playlist", "skip_download": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
                try:
                    entries = ydl.extract_info(f"ytsearch{search_limit}:{search_kw}", download=False).get("entries", [])
                except: entries = []
            
            if not entries:
                st.error("获取外层搜索失败，可能是节点 IP 被限制，建议更换住宅节点或稍后再试。")
            else:
                channel_cache_dict = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(process_single_search_entry, e, one_year_ago, channel_cache_dict) for e in entries if e]
                    
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            all_captured.append(result)
                
                if all_captured:
                    c.executemany("""INSERT OR REPLACE INTO videos (video_id, title, channel_name, views, channel_avg_views, outlier_score, vph, hot_score, url, publish_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", all_captured)
                    conn.commit()
                    st.rerun()
                else:
                    st.warning(f"扫描完成！未发现有效结果。")

with col_table:
    st.subheader("搜索视频排行")
    query_wild = f"SELECT title, channel_name, publish_time, views, channel_avg_views, outlier_score, vph, url FROM videos WHERE channel_name NOT IN ({','.join(['?'] * len(TARGET_NAMES))}) AND publish_time >= '{cutoff_date}' LIMIT 30"
    render_ranking_table(pd.read_sql_query(query_wild, conn, params=TARGET_NAMES), "散户历史缓存已清空。请在右侧输入关键词启动多线程全网透视。")

conn.close()
