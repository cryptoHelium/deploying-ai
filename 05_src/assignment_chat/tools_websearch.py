# Service 3: Simple Web search using DuckDuckGo HTML to do a web search.
# POST the search query to DuckDuckGo's web server
# Parse the returned HTML to extract titles, snippets, and URLs
# Return the top 5 results as a formatted markdown string
# There are additional libraries that make this much easier and faster. this does not use the DDG library


import urllib.request
import urllib.parse
from html.parser import HTMLParser
from langchain_core.tools import tool


class _DDGParser(HTMLParser):
    """
    Goes through the DuckDuckGo HTML results page and pulls out the useful bits.

    DuckDuckGo wraps each result in a <div class="result ..."> block.
    Inside each block:
      - The title is in <a class="result__a">
      - The snippet is in <a class="result__snippet">
      - The real URL is embedded as a query param in the title link's href
    """

    def __init__(self):
        super().__init__()
        self.results = []    # completed results go here
        self._current = None # the result currently being built
        self._capture = None # which field we are collecting text into ("title" or "snippet")

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        css  = attr.get("class", "")

        # A new result block starts — skip ads (class contains "result--ad")
        if tag == "div" and "result" in css and "result--ad" not in css:
            self._current = {"title": "", "snippet": "", "url": ""}

        if self._current is None:
            return

        # Title link — start capturing title text and extract the real URL
        if tag == "a" and "result__a" in css:
            self._capture = "title"
            # DDG wraps the real URL in a redirect href like /?uddg=https%3A%2F%2F...
            # Parse it out of the query string
            raw = attr.get("href", "")
            qs  = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
            self._current["url"] = qs.get("uddg", [raw])[0]

        # Snippet link — start capturing snippet text
        if tag == "a" and "result__snippet" in css:
            self._capture = "snippet"

    def handle_endtag(self, tag):
        # Stop capturing text when any tag closes
        self._capture = None

        # When a result div closes, save it if it has a title
        if tag == "div" and self._current and self._current["title"]:
            self.results.append(self._current)
            self._current = None

    def handle_data(self, data):
        # Append text to whichever field we are currently capturing
        if self._current and self._capture and data.strip():
            self._current[self._capture] += data.strip()


@tool
def handle_web_search(query: str) -> str:
    """
    Pre-Condition
    Search the web using DuckDuckGo. Use this for general knowledge questions,
    current events, definitions, or anything not covered by the NHL or BBC news services.
    Duck Duck Go Search is free. No api key or anything needed
    
    Post-Condition The data will be parsed out and used by the model.

    """
    # Encode the query as form data for a POST request
    # kl=us-en sets the region/language to US English
    data    = urllib.parse.urlencode({"q": query, "kl": "us-en"}).encode()
    request = urllib.request.Request(
        "https://html.duckduckgo.com/html/",  # plain HTML endpoint, no JavaScript needed
        data=data,
        headers={"User-Agent": "Mozilla/5.0"},  # browser-like header so DDG doesn't block us
        method="POST",
    )

    # Fetch the page and decode the HTML
    with urllib.request.urlopen(request, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Parse the HTML and extract results
    parser = _DDGParser()
    parser.feed(html)

    # Format the top 5 results as markdown
    lines = [f"Web Search Results for: *\"{query}\"*\n"]
    for i, r in enumerate(parser.results[:5], 1):
        lines.append(f"**{i}. {r['title']}**")
        if r["snippet"]:
            lines.append(r["snippet"][:350])  # trim long snippets
        if r["url"]:
            lines.append(f" {r['url']}")
        lines.append("")  # blank line between results

    return "\n".join(lines)