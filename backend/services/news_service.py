import logging
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone
from backend.config import settings

logger = logging.getLogger("finnews.news_service")

# Curated high-fidelity financial news articles representing realistic market conditions
MOCK_FINANCIAL_ARTICLES: List[Dict[str, Any]] = [
    {
        "title": "Federal Reserve Holds Benchmark Rate Steady at 5.25%-5.50% Amid Sticky Core Inflation",
        "source": "Financial Times",
        "author": "Colby Smith",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.ft.com/central-banks",
        "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80",
        "category": "Economy",
        "description": "The Federal Open Market Committee voted unanimously to maintain the federal funds target range as policymakers await further evidence that core PCE inflation is sustainably decelerating toward the 2% statutory objective.",
        "content": "Federal Reserve Chairman Jerome Powell emphasized that while disinflation has occurred across durable goods, sticky services inflation and robust nonfarm payroll growth warrant keeping policy in restrictive territory before considering monetary accommodation."
    },
    {
        "title": "Tech Stocks Surge as Semiconductor Giants Rally on Accelerated Enterprise AI Capex",
        "source": "Bloomberg Markets",
        "author": "Jeran Wittenstein",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.bloomberg.com/markets",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
        "category": "Tech Stocks",
        "description": "The Nasdaq 100 gained 1.8% led by hyperscaler hardware vendors, as cloud providers announced elevated capital expenditures for custom silicon and generative AI data center infrastructure.",
        "content": "Investor appetite expanded following quarterly guidance indicating continued double-digit growth in cloud infrastructure spending. Gross margins remained resilient despite supply-chain lead times on advanced wafer packaging technologies."
    },
    {
        "title": "US 10-Year Treasury Yield Inverts Further Against 2-Year Bond as Recession Signals Stir Debate",
        "source": "The Wall Street Journal",
        "author": "Matt Phillips",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.wsj.com/economy",
        "image_url": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
        "category": "Markets",
        "description": "The sovereign bond yield curve experienced continued inversion as short-duration rates reflected hawkish central bank guidance while long-duration yields priced in moderating future economic momentum.",
        "content": "Historically considered a reliable harbinger of macroeconomic contraction, the 2s/10s spread oscillated around negative 35 basis points. Economists remain divided on whether this cycle represents a soft landing or a lagged contractionary shock."
    },
    {
        "title": "Global Oil Benchmarks Climb Above $85 Following OPEC+ Output Quota Extension",
        "source": "Reuters Energy",
        "author": "Alex Lawler",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.reuters.com/business/energy",
        "image_url": "https://images.unsplash.com/photo-1518623489648-a173ef7824f3?auto=format&fit=crop&w=800&q=80",
        "category": "Commodities",
        "description": "Brent crude and WTI futures advanced over 2% after member nations agreed to roll over voluntary production cuts of 2.2 million barrels per day through the upcoming quarter to preempt inventory overhangs.",
        "content": "Crude supplies are anticipated to tighten as seasonal summer refinery runs coincide with constrained maritime throughput across key transit chokepoints, posing marginal upside risk to headline consumer price index readings."
    },
    {
        "title": "Consumer Discretionary Spending Cools as Household Excess Savings Deplete",
        "source": "CNBC Business",
        "author": "Jeff Cox",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.cnbc.com/economy",
        "image_url": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=800&q=80",
        "category": "Economy",
        "description": "Retail sales data showed sequential deceleration as lower-income deciles cut back on non-essential expenditures amidst elevated revolving credit card debt and resumption of student loan obligations.",
        "content": "Major department stores and big-box retailers noted increased promotional activity and consumer trading-down to private-label brands. Delinquency rates on subprime auto loans reached their highest levels since 2010."
    },
    {
        "title": "European Central Bank Hints at June Rate Cut Contingent on Negotiated Wage Growth Data",
        "source": "MarketWatch",
        "author": "Pierre Briançon",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.marketwatch.com/economy-politics",
        "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80",
        "category": "Global Finance",
        "description": "ECB Governing Council members signaled divergence from the Federal Reserve, suggesting softening Eurozone manufacturing indicators may justify early policy easing if labor cost pressures subside.",
        "content": "With headline inflation converging toward 2.4% across the bloc, policymakers in Frankfurt stressed that monetary policy must not remain overly restrictive for too long lest it asphyxiate sluggish private capital formation."
    },
    {
        "title": "Bitcoin Consolidates Around $65,000 as Spot ETF Inflows Offset Post-Halving Miner Selling",
        "source": "CoinDesk",
        "author": "Helene Braun",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.coindesk.com/markets",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
        "category": "Crypto",
        "description": "Digital asset markets demonstrated reduced volatility with net inflows into institutional spot exchange-traded products countering hash-rate capitulation from proof-of-work mining consortiums.",
        "content": "Market makers observed tight bid-ask spreads across institutional order books. Analysts note that reduced daily block subsidy emissions are structurally limiting liquid spot supply over medium-term horizons."
    },
    {
        "title": "Dollar Index Retains Strength as Geopolitical Hedging and High Yield Differential Persist",
        "source": "Bloomberg Currency",
        "author": "Alice Atkins",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "url": "https://www.bloomberg.com/currencies",
        "image_url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=800&q=80",
        "category": "Currencies",
        "description": "The greenback (DXY) traded near multi-month highs against the Yen and Euro as foreign exchange carry trades continued to favor high-yielding US short-term paper over low-rate sovereign counterparts.",
        "content": "Intervention threats by Asian central banks have so far achieved only temporary reprieves against dollar strength, with the substantial interest rate differential between the Fed and Bank of Japan continuing to drive capital flows."
    }
]


