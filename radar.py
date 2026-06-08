from __future__ import annotations

import os
import time
import random
import base64
import requests
from dataclasses import dataclass
from datetime import UTC, datetime, time as dt_time, timedelta
from typing import Any

import pandas as pd
import yt_dlp


SEARCH_LIMIT = 500
MAX_VIDEOS_PER_KEYWORD = 200
TOP_VIDEOS_PER_KEYWORD = 20
# 【修改点1】云端运行降频：将频道历史视频提取量降为5，减少API请求压力，防封号
CHANNEL_RECENT_VIDEO_LIMIT = 5 
OUTPUT_FILE = "results.csv"

CSV_COLUMNS = [
    "keyword",
    "title",
    "channel",
    "subscribers",
    "views",
    "hours_since_publish",
    "vph",
    "average_channel_vph",
    "viral_score",
    "viral_level",
    "upload_date",
    "url",
]

# 【修改点2】加强防风控伪装：加入超时时间和真实浏览器 User-Agent
YDL_OPTIONS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "skip_download": True,
    "socket_timeout": 60,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
}


@dataclass
class ChannelData:
    cache_date: str
    subscribers: int | None
    recent_videos: list[dict[str, Any]]


channel_cache: dict[str, ChannelData] = {}


def choose_time_range() -> tuple[int, datetime]:
    choices = {
        "1": (30, "最近1个月"),
        "2": (90, "最近3个月"),
        "3": (180, "最近6个月"),
    }

    print("请选择分析时间范围：")
    print("1 = 最近1个月")
    print("2 = 最近3个月")
    print("3 = 最近6个月")

    while True:
        choice = input("请输入选项（1/2/3）：").strip()
        if choice in choices:
            days, label = choices[choice]
            cutoff = datetime.now(UTC) - timedelta(days=days)
            print(f"已选择：{label}（从 {cutoff.date().isoformat()} 开始）")
            return days, cutoff
        print("输入无效，请输入 1、2 或 3。")


def read_keywords() -> list[str]:
    print("\n请输入关键词，一行一个。输入空行后开始分析：")
    keywords: list[str] = []
    while True:
        keyword = input("> ").strip()
        if not keyword:
            break
        keywords.append(keyword)
    return keywords


def parse_upload_date(value: Any) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()
    if len(text) != 8 or not text.isdigit():
        return None

    try:
        parsed_date = datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None

    return datetime.combine(parsed_date, dt_time.min, tzinfo=UTC)


def hours_since_publish(uploaded_at: datetime, now: datetime) -> float:
    hours = (now - uploaded_at).total_seconds() / 3600
    return max(hours, 1.0)


def make_video_url(info: dict[str, Any]) -> str | None:
    for key in ("webpage_url", "original_url", "url"):
        value = info.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value

    video_id = info.get("id")
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    return None


def get_channel_key(info: dict[str, Any]) -> str | None:
    for key in ("channel_id", "uploader_id", "channel_url", "uploader_url", "channel", "uploader"):
        value = info.get(key)
        if value:
            return str(value)
    return None


def get_channel_url(info: dict[str, Any]) -> str | None:
    for key in ("channel_url", "uploader_url"):
        value = info.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value.rstrip("/")
    return None


def get_channel_name(info: dict[str, Any]) -> str:
    for key in ("channel", "uploader", "creator"):
        value = info.get(key)
        if value:
            return str(value)
    return ""


def get_subscribers(info: dict[str, Any]) -> int | None:
    for key in ("channel_follower_count", "uploader_follower_count", "subscriber_count"):
        value = info.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    return None


def safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def extract_entries(url: str, ydl_options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    options = dict(YDL_OPTIONS)
    if ydl_options:
        options.update(ydl_options)

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        return []

    entries = info.get("entries")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]

    if isinstance(info, dict):
        return [info]

    return []


def search_keyword(keyword: str) -> list[dict[str, Any]]:
    search_url = f"ytsearch{SEARCH_LIMIT}:{keyword}"
    return extract_entries(search_url)


