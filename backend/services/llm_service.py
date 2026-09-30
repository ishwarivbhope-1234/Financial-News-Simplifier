import json
import logging
from typing import Dict, Any, List, Optional
from backend.config import settings

logger = logging.getLogger("finnews.llm_service")

# Prompt template instructing llama-3.3-70b-versatile to act as a financial simplifier
SYSTEM_PROMPT = """You are FinNews AI, an expert financial journalist and educator.
Your task is to take complex financial and economic news articles and explain them in clear, accessible language for ordinary readers, retail investors, and students.

Guidelines:
1. Simplify Jargon: Translate Wall Street and economic terms (e.g., basis points, quantitative tightening, yield curve inversion, hawkish/dovish, capex) into plain English.
2. Maintain Accuracy: Do not alter factual data, numbers, company names, or core market realities.
3. Structure Output: Return your analysis STRICTLY as a valid JSON object matching this schema:
{
  "summary": "2 to 3 concise, jargon-free sentences explaining the core event in simple terms.",
  "key_takeaways": [
    "First main takeaway or impact on everyday investors/consumers",
    "Second key insight regarding markets or future expectations",
    "Third takeaway if applicable (or 2 minimum)"
  ],
  "simplified_terms": {
    "Technical Term 1": "Brief plain-English definition in this context",
    "Technical Term 2": "Brief plain-English definition in this context"
  }
}
Output ONLY the JSON object. Do not enclose in markdown blocks like ```json ... ``` unless necessary, and do not provide introductory or concluding banter.
"""

