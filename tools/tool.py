from langchain.tools import tool
from collections.abc import Mapping
import requests
from dotenv import load_dotenv
import os
from langchain_tavily import TavilySearch
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re

load_dotenv()

search_tool = TavilySearch(  # intialize the TavilySearch tool
    max_results=5
)


@tool
def web_search(query: str) -> str:
    """Search the web for a query and return the results."""
    response = search_tool.invoke({"query": query})
    if not isinstance(response, Mapping):
        return f"Search returned an unexpected response: {response}"
    if response.get("error"):
        return f"Search failed: {response['error']}"

    results = response.get("results", [])
    if not isinstance(results, list):
        return "Search returned no usable results."

    out = []
    for result in results:
        if not isinstance(result, Mapping):
            continue
        title = str(result.get("title", "Untitled source"))
        url = str(result.get("url", ""))
        content = str(result.get("content", ""))
        out.append(
            f"Title: {title}\nURL: {url}\nSnippet: {content[:300]}\n"
        )

    return "\n".join(out) or "Search returned no usable results."


@tool
def scrape_webpage(url: str) -> str:
    """Scrape the main content of a webpage and return it as text."""

    try:
        # Download the webpage
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        # Check if the request was successful
        response.raise_for_status()

        # Get the HTML
        html_content = response.text

        # Extract the main content using Readability
        doc = Document(html_content)
        main_content = doc.summary()

        # Convert the main HTML content into plain text
        soup = BeautifulSoup(main_content, "html.parser")

        text = soup.get_text(
            separator="\n",
            strip=True
        )

        # Return the text
        return text if text else "No content found."

    except Exception as e:
        return f"Error scraping the webpage: {e}"