def normalize_video(keyword: str, info: dict[str, Any], now: datetime) -> dict[str, Any] | None:
    uploaded_at = parse_upload_date(info.get("upload_date"))
    title = info.get("title")
    url = make_video_url(info)

    if not uploaded_at or not title or not url:
        return None

    views = safe_int(info.get("view_count"), 0)
    hours = hours_since_publish(uploaded_at, now)
    vph = views / hours if hours > 0 else 0.0

    return {
        "keyword": keyword,
        "title": str(title),
        "channel": get_channel_name(info),
        "subscribers": get_subscribers(info),
        "views": views,
        "hours_since_publish": round(hours, 2),
        "vph": round(vph, 2),
        "average_channel_vph": 0.0,
        "viral_score": 0.0,
        "viral_level": "Normal",
        "upload_date": uploaded_at.date().isoformat(),
        "url": url,
        "_video_id": info.get("id"),
        "_channel_key": get_channel_key(info),
        "_channel_url": get_channel_url(info),
        "_raw_info": info,
    }


def get_channel_recent_videos(channel_url: str) -> list[dict[str, Any]]:
    videos_url = channel_url.rstrip("/") + "/videos"
    return extract_entries(
        videos_url,
        {
            "playlistend": CHANNEL_RECENT_VIDEO_LIMIT,
        },
    )[:CHANNEL_RECENT_VIDEO_LIMIT]


def get_channel_data(video: dict[str, Any]) -> ChannelData:
    today = datetime.now(UTC).date().isoformat()
    channel_key = video.get("_channel_key") or video.get("channel") or video.get("_channel_url")

    if channel_key and channel_key in channel_cache:
        cached = channel_cache[channel_key]
        if cached.cache_date == today:
            return cached

    subscribers = video.get("subscribers")
    recent_videos: list[dict[str, Any]] = []
    channel_url = video.get("_channel_url")

    if channel_url:
        try:
            # 【修改点3】强制随机休眠3到6秒，防止频道连续请求被拦截
            sleep_time = random.uniform(3, 6)
            print(f"  [防风控] 正在休眠 {sleep_time:.1f} 秒，准备抓取频道：{video.get('channel', '')}")
            time.sleep(sleep_time)
            
            recent_videos = get_channel_recent_videos(str(channel_url))
            for recent in recent_videos:
                if subscribers is None:
                    subscribers = get_subscribers(recent)
        except Exception as exc:
            print(f"  频道历史视频抓取失败：{video.get('channel', '')}，原因：{exc}")

    data = ChannelData(
        cache_date=today,
        subscribers=subscribers if isinstance(subscribers, int) else None,
        recent_videos=recent_videos,
    )

    if channel_key:
        channel_cache[str(channel_key)] = data

    return data


def calculate_average_channel_vph(
    current_video: dict[str, Any], recent_videos: list[dict[str, Any]], now: datetime
) -> float:
    current_id = current_video.get("_video_id")
    current_url = current_video.get("url")
    values: list[float] = []

    for item in recent_videos:
        item_id = item.get("id")
        item_url = make_video_url(item)

        if current_id and item_id and str(current_id) == str(item_id):
            continue
        if current_url and item_url and current_url == item_url:
            continue

        uploaded_at = parse_upload_date(item.get("upload_date"))
        if not uploaded_at:
            continue

        views = safe_int(item.get("view_count"), 0)
        hours = hours_since_publish(uploaded_at, now)
        values.append(views / hours if hours > 0 else 0.0)

    if not values:
        return 0.0

    return sum(values) / len(values)


def viral_level(score: float) -> str:
    if score >= 10:
        return "Viral"
    if score >= 5:
        return "Hot"
    if score >= 2:
        return "Good"
    return "Normal"