# Realistic pre-generated simplifications for the curated sample articles
MOCK_SIMPLIFICATIONS: Dict[str, Dict[str, Any]] = {
    "Federal Reserve Holds Benchmark Rate Steady at 5.25%-5.50% Amid Sticky Core Inflation": {
        "summary": "The US Federal Reserve decided not to change interest rates, keeping them at their highest level in over two decades. Central bankers want more proof that prices for everyday goods and services are truly under control before cutting borrowing costs.",
        "key_takeaways": [
            "Borrowing costs for mortgages, car loans, and credit cards will stay elevated for now.",
            "High-yield savings accounts and certificates of deposit (CDs) will continue to pay attractive interest.",
            "Policymakers are being cautious to ensure inflation doesn't rebound before lowering rates."
        ],
        "simplified_terms": {
            "Benchmark Rate": "The interest rate commercial banks charge each other to borrow money overnight, which influences consumer loan rates.",
            "Core Inflation": "The measure of price increases excluding volatile food and energy costs to gauge underlying trends.",
            "Monetary Accommodation": "When a central bank lowers rates to stimulate economic growth and encourage borrowing."
        }
    },
    "Tech Stocks Surge as Semiconductor Giants Rally on Accelerated Enterprise AI Capex": {
        "summary": "Major technology stocks surged higher after chipmakers and cloud companies reported spending massive amounts of money to build out artificial intelligence data centers. Investors see this ongoing corporate spending as proof that AI demand remains robust.",
        "key_takeaways": [
            "Tech-heavy stock indices like the Nasdaq saw significant gains driven by chipmakers.",
            "Big cloud companies are allocating billions to buy specialized computing hardware.",
            "Suppliers of advanced chips and data center components are seeing continued strong profitability."
        ],
        "simplified_terms": {
            "Capex (Capital Expenditure)": "Funds used by a company to acquire, upgrade, and maintain physical assets like servers and factories.",
            "Hyperscaler": "Giant technology companies (like Microsoft, Google, or Amazon) that operate massive global cloud networks.",
            "Gross Margin": "The percentage of revenue a company retains after paying the direct costs of producing its goods."
        }
    },
    "US 10-Year Treasury Yield Inverts Further Against 2-Year Bond as Recession Signals Stir Debate": {
        "summary": "In the government bond market, short-term bonds are paying higher annual interest than long-term bonds. This unusual condition, known as a yield curve inversion, has historically been a warning signal for possible economic slowdowns.",
        "key_takeaways": [
            "Investors are willing to accept lower returns for lock-in safety over ten years than for two years.",
            "While an inverted yield curve historically warned of recessions, the economy currently shows strong job numbers.",
            "Banks face compressed profit margins because they pay more to borrow short-term funds than they earn lending long-term."
        ],
        "simplified_terms": {
            "Treasury Yield": "The annual interest rate the US government pays to investors who buy its debt bonds.",
            "Yield Curve Inversion": "An unusual situation where lending money short-term pays higher interest than lending money long-term.",
            "Basis Points": "A financial unit of measure equal to 1/100th of 1% (e.g., 35 basis points = 0.35%)."
        }
    },
    "Global Oil Benchmarks Climb Above $85 Following OPEC+ Output Quota Extension": {
        "summary": "Global crude oil prices rose past $85 a barrel after major oil-exporting nations decided to continue limiting their oil production. By holding back supply, the group aims to keep prices stable as global demand increases during the summer travel months.",
        "key_takeaways": [
            "Higher crude oil prices often trickle down to higher gasoline prices at the pump for drivers.",
            "Energy company stocks generally benefit from increased profit margins on oil extraction.",
            "Rising fuel costs can put upward pressure on broader inflation by raising transportation costs for goods."
        ],
        "simplified_terms": {
            "OPEC+": "A coalition of 23 oil-producing nations that coordinate oil production levels to influence global prices.",
            "Futures": "Financial contracts where buyers and sellers agree on a set price today for a commodity delivered in the future.",
            "Inventory Overhang": "Having too much stored supply of a commodity, which typically drives prices downward."
        }
    },
    "Consumer Discretionary Spending Cools as Household Excess Savings Deplete": {
        "summary": "Shoppers are becoming more selective and cutting back on non-essential purchases like dining out and electronics. With pandemic-era savings mostly spent and credit card balances high, households are prioritizing essentials like groceries and rent.",
        "key_takeaways": [
            "Retail stores are increasing discounts and store-brand offerings to attract cost-conscious shoppers.",
            "Household debt has reached new highs, putting financial strain on lower-income families.",
            "Companies that sell luxury or non-essential goods may experience slower sales growth."
        ],
        "simplified_terms": {
            "Consumer Discretionary": "Goods and services that people want but do not strictly need to survive (e.g., vacations, entertainment, designer apparel).",
            "Trading-Down": "When consumers switch from premium brands to cheaper private-label or discount alternatives to save money.",
            "Delinquency Rate": "The percentage of loans that have past-due payments by 30 days or more."
        }
    },
    "European Central Bank Hints at June Rate Cut Contingent on Negotiated Wage Growth Data": {
        "summary": "The European Central Bank indicated it might start lowering interest rates in June if wage increases show signs of moderation. European leaders want to encourage business activity as inflation in Europe cools faster than in the United States.",
        "key_takeaways": [
            "European businesses and homeowners may see lower borrowing costs sooner than their American counterparts.",
            "Lower interest rates could stimulate slow economic growth in major European economies like Germany.",
            "A divergent interest rate policy may cause the Euro to weaken slightly against the US Dollar."
        ],
        "simplified_terms": {
            "ECB (European Central Bank)": "The central bank responsible for monetary policy for countries that use the Euro.",
            "Policy Easing": "The process of reducing interest rates to make money cheaper to borrow and stimulate the economy.",
            "Capital Formation": "The net addition to fixed assets, buildings, and technology that businesses invest to grow."
        }
    },
    "Bitcoin Consolidates Around $65,000 as Spot ETF Inflows Offset Post-Halving Miner Selling": {
        "summary": "Bitcoin traded steadily around the $65,000 mark as strong buying through recently approved exchange-traded funds balanced out selling by crypto miners. The recent halving event has cut the daily creation of new bitcoins in half.",
        "key_takeaways": [
            "Spot ETFs have made it easier for traditional retirement accounts and institutions to invest in Bitcoin.",
            "The halving reduced the daily supply of newly created bitcoins from 900 to 450 coins.",
            "Price swings have moderated compared to previous crypto market cycles."
        ],
        "simplified_terms": {
            "Spot ETF": "An investment fund traded on regular stock exchanges that directly holds the underlying asset (in this case, Bitcoin).",
            "Halving": "A scheduled code event occurring every four years that cuts the block reward given to crypto miners in half.",
            "Order Book": "A real-time electronic list of buy and sell orders for a specific security or currency."
        }
    },
    "Dollar Index Retains Strength as Geopolitical Hedging and High Yield Differential Persist": {
        "summary": "The US Dollar remained near its highest levels in months compared to other world currencies. Global investors prefer holding dollars because US government bonds offer higher interest rates than bonds in Japan or Europe, combined with the dollar's perceived safety.",
        "key_takeaways": [
            "A strong dollar makes imported goods cheaper for American consumers and travelers traveling abroad.",
            "US exporters find it harder to sell goods overseas because American products become more expensive in foreign currencies.",
            "Emerging markets with dollar-denominated debt face higher repayment costs."
        ],
        "simplified_terms": {
            "DXY (Dollar Index)": "A benchmark measuring the value of the US Dollar relative to a basket of six major foreign currencies.",
            "Carry Trade": "A financial strategy where investors borrow money in a low-interest-rate currency and invest it in a high-interest-rate currency.",
            "Yield Differential": "The gap in interest rates between bonds issued by two different sovereign governments."
        }
    }
}


