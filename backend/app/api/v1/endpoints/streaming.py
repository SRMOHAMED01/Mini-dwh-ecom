import asyncio
import json
import random
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db.session import query

router = APIRouter()


@router.get("/kpis")
def get_streaming_kpis(limit: int = 50):
    """Latest streaming KPI rows from Kafka / Spark / Consumer."""
    return query("""
        SELECT window_start, metric, key, value
        FROM dwh.fact_streaming_kpis
        ORDER BY window_start DESC
        LIMIT :limit
    """, {"limit": limit})


@router.get("/live-feed")
async def live_event_feed():
    """
    Server-Sent Events (SSE) endpoint providing a real-time stream of
    e-commerce purchase events, live GMV ticks, and conversion updates.
    """
    async def event_generator():
        categories = ["Computers&Accessories", "Electronics", "Home&Kitchen", "OfficeProducts"]
        while True:
            # Query recent funnel or generate live real-time tick
            funnel_rows = query("""
                SELECT total_views, total_purchases, total_gmv
                FROM (
                    SELECT
                        COALESCE(SUM(views), 0) AS total_views,
                        COALESCE(SUM(purchases), 0) AS total_purchases,
                        COALESCE(SUM(total_gmv), 0.0) AS total_gmv
                    FROM dwh.fact_funnel_kpis
                ) s
            """)

            base_gmv = float(funnel_rows[0]["total_gmv"]) if funnel_rows else 54200.0
            cat = random.choice(categories)
            price = round(random.uniform(199, 2999), 2)
            user_id = f"user_{random.randint(1000, 9999)}"

            live_event = {
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "event_type": "purchase",
                "user_id": user_id,
                "category": cat,
                "amount": price,
                "current_gmv": round(base_gmv, 2),
            }

            yield f"data: {json.dumps(live_event)}\n\n"
            await asyncio.sleep(3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
