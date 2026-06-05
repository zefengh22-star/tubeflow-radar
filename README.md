# YouTube 爆款发现雷达 V1.6

一个简单的 Python 命令行工具，用于发现 YouTube 在指定时间范围内可能正在爆发的视频。

本项目使用 `yt-dlp` 抓取公开网页数据，使用 `pandas` 导出 CSV：

- 不使用收费 API
- 不使用 YouTube Data API
- Python 3.13 兼容

## 安装

建议先创建虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 运行

```bash
python radar.py
```

程序启动后先选择时间范围：

```text
1 = 最近1个月
2 = 最近3个月
3 = 最近6个月
```

然后输入关键词，一行一个，输入空行后开始分析。

## 示例输入

```text
请选择分析时间范围：
1 = 最近1个月
2 = 最近3个月
3 = 最近6个月
请输入选项（1/2/3）：1

请输入关键词，一行一个。输入空行后开始分析：
> VPN
> Residential Proxy
> TikTok Shop
> AI Automation
>
```

## 示例输出

```text
开始处理关键词：VPN
关键词：VPN
搜索结果数：500
时间过滤后数量：137
Top20数量：20
最终导出数量：20

已导出：results.csv
总导出数量：80
```

实际数量会受到 YouTube 返回结果、视频发布时间、地区网络环境和 yt-dlp 可获取字段影响。

## CSV 字段

导出的 `results.csv` 使用 `utf-8-sig` 编码，方便 Excel 正确显示中文。

字段顺序：

```text
keyword
title
channel
subscribers
views
hours_since_publish
vph
average_channel_vph
viral_score
viral_level
upload_date
url
```

## 计算规则

### 时间过滤

程序只使用 `upload_date` 字段过滤发布时间，格式为 `YYYYMMDD`：

- 最近1个月：当前时间减 30 天
- 最近3个月：当前时间减 90 天
- 最近6个月：当前时间减 180 天

每个关键词最多保留 200 条符合时间范围的视频。如果不足 200 条，则全部保留。

### VPH

```text
vph = views / hours_since_publish
```

如果发布时间不足 1 小时，按 1 小时计算，避免除零。

### 频道平均 VPH

程序会对每个关键词先按当前视频 `vph` 排序，只保留 Top20 进入频道分析阶段。

对 Top20 中的每条视频：

1. 获取该频道最近 20 条视频。
2. 排除当前正在分析的视频。
3. 对剩余视频计算平均 VPH，得到 `average_channel_vph`。

同一个频道当天只请求一次，程序会缓存：

- `subscribers`
- `recent_videos`

### Viral Score

```text
viral_score = current_vph / average_channel_vph
```

如果 `average_channel_vph` 为 0 或无法计算：

```text
viral_score = 0
```

### Viral Level

```text
viral_score < 2              = Normal
viral_score >= 2 and < 5     = Good
viral_score >= 5 and < 10    = Hot
viral_score >= 10            = Viral
```

最终导出前会再次排序：

```text
viral_score DESC
vph DESC
```

## 字段稳定性说明

如果 yt-dlp 某些字段无法稳定获取，程序会优先保证：

1. `upload_date`
2. `views`
3. `channel`
4. `url`

其次再获取 `subscribers`。如果订阅数无法获取，CSV 中该单元格保持空白，不写 `0` 或 `Unknown`。

## 后续版本暂不包含

- 频道白名单模式
- topic_group 选题聚类
- Gemini 自动洗稿
- Streamlit 网页版