class LLMService:
    """Service to simplify financial news using Groq's llama-3.3-70b-versatile model."""

    def __init__(self):
        self.model = settings.GROQ_MODEL
        self._groq_client = None

    def _get_client(self):
        """Lazy initializer for Groq SDK client."""
        if self._groq_client is None and settings.has_groq_key:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"Initialized Groq client with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._groq_client = None
        return self._groq_client

    def simplify_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplify a single financial article using Groq LLM or intelligent fallback.
        Returns a dict with: 'summary', 'key_takeaways', and 'simplified_terms'.
        """
        title = article.get("title", "")
        client = self._get_client()

        # If Groq is not configured, use pre-generated or heuristic fallback
        if not client:
            return self._fallback_simplification(article)

        # Build prompt
        article_text = (
            f"Title: {title}\n"
            f"Source: {article.get('source', 'Unknown')}\n"
            f"Original Snippet: {article.get('description', '')}\n"
            f"Context: {article.get('content', '')[:1000]}"
        )

        try:
            chat_completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Simplify this financial news article for a retail investor and student:\n\n{article_text}"
                    }
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            raw_response = chat_completion.choices[0].message.content.strip()
            parsed = json.loads(raw_response)

            summary = parsed.get("summary") or "Financial summary currently being analyzed."
            key_takeaways = parsed.get("key_takeaways") or []
            simplified_terms = parsed.get("simplified_terms") or {}

            return {
                "summary": summary,
                "key_takeaways": key_takeaways,
                "simplified_terms": simplified_terms
            }

        except Exception as e:
            logger.warning(f"Groq API call failed ({e}); switching to fallback simplification.")
            return self._fallback_simplification(article)

    def _fallback_simplification(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Provide realistic, high-quality simplification without active Groq API keys."""
        title = article.get("title", "")

        # Check exact or partial match in curated store
        for stored_title, data in MOCK_SIMPLIFICATIONS.items():
            if stored_title.lower() in title.lower() or title.lower() in stored_title.lower():
                return data

        # Generic heuristic simplification if not in mock dictionary
        desc = article.get("description") or article.get("content") or "Latest financial development."
        cleaned_desc = desc.split(". ")[0] + "."

        return {
            "summary": f"This financial report explains recent market developments regarding {title}. In simple terms, {cleaned_desc}",
            "key_takeaways": [
                f"Market movement: Investors are actively evaluating the consequences of {article.get('source', 'this announcement')}.",
                "Consumer impact: Changes in borrowing rates, inflation, or asset values may influence household budgets.",
                "Outlook: Analysts recommend monitoring official reports and earnings over the upcoming quarter."
            ],
            "simplified_terms": {
                "Market Volatility": "The rate at which the price of an asset increases or decreases over a short time period.",
                "Liquidity": "How quickly and easily an asset can be bought or sold without causing a drastic price change."
            }
        }

llm_service = LLMService()
