import requests
import os


def web_search(query: str) -> str:
    """
    Search the internet for the given query
    """
    data = {
        "api_key": os.getenv("TAVILY_API_KEY"),
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "include_images": False,
        "include_image_descriptions": False,
        "include_raw_content": False,
        "max_results": 5,
        "include_domains": [],
        "exclude_domains": [],
    }
    response = requests.post("https://api.tavily.com/search", json=data)
    response.raise_for_status()
    answer = response.json()["answer"]
    results = response.json()["results"]
    return f"answer: {answer}\n references: {results}"

tools_map = {
    "web_search": web_search,
}

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(".env.playground.tom")
    print(web_search("What is the weather in Tokyo?"))
