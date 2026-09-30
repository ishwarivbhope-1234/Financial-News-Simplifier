import os
import logging
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models import (
    SimplifiedArticle,
    NewsResponse,
    HealthResponse,
    ErrorResponse,
)
from backend.services.news_service import news_service
from backend.services.llm_service import llm_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("finnews.api")

# FastAPI application initialization
app = FastAPI(
    title="FinNews AI – Financial News Simplifier",
    description=(
        "An AI-powered web API that fetches real-time financial news articles "
        "and generates simplified summaries, key takeaways, and jargon definitions "
        "using Groq's Llama 3.3 70B model."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable Cross-Origin Resource Sharing (CORS) for seamless frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend directories (checked across root, public, and frontend)
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
PUBLIC_DIR = BASE_DIR / "public"

# Mount static asset routes
if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
elif (PUBLIC_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(PUBLIC_DIR / "css")), name="css")

if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
elif (PUBLIC_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(PUBLIC_DIR / "js")), name="js")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
elif PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


@app.get("/", summary="Root endpoint - Web App Interface or API Info", response_class=FileResponse)
def root():
    """
    Serves the modern frontend application interface if index.html exists,
    otherwise returns API metadata.
    """
    for candidate in [
        PUBLIC_DIR / "index.html",
        FRONTEND_DIR / "index.html",
        BASE_DIR / "index.html"
    ]:
        if candidate.exists():
            return FileResponse(str(candidate))

    return JSONResponse({
        "app": "FinNews AI – Financial News Simplifier",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "news": "/news?count=5",
            "documentation": "/docs"
        },
        "status": "online"
    })


@app.get("/api", summary="API Metadata and Documentation Links")
def api_info():
    """Returns basic API info, version, and documentation links."""
    return {
        "app": "FinNews AI – Financial News Simplifier",
        "version": "1.0.0",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "news": "/news?count={1-10}",
            "swagger_docs": "/docs",
            "redoc": "/redoc"
        },
        "groq_model": settings.GROQ_MODEL,
        "mode": "live" if settings.has_groq_key else "demo"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check and API Key Verification",
    tags=["System"]
)
@app.get(
    "/api/health",
    response_model=HealthResponse,
    include_in_schema=False
)
def health_check():
    """
    Health monitoring endpoint.
    Verifies that the service is operational and reports whether Groq and NewsAPI
    keys are configured.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        app_name="FinNews AI – Financial News Simplifier",
        groq_configured=settings.has_groq_key,
        newsapi_configured=settings.has_news_api_key,
        model=settings.GROQ_MODEL,
        environment=settings.ENVIRONMENT
    )


@app.get(
    "/news",
    response_model=NewsResponse,
    responses={400: {"model": ErrorResponse}, 422: {"description": "Validation Error"}},
    summary="Fetch & Simplify Financial News",
    tags=["News Simplification"]
)
@app.get(
    "/api/news",
    response_model=NewsResponse,
    responses={400: {"model": ErrorResponse}, 422: {"description": "Validation Error"}},
    include_in_schema=False
)
def get_simplified_news(
    count: int = Query(
        default=5,
        ge=1,
        le=10,
        description="Number of financial news articles to retrieve and simplify (1 to 10)"
    ),
    category: Optional[str] = Query(
        default=None,
        description="Topic filter: Markets, Economy, Tech Stocks, Commodities, Crypto, Currencies"
    )
):
    """
    Retrieves the latest financial news articles and uses Groq Llama 3.3 70B
    to generate jargon-free summaries, actionable bullet points, and terminology definitions.
    """
    try:
        logger.info(f"Processing news request: count={count}, category={category}")

        # 1. Fetch raw articles via news service
        raw_articles = news_service.fetch_articles(count=count, category=category)

        if not raw_articles:
            return NewsResponse(
                success=True,
                count=0,
                mode="live" if settings.has_groq_key else "demo",
                model=settings.GROQ_MODEL,
                articles=[]
            )

        # 2. Process articles through Groq LLM simplification engine
        simplified_articles: List[SimplifiedArticle] = []

        for item in raw_articles:
            simplification = llm_service.simplify_article(item)

            article_obj = SimplifiedArticle(
                title=item.get("title", "Untitled"),
                source=item.get("source", "Financial News"),
                author=item.get("author"),
                published_at=item.get("published_at"),
                url=item.get("url"),
                image_url=item.get("image_url"),
                category=item.get("category", "Markets"),
                original_description=item.get("description"),
                summary=simplification.get("summary", ""),
                key_takeaways=simplification.get("key_takeaways", []),
                simplified_terms=simplification.get("simplified_terms", {})
            )
            simplified_articles.append(article_obj)

        mode_str = "live" if (settings.has_groq_key and settings.has_news_api_key) else (
            "hybrid" if (settings.has_groq_key or settings.has_news_api_key) else "demo"
        )

        return NewsResponse(
            success=True,
            count=len(simplified_articles),
            mode=mode_str,
            model=settings.GROQ_MODEL,
            articles=simplified_articles
        )

    except Exception as e:
        logger.exception(f"Unhandled error in /news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching and simplifying financial news: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
