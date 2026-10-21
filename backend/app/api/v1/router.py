from fastapi import APIRouter
from app.api.v1.endpoints import kpis, sentiment, funnel, streaming

api_router = APIRouter()

# Core KPIs & Business Analytics
api_router.include_router(kpis.router, tags=["KPIs & Analytics"])

# NLP Sentiment & Review Intelligence
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["NLP Sentiment"])

# Real-Time Conversion Funnel
api_router.include_router(funnel.router, prefix="/funnel", tags=["Conversion Funnel"])

# Streaming & Live Events
api_router.include_router(streaming.router, prefix="/streaming", tags=["Real-Time Streaming"])
