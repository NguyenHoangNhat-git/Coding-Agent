import requests, os
from bs4 import BeautifulSoup
from langchain.tools import tool
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


@tool("web_search")
def web_search(query: str, max_results: int = 5) -> str:
    """
    Google-like search using Serper.dev API.
    """
    try:
        url = "https://google.serper.dev/search"
        payload = {"q": query, "num": max_results}
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        results = []
        for item in data.get("organic", []):
            results.append(f"- {item.get('title')} — {item.get('link')}")

        return "\n".join(results) or "No results found."
    except Exception as e:
        return f"Search failed: {e}"


@tool("fetch_website_text")
def fetch_website_text(url: str, max_chars: int = 4000) -> str:
    """
    Fetch and clean readable text content from a webpage.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts, styles, etc.
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        clean_text = " ".join(text.split())

        return clean_text[:max_chars] or "(Empty or unreadable content)"
    except Exception as e:
        return f"Failed to fetch page: {e}"