class NewsService:
    """Service to retrieve real-time financial news from NewsAPI or fallback sources."""

    def __init__(self):
        self.api_key = settings.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"

    def fetch_articles(self, count: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch `count` articles from NewsAPI. If API key is missing, invalid, or exhausted,
        gracefully returns curated real-world financial articles.
        """
        # Clamp count to 1-10
        count = max(1, min(10, count))

        if not settings.has_news_api_key:
            logger.info("NewsAPI key not configured; using curated financial articles (demo mode).")
            return self._get_fallback_articles(count, category)

        try:
            # Query NewsAPI for financial/business news
            params = {
                "category": "business",
                "country": "us",
                "pageSize": min(20, count * 2),  # Fetch extra to filter out removed/empty articles
                "apiKey": self.api_key
            }
            query_string = urllib.parse.urlencode(params)
            req_url = f"{self.base_url}/top-headlines?{query_string}"

            req = urllib.request.Request(
                req_url,
                headers={"User-Agent": "FinNewsAI/1.0", "Accept": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning(f"NewsAPI returned status {resp.status}, falling back.")
                    return self._get_fallback_articles(count, category)

                data = json.loads(resp.read().decode("utf-8"))

            if data.get("status") != "ok":
                logger.warning(f"NewsAPI error: {data.get('message')}. Using fallback.")
                return self._get_fallback_articles(count, category)

            raw_articles = data.get("articles", [])
            valid_articles: List[Dict[str, Any]] = []

            for art in raw_articles:
                title = (art.get("title") or "").strip()
                description = (art.get("description") or "").strip()
                content = (art.get("content") or "").strip()

                # Filter out removed or junk articles
                if not title or "[Removed]" in title or len(title) < 10:
                    continue
                if not description and not content:
                    continue

                source_name = "Financial Source"
                if isinstance(art.get("source"), dict):
                    source_name = art["source"].get("name") or source_name

                valid_articles.append({
                    "title": title,
                    "source": source_name,
                    "author": art.get("author") or "Market Analyst",
                    "published_at": art.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                    "url": art.get("url") or "#",
                    "image_url": art.get("urlToImage") or "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80",
                    "category": category or "Finance",
                    "description": description or content[:200],
                    "content": content or description
                })

                if len(valid_articles) >= count:
                    break

            if len(valid_articles) < count:
                # Top up with fallback articles if NewsAPI returned too few valid ones
                fallback = self._get_fallback_articles(count, category)
                for f_art in fallback:
                    if len(valid_articles) >= count:
                        break
                    if not any(v["title"] == f_art["title"] for v in valid_articles):
                        valid_articles.append(f_art)

            return valid_articles[:count]

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}. Falling back to curated data.")
            return self._get_fallback_articles(count, category)

    def _get_fallback_articles(self, count: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return curated sample articles filtered by category if specified."""
        articles = MOCK_FINANCIAL_ARTICLES
        if category and category.lower() not in ["all", "all finance", ""]:
            cat_lower = category.lower()
            filtered = [a for a in articles if cat_lower in a.get("category", "").lower()]
            if filtered:
                articles = filtered
        return articles[:count]

news_service = NewsService()
