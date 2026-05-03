"""
This is the 3rd service.
Free web search via DuckDuckGo (no API key required).

tools_websearch.py

Googled this:  Uses the `duckduckgo-search` library which wraps the DDG API.

duckduckgo-search (DDGS): Currently the most popular and actively maintained library. It provides a DDGS class to 
fetch text, images, videos, and news.

ddgs (Dux Distributed Global Search): A newer metasearch library that aggregates results from multiple services 
and uses a distributed cache network to reduce rate limits.

When using the modern DDGS library, you can access several search types:text(): Returns standard web search results including snippets 
and URLs.images(): Retrieves image search results.news(): Scrapes the latest news articles for specific keywords.translate(): Provides 
translation services directly through the search engine.answers(): Returns "Instant Answers" (definitions or facts) for direct queries.
"""
from langchain.tools import tool
import re
from typing import Optional
from duckduckgo_search import DDGS


# Limit the results of duck duck go

MAX_RESULTS = 5
SNIPPET_MAX = 350


# Helpers

def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:SNIPPET_MAX] + ("…" if len(text) > SNIPPET_MAX else "")


# Public API

@tool
def handle_web_search(query: str, num_results: int = MAX_RESULTS) -> str:
    """
    Search the web with DuckDuckGo and return formatted markdown results.

    Args:
        query:       The user's search question.
        num_results: How many results to return (default 5).

    Returns:
        A formatted markdown string with titles, snippets, and URLs.
    """
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=num_results))
    except Exception as e:
        return f"Web search failed: {e}\n\nTry rephrasing your query."

    if not raw:
        return f"No web results found for: *\"{query}\"*"

    lines = [f"** Using Duck Duck Go, Web Search Results** for: *\"{query}\"*\n"]
    for i, result in enumerate(raw, 1):
        title = _clean(result.get("title", "No title"))
        body = _clean(result.get("body", ""))
        url = result.get("href", "")

        lines.append(f"**{i}. {title}**")
        if body:
            lines.append(f"{body}")
        if url:
            lines.append(f"[{url}]({url})")
        lines.append("")

    return "\n".join(lines)


#def handle_web_search_with_summary(query: str, llm_client=None, num_results: int = MAX_RESULTS) -> str:
#    
#    Enhanced version: fetches DDG results, then optionally uses the LLM to
#    synthesize a summary from the snippets (pass llm_client from main.py).
#
#    If llm client is None, falls back to plain handle_web_search().
#    
 #   raw_results = handle_web_search(query, num_results)
#
#    if llm_client is None:#
#        return raw_results

    # Ask the LLM to synthesize an answer from the snippets
#    try:
#        from prompts import return_instructions
#        synthesis_prompt = (
#            f"User question: \"{query}\"\n\n"
#            f"Search results:\n{raw_results}\n\n"
#            f"Synthesize the key information in 2-3 sentences, then list the sources."
#        )
#        response = llm_client.chat.completions.create(
 #           model="gpt-4o-mini",
  #          messages=[
   #             {"role": "system", "content": return_instructions()},
    #            {"role": "user", "content": synthesis_prompt},
     #       ],
      #      max_tokens=400,
       #     temperature=0.3,
        #)
#        summary = response.choices[0].message.content.strip()
#        return f"Web Search — AI Summary**\n\n{summary}\n\n---\n\n{raw_results}"
#    except Exception as e:
#        print(f"[websearch] LLM synthesis failed, returning raw results: {e}")
#        return raw_results
#"""