"""
Trend fetcher: pulls viral robotics content from YouTube and TikTok Research API.
YouTube: free, works immediately.
TikTok: requires Research API approval — scaffolded and ready once you have credentials.
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Optional


class YouTubeTrendFetcher:
    """Fetch trending robotics content from YouTube Data API v3."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_trending(
        self,
        keywords: list[str],
        days_back: int = 30,
        max_per_keyword: int = 10,
    ) -> list[dict]:
        published_after = (datetime.now() - timedelta(days=days_back)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        all_videos: list[dict] = []

        for keyword in keywords:
            video_ids = self._search(keyword, published_after, max_per_keyword)
            if not video_ids:
                continue
            videos = self._get_stats(video_ids, keyword)
            all_videos.extend(videos)
            time.sleep(0.2)  # be gentle with the quota

        return self._deduplicate(all_videos)

    def _search(self, keyword: str, published_after: str, max_results: int) -> list[str]:
        resp = requests.get(
            f"{self.BASE_URL}/search",
            params={
                "part": "snippet",
                "q": keyword,
                "order": "viewCount",
                "type": "video",
                "publishedAfter": published_after,
                "maxResults": max_results,
                "key": self.api_key,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"  [YouTube] Search failed for '{keyword}': {resp.status_code}")
            return []
        return [item["id"]["videoId"] for item in resp.json().get("items", [])]

    def _get_stats(self, video_ids: list[str], keyword: str) -> list[dict]:
        resp = requests.get(
            f"{self.BASE_URL}/videos",
            params={
                "part": "statistics,snippet,contentDetails",
                "id": ",".join(video_ids),
                "key": self.api_key,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []

        results = []
        for item in resp.json().get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            results.append({
                "platform": "youtube",
                "id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:400],
                "channel": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": item.get("contentDetails", {}).get("duration", ""),
                "search_keyword": keyword,
                "url": f"https://youtube.com/watch?v={item['id']}",
            })
        return results

    def _deduplicate(self, videos: list[dict]) -> list[dict]:
        seen: set[str] = set()
        unique = []
        for v in sorted(videos, key=lambda x: x["view_count"], reverse=True):
            if v["id"] not in seen:
                seen.add(v["id"])
                unique.append(v)
        return unique


class TikTokTrendFetcher:
    """
    Fetch trending robotics content via TikTok Research API.

    Requires: TikTok Developer account + Research API access.
    Apply at: https://developers.tiktok.com/products/research-api/
    Once approved you get CLIENT_KEY + CLIENT_SECRET.
    """

    AUTH_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"

    def __init__(self, client_key: str, client_secret: str):
        self.client_key = client_key
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        resp = requests.post(
            self.AUTH_URL,
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]
        return self._access_token

    def fetch_trending(
        self,
        keywords: list[str],
        hashtags: list[str],
        days_back: int = 30,
        max_results: int = 50,
    ) -> list[dict]:
        token = self._get_access_token()
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        # Build OR query across keywords + hashtags
        keyword_conditions = [
            {"field": "keyword", "operation": "IN", "field_values": keywords[:5]}
        ]
        hashtag_conditions = [
            {"field": "hashtag_name", "operation": "IN", "field_values": [h.lstrip("#") for h in hashtags[:5]]}
        ]

        body = {
            "query": {
                "or": keyword_conditions + hashtag_conditions
            },
            "start_date": start_date,
            "end_date": end_date,
            "max_count": max_results,
            "fields": "id,title,video_description,create_time,region_code,view_count,like_count,comment_count,share_count,hashtag_names,username",
            "sort_type": "POPULAR",
        }

        resp = requests.post(
            self.QUERY_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if resp.status_code != 200:
            print(f"  [TikTok] Query failed: {resp.status_code} — {resp.text[:200]}")
            return []

        videos = resp.json().get("data", {}).get("videos", [])
        return [
            {
                "platform": "tiktok",
                "id": str(v.get("id", "")),
                "title": v.get("title", "") or v.get("video_description", "")[:100],
                "description": v.get("video_description", "")[:400],
                "channel": v.get("username", ""),
                "published_at": datetime.fromtimestamp(v.get("create_time", 0)).isoformat(),
                "view_count": v.get("view_count", 0),
                "like_count": v.get("like_count", 0),
                "comment_count": v.get("comment_count", 0),
                "share_count": v.get("share_count", 0),
                "hashtags": v.get("hashtag_names", []),
                "url": f"https://tiktok.com/@{v.get('username', '')}",
            }
            for v in videos
        ]


class TrendFetcher:
    """Orchestrates both fetchers and returns merged, ranked trend data."""

    def __init__(self):
        self.youtube = self._init_youtube()
        self.tiktok = self._init_tiktok()

    def _init_youtube(self) -> Optional[YouTubeTrendFetcher]:
        key = os.getenv("YOUTUBE_API_KEY")
        if not key:
            print("  [!] YOUTUBE_API_KEY not set — skipping YouTube")
            return None
        return YouTubeTrendFetcher(key)

    def _init_tiktok(self) -> Optional[TikTokTrendFetcher]:
        client_key = os.getenv("TIKTOK_CLIENT_KEY")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        if not client_key or not client_secret:
            print("  [!] TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET not set — skipping TikTok")
            return None
        return TikTokTrendFetcher(client_key, client_secret)

    def fetch_all(self, days_back: int = 30) -> list[dict]:
        """Fetch from all available platforms and return merged results."""
        with open("config/keywords.json") as f:
            kw = json.load(f)

        all_trends: list[dict] = []

        if self.youtube:
            print("  Fetching YouTube trends...")
            keywords = kw["primary"] + kw["technical"][:5]
            yt_trends = self.youtube.fetch_trending(keywords, days_back=days_back)
            print(f"  Found {len(yt_trends)} YouTube videos")
            all_trends.extend(yt_trends)

        if self.tiktok:
            print("  Fetching TikTok trends...")
            tt_trends = self.tiktok.fetch_trending(
                keywords=kw["primary"],
                hashtags=kw["trending_hashtags"]["tiktok"],
                days_back=days_back,
            )
            print(f"  Found {len(tt_trends)} TikTok videos")
            all_trends.extend(tt_trends)

        if not all_trends:
            print("  No trends fetched — check your API keys")
            return []

        # Save raw data
        os.makedirs("data", exist_ok=True)
        outpath = f"data/trends_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(outpath, "w") as f:
            json.dump(all_trends, f, indent=2)
        print(f"  Saved {len(all_trends)} trends → {outpath}")

        return all_trends