def enrich_with_channel_analysis(videos: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []

    for video in videos:
        try:
            channel_data = get_channel_data(video)
            avg_vph = calculate_average_channel_vph(video, channel_data.recent_videos, now)
            current_vph = float(video.get("vph") or 0)
            score = current_vph / avg_vph if avg_vph > 0 else 0.0

            video["subscribers"] = channel_data.subscribers
            video["average_channel_vph"] = round(avg_vph, 2)
            video["viral_score"] = round(score, 2)
            video["viral_level"] = viral_level(score)
        except Exception as exc:
            print(f"  视频频道分析失败：{video.get('title', '')}，原因：{exc}")
            video["average_channel_vph"] = 0.0
            video["viral_score"] = 0.0
            video["viral_level"] = "Normal"

        enriched.append(video)

    return enriched


def process_keyword(keyword: str, cutoff: datetime, now: datetime) -> list[dict[str, Any]]:
    print(f"\n开始处理关键词：{keyword}")

    try:
        entries = search_keyword(keyword)
    except Exception as exc:
        print(f"关键词搜索失败：{keyword}，原因：{exc}")
        print(f"关键词：{keyword}")
        print("搜索结果数：0")
        print("时间过滤后数量：0")
        print("Top20数量：0")
        print("最终导出数量：0")
        return []

    normalized: list[dict[str, Any]] = []
    for entry in entries:
        video = normalize_video(keyword, entry, now)
        if not video:
            continue

        uploaded_at = datetime.fromisoformat(str(video["upload_date"])).replace(tzinfo=UTC)
        if uploaded_at >= cutoff:
            normalized.append(video)

        if len(normalized) >= MAX_VIDEOS_PER_KEYWORD:
            break

    normalized.sort(key=lambda item: float(item.get("vph") or 0), reverse=True)
    top_videos = normalized[:TOP_VIDEOS_PER_KEYWORD]
    enriched = enrich_with_channel_analysis(top_videos, now)

    print(f"关键词：{keyword}")
    print(f"搜索结果数：{len(entries)}")
    print(f"时间过滤后数量：{len(normalized)}")
    print(f"Top20数量：{len(top_videos)}")
    print(f"最终导出数量：{len(enriched)}")

    return enriched


def clean_for_csv(rows: list[dict[str, Any]]) -> pd.DataFrame:
    clean_rows = []
    for row in rows:
        clean_rows.append({column: row.get(column) for column in CSV_COLUMNS})

    df = pd.DataFrame(clean_rows, columns=CSV_COLUMNS)
    if df.empty:
        return df

    df["viral_score"] = pd.to_numeric(df["viral_score"], errors="coerce").fillna(0)
    df["vph"] = pd.to_numeric(df["vph"], errors="coerce").fillna(0)
    df = df.sort_values(by=["viral_score", "vph"], ascending=[False, False])
    df["subscribers"] = df["subscribers"].where(pd.notna(df["subscribers"]), None)
    return df


def export_results(rows: list[dict[str, Any]]) -> None:
    df = clean_for_csv(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n已导出：{OUTPUT_FILE}")
    print(f"总导出数量：{len(df)}")


# 【修改点4】新增 GitHub 自动同步函数
def save_to_github(filename: str = OUTPUT_FILE) -> None:
    token = os.environ.get("GIT_TOKEN")
    if not token:
        print("\n⚠️ 未配置 GIT_TOKEN 环境变量，已跳过 GitHub 云端同步。")
        return

    repo = "zefengh22-star/管流雷达" 
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. 尝试获取原文件的 SHA（更新文件必须提供原文件的 SHA）
    get_resp = requests.get(url, headers=headers)
    sha = None
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")

    # 2. 读取并编码刚生成的 CSV 文件
    try:
        with open(filename, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"\n❌ 找不到文件 {filename}，同步失败。")
        return

    # 3. 构造请求载荷并推送到 GitHub
    data = {
        "message": f"Auto-sync {filename} via HuggingFace Radar",
        "content": content,
        "branch": "main" 
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    
    if put_resp.status_code in [200, 201]:
        print(f"\n✅ 太棒了！{filename} 已成功备份至 GitHub 仓库 ({repo})，数据永久安全！")
    else:
        print(f"\n❌ GitHub 同步失败: 状态码 {put_resp.status_code}")
        print(put_resp.text)


def main() -> None:
    print("YouTube 爆款发现雷达 V1.6 (云端防风控特化版)")
    _, cutoff = choose_time_range()
    keywords = read_keywords()

    if not keywords:
        print("未输入关键词，将生成空的 results.csv。")
        export_results([])
        save_to_github(OUTPUT_FILE) # 即使为空，也覆盖一下云端
        return

    now = datetime.now(UTC)
    all_rows: list[dict[str, Any]] = []

    for keyword in keywords:
        all_rows.extend(process_keyword(keyword, cutoff, now))

    export_results(all_rows)
    
    # 【修改点5】执行数据导出后，自动触发 GitHub 同传
    save_to_github(OUTPUT_FILE)


if __name__ == "__main__":
    main()