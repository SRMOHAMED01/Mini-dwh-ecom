# etl/api.py
import os
from fastapi import FastAPI
#Pour autoriser React à appeler ton API.
from fastapi.middleware.cors import CORSMiddleware
#crée la connexion vers PostgreSQL text → permet d’écrire du SQL brut proprement
from sqlalchemy import create_engine, text

#connection a la base de données Si elle n’existe pas → on utilise "postgres".
DB_HOST = os.getenv("DB_HOST", "postgres")
#C’est l’URL de connexion PostgreSQL.
DB_URL  = f"postgresql://dwh_user:dwh_pass@{DB_HOST}:5432/ecommerce_dwh"
#On crée le moteur de connexion SQLAlchemy. 👉 C’est lui qui permet d’envoyer du SQL à PostgreSQL.
engine = create_engine(DB_URL)
app    = FastAPI(title="Amazon DWH API")

# ✅ Allow React (port 3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def query(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        #On récupère les noms des colonnes.
        cols = result.keys()
        #On transforme les résultats en liste de dicts (une ligne = un dict)
        #FastAPI convertit ensuite automatiquement en JSON.
        return [dict(zip(cols, row)) for row in result.fetchall()]


@app.get("/api/top-categories")
def top_categories():
    return query("""
        SELECT
            category,
            COUNT(*)                                AS product_count,
            ROUND(AVG(rating)::numeric, 2)          AS avg_rating,
            ROUND(AVG(discount_pct)::numeric, 1)    AS avg_discount_pct
        FROM dwh.dim_product
        WHERE category IS NOT NULL AND category <> ''
        GROUP BY category
        ORDER BY product_count DESC
        LIMIT 10
    """)


@app.get("/api/kpi-summary")
def kpi_summary():
    return query("""
        SELECT
            COUNT(*)                                    AS total_products,
            ROUND(AVG(rating)::numeric, 2)              AS avg_rating,
            ROUND(AVG(discount_pct)::numeric, 1)        AS avg_discount_pct,
            (SELECT COUNT(*) FROM dwh.fact_reviews)     AS total_reviews
        FROM dwh.dim_product
    """)[0]


@app.get("/api/top-rated-products")
def top_rated_products():
    return query("""
        SELECT
            product_id,
            LEFT(product_name, 60)  AS product_name,
            rating,
            rating_count,
            ROUND(discount_pct, 1)  AS discount_pct
        FROM dwh.dim_product
        WHERE rating_count >= 500
        ORDER BY rating DESC, rating_count DESC
        LIMIT 10
    """)


@app.get("/api/most-reviewed")
def most_reviewed():
    return query("""
        SELECT
            p.product_id,
            LEFT(p.product_name, 60) AS product_name,
            COUNT(r.review_id)        AS review_count,
            p.rating
        FROM dwh.dim_product p
        JOIN dwh.fact_reviews r ON p.product_id = r.product_id
        GROUP BY p.product_id, p.product_name, p.rating
        ORDER BY review_count DESC
        LIMIT 10
    """)


@app.get("/api/discount-distribution")
def discount_distribution():
    return query("""
        SELECT
            CASE
                WHEN discount_pct < 20  THEN '0-19%'
                WHEN discount_pct < 40  THEN '20-39%'
                WHEN discount_pct < 60  THEN '40-59%'
                WHEN discount_pct < 80  THEN '60-79%'
                ELSE '80-100%'
            END AS bucket,
            COUNT(*) AS product_count
        FROM dwh.dim_product
        WHERE discount_pct IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket
    """)