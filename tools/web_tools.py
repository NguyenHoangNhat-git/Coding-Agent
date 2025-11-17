import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults

# Use DuckDuckGo for quick web searches (no API key needed)


@tool("web_search")
def web_search(query: str, max_results: int = 5) -> str:
    """
    Perform a web search using DuckDuckGo and return top results.
    """
    try:
        search = DuckDuckGoSearchResults(max_results=max_results)
        results = search.run(query)
        return results or "No results found."
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
