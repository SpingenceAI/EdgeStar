import requests
from typing import List

from loguru import logger
from pydantic import BaseModel, Field


class SearchEngineConfig(BaseModel):
    """Search engine config"""

    provider: str = "searxng"
    base_url: str = "http://localhost:8080"


class SearchResult(BaseModel):
    """Search result"""

    search_query: str = Field(description="The search query")
    url: str = Field(description="The url of the search result")
    title: str = Field(description="The title of the search result")
    content: str = Field(description="Part of the content of the search result")


class Params(BaseModel):
    """Search params"""

    time_range: str = Field(
        description="The time range of the search query, e.g. month, year, week, day",
        default="month",
    )
    limit: int = Field(description="The number of search results to return", default=3)
    locale: str = Field(
        description="The locale of the search query, e.g. zh-TW", default="zh-TW"
    )
    categories: str = Field(
        description="The categories of the search query, e.g. general, images",
        default="general",
    )


class SearchEngineBase:

    def __init__(self, config: SearchEngineConfig):
        self.config = config

    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Search for general results"""
        params = Params(**kwargs)
        return self._search(self.config.base_url, query, params)

    def _search(self, base_url: str, query: str, params: Params) -> List[SearchResult]:
        """Search for general results"""
        raise NotImplementedError("Subclass must implement this method")


class SearchEngineSearxng(SearchEngineBase):
    def _search(self, base_url: str, query: str, params: Params) -> List[SearchResult]:
        """Search"""
        url = f"{base_url}/search"

        time_range = (
            params.time_range
            if params.time_range in ["month", "year", "week", "day"]
            else "month"
        )

        request_params = {
            "q": query,
            "format": "json",
            "language": params.locale,
            "time_range": time_range,
            "categories": params.categories,
        }
        response = requests.get(url, params=request_params)
        response_json = response.json()
        results = []
        try:
            for x in response_json["results"][: params.limit]:
                results.append(SearchResult(**{"search_query": query, **x}))
        except Exception as e:
            logger.error(f"Error in search: {e}")
        return results


def search_engine_factory(config: SearchEngineConfig):
    """Search engine factory"""
    if config.provider == "searxng":
        return SearchEngineSearxng(config)
    else:
        raise ValueError(f"Search engine {config.provider} not found")

if __name__ == "__main__":
    search_engine = SearchEngineSearxng(SearchEngineConfig())
    search_results = search_engine.search(
        "今年中華隊經典賽選手名單",
        time_range="month",
        limit=3,
        locale="zh-TW",
        categories="general",
    )
    print(search_results)
