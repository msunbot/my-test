"""
Configuration: news sources, keywords, and Claude model settings.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Source:
    name: str
    url: str
    lang: str  # "zh" or "en"
    category: str = "general"


# ── Chinese sources ──────────────────────────────────────────────────────────
CHINESE_SOURCES: list[Source] = [
    # General tech / startup
    Source("36Kr",         "https://36kr.com/feed",                         "zh"),
    Source("Huxiu",        "https://www.huxiu.com/rss/0.xml",               "zh"),
    Source("TMTPost",      "https://www.tmtpost.com/feed",                  "zh"),
    # AI / robotics focused
    Source("Jiqizhixin",   "https://www.jiqizhixin.com/rss",                "zh", "robotics"),
    Source("Leiphone",     "https://www.leiphone.com/feed",                 "zh", "ai"),
    # Business news with tech coverage
    Source("Jiemian",      "https://www.jiemian.com/rss.html",              "zh"),
    Source("ThePaper",     "https://www.thepaper.cn/rss_cn.jsp",            "zh"),
    Source("Caixin",       "https://www.caixin.com/rss/caixinglobal.xml",   "zh"),
]

# ── English sources ───────────────────────────────────────────────────────────
ENGLISH_SOURCES: list[Source] = [
    Source("Reuters Tech",       "https://feeds.reuters.com/reuters/technologyNews",          "en"),
    Source("SCMP Tech",          "https://www.scmp.com/rss/5/feed",                           "en", "china"),
    Source("Nikkei Asia",        "https://asia.nikkei.com/rss/feed/nar",                      "en", "asia"),
    Source("TechCrunch",         "https://techcrunch.com/feed/",                              "en"),
    Source("IEEE Spectrum",      "https://spectrum.ieee.org/feeds/topic/robotics.rss",        "en", "robotics"),
    Source("The Robot Report",   "https://www.therobotreport.com/feed/",                      "en", "robotics"),
    Source("Wired",              "https://www.wired.com/feed/rss",                            "en"),
    Source("Rest of World",      "https://restofworld.org/feed/",                             "en", "china"),
]

ALL_SOURCES = CHINESE_SOURCES + ENGLISH_SOURCES

# ── Relevance keywords ────────────────────────────────────────────────────────
KEYWORDS = {
    "robotics": [
        # English
        "robot", "robotic", "robotics", "humanoid", "automation", "actuator",
        "servo", "end-effector", "manipulator", "autonomous", "cobot",
        "Boston Dynamics", "Figure AI", "Agility Robotics", "1X", "Apptronik",
        "Unitree", "UBTECH", "Fourier Intelligence", "Leju", "Agibot",
        # Chinese
        "机器人", "人形机器人", "工业机器人", "协作机器人", "自动化",
        "宇树", "优必选", "傅利叶", "乐聚", "智元", "追觅", "小米机器人",
        "具身智能",
    ],
    "supply_chain": [
        # English
        "supply chain", "semiconductor", "chip", "manufacturing", "factory",
        "reshoring", "nearshoring", "decoupling", "tariff", "export control",
        "TSMC", "SMIC", "Huawei", "NVIDIA", "fab",
        # Chinese
        "供应链", "半导体", "芯片", "制造", "工厂", "产业链",
        "台积电", "中芯国际", "华为", "英伟达", "脱钩", "关税",
    ],
}

ALL_KEYWORDS = [kw.lower() for kws in KEYWORDS.values() for kw in kws]

# ── Claude models ─────────────────────────────────────────────────────────────
HAIKU_MODEL  = "claude-haiku-4-5"    # fast triage
OPUS_MODEL   = "claude-opus-4-7"     # deep analysis + content generation

# ── Scheduling ────────────────────────────────────────────────────────────────
FETCH_INTERVAL_HOURS = 6     # how often to run
MAX_ARTICLES_PER_RUN = 30    # cap articles processed per run

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "digests"
DB_PATH    = "seen_articles.db"
