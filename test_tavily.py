from dotenv import load_dotenv

load_dotenv()

from langchain_community.tools.tavily_search import TavilySearchResults

tool = TavilySearchResults(max_results=3)

result = tool.invoke(
    "Latest amendments to Information Technology Act India"
)

print(result)