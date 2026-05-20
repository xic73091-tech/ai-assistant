"""联网搜索模块"""

from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx

from .i18n import i18n


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: list[SearchResult] = field(default_factory=list)
    provider: str = ""
    error: Optional[str] = None


class SearchProvider:
    """搜索提供商基类"""

    name: str = "base"

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        raise NotImplementedError


class DuckDuckGoSearch(SearchProvider):
    """DuckDuckGo搜索"""

    name = "duckduckgo"

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """使用DuckDuckGo HTML搜索"""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                results = self._parse_html(resp.text, max_results)
                return SearchResponse(
                    query=query,
                    results=results,
                    provider=self.name,
                )
            except Exception as e:
                return SearchResponse(
                    query=query,
                    provider=self.name,
                    error=str(e),
                )

    def _parse_html(self, html: str, max_results: int) -> list[SearchResult]:
        """解析DuckDuckGo HTML搜索结果"""
        results = []
        # 简单的HTML解析，不依赖BeautifulSoup
        import re

        # 匹配搜索结果块
        # DuckDuckGo HTML结果格式: <a class="result__a" href="...">title</a>
        # <a class="result__snippet" ...>snippet</a>
        blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        )

        for url, title, snippet in blocks[:max_results]:
            # 清理HTML标签
            title = re.sub(r"<[^>]+>", "", title).strip()
            snippet = re.sub(r"<[^>]+>", "", snippet).strip()
            # 解码HTML实体
            title = self._decode_entities(title)
            snippet = self._decode_entities(snippet)
            # DuckDuckGo的URL可能需要解码
            if "uddg=" in url:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                url = parsed.get("uddg", [url])[0]

            if title and snippet:
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="DuckDuckGo",
                ))

        return results

    @staticmethod
    def _decode_entities(text: str) -> str:
        """解码HTML实体"""
        import html
        return html.unescape(text)


class BingSearch(SearchProvider):
    """Bing搜索（需要API Key）"""

    name = "bing"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """使用Bing搜索API"""
        if not self.api_key:
            return SearchResponse(
                query=query,
                provider=self.name,
                error="Bing API key not configured",
            )

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": max_results, "mkt": "zh-CN"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = []

                for item in data.get("webPages", {}).get("value", [])[:max_results]:
                    results.append(SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source="Bing",
                    ))

                return SearchResponse(
                    query=query,
                    results=results,
                    provider=self.name,
                )
            except Exception as e:
                return SearchResponse(
                    query=query,
                    provider=self.name,
                    error=str(e),
                )


class WebSearcher:
    """联网搜索管理器"""

    def __init__(self, bing_api_key: str = ""):
        self._providers: dict[str, SearchProvider] = {
            "duckduckgo": DuckDuckGoSearch(),
            "bing": BingSearch(bing_api_key),
        }
        self._default_provider = "duckduckgo"

    @property
    def default_provider(self) -> str:
        return self._default_provider

    @default_provider.setter
    def default_provider(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Unknown search provider: {name}")
        self._default_provider = name

    async def search(
        self,
        query: str,
        max_results: int = 5,
        provider: Optional[str] = None,
    ) -> SearchResponse:
        """执行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数
            provider: 搜索引擎名称

        Returns:
            搜索响应
        """
        provider_name = provider or self._default_provider
        search_provider = self._providers.get(provider_name)
        if not search_provider:
            return SearchResponse(
                query=query,
                provider=provider_name,
                error=f"Unknown provider: {provider_name}",
            )
        return await search_provider.search(query, max_results)

    def format_results(self, response: SearchResponse) -> str:
        """格式化搜索结果为文本，可注入AI上下文"""
        if response.error:
            return i18n.t("search_error", error=response.error)

        if not response.results:
            return i18n.t("search_no_results")

        lines = [f"## {i18n.t('search_results')}: {response.query}\n"]
        for i, r in enumerate(response.results, 1):
            lines.append(f"**{i}. {r.title}**")
            lines.append(f"   {r.snippet}")
            lines.append(f"   [{i18n.t('search_source')}]({r.url})\n")

        return "\n".join(lines)

    def get_context_prompt(self, response: SearchResponse) -> str:
        """生成可注入对话上下文的搜索结果提示"""
        if response.error or not response.results:
            return ""

        parts = [f"以下是关于「{response.query}」的实时搜索结果，请参考这些信息回答用户问题：\n"]
        for i, r in enumerate(response.results, 1):
            parts.append(f"{i}. {r.title}: {r.snippet} (来源: {r.url})")

        return "\n".join(parts)


# 全局实例
web_searcher = WebSearcher()
