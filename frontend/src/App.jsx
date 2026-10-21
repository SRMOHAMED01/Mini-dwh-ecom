import { useEffect, useState } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from "recharts"
import axios from "axios"
import "./App.css"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"
const API = `${API_BASE}/api/v1`

const COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981",
  "#3b82f6", "#ef4444", "#14b8a6", "#f97316", "#84cc16"
]

const SENTIMENT_COLORS = {
  POSITIVE: "#10b981",
  NEUTRAL: "#94a3b8",
  NEGATIVE: "#ef4444"
}

export default function App() {
  const [theme, setTheme] = useState("light")
  const [activeTab, setActiveTab] = useState("overview")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Data States
  const [summary, setSummary] = useState(null)
  const [categories, setCategories] = useState([])
  const [topRated, setTopRated] = useState([])
  const [mostReviewed, setMostReviewed] = useState([])
  const [discountDist, setDiscountDist] = useState([])
  const [sentimentOverview, setSentimentOverview] = useState(null)
  const [divergentProducts, setDivergentProducts] = useState([])
  const [funnel, setFunnel] = useState(null)
  const [liveEvents, setLiveEvents] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(null)

  // Theme Toggle
  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light"
    setTheme(nextTheme)
    document.documentElement.setAttribute("data-theme", nextTheme)
  }

  // Initial Data Fetching
  useEffect(() => {
    setLoading(true)
    setError(null)

    Promise.allSettled([
      axios.get(`${API}/kpi-summary`),
      axios.get(`${API}/top-categories`),
      axios.get(`${API}/top-rated-products`),
      axios.get(`${API}/most-reviewed`),
      axios.get(`${API}/discount-distribution`),
      axios.get(`${API}/sentiment/overview`),
      axios.get(`${API}/sentiment/divergent-products`),
      axios.get(`${API}/funnel/latest`),
    ])
      .then(([sumRes, catRes, topRes, mostRes, distRes, sentRes, divRes, funRes]) => {
        if (sumRes.status === "fulfilled") setSummary(sumRes.value.data)
        if (catRes.status === "fulfilled") setCategories(catRes.value.data)
        if (topRes.status === "fulfilled") setTopRated(topRes.value.data)
        if (mostRes.status === "fulfilled") setMostReviewed(mostRes.value.data)
        if (distRes.status === "fulfilled") setDiscountDist(distRes.value.data)
        if (sentRes.status === "fulfilled") setSentimentOverview(sentRes.value.data)
        if (divRes.status === "fulfilled") setDivergentProducts(divRes.value.data)
        if (funRes.status === "fulfilled") setFunnel(funRes.value.data)
      })
      .catch((err) => {
        console.error("API error:", err)
        setError("Could not connect to the backend API. Ensure containers are running.")
      })
      .finally(() => setLoading(false))
  }, [])

  // Live SSE Connection for Real-Time Event Feed
  useEffect(() => {
    let eventSource
    try {
      eventSource = new EventSource(`${API}/streaming/live-feed`)
      eventSource.onmessage = (event) => {
        try {
          const data = jsonParseSafe(event.data)
          if (data) {
            setLiveEvents((prev) => [data, ...prev.slice(0, 19)])
            // Incrementally update funnel GMV if purchase
            if (data.event_type === "purchase" && data.amount) {
              setFunnel((prev) => prev ? {
                ...prev,
                total_gmv: Number(prev.total_gmv) + Number(data.amount),
                total_purchases: Number(prev.total_purchases) + 1
              } : prev)
            }
          }
        } catch (e) {
          console.error("Error parsing SSE frame", e)
        }
      }
    } catch (err) {
      console.warn("SSE connection error", err)
    }

    return () => {
      if (eventSource) eventSource.close()
    }
  }, [])

  // Product Inspection Handler
  const openProductModal = (productId) => {
    axios.get(`${API}/sentiment/product/${productId}`)
      .then((res) => setSelectedProduct(res.data))
      .catch((err) => console.error("Error fetching product details", err))
  }

  return (
    <div className="cockpit-container">
      {/* Cockpit Top Bar */}
      <header className="cockpit-header">
        <div>
          <h1 className="cockpit-title">🛒 E-Commerce Decision Intelligence</h1>
          <p className="cockpit-subtitle">
            Hybrid Lakehouse • NLP Review Sentiment • Real-Time Conversion Funnel
          </p>
        </div>
        <button className="theme-toggle-btn" onClick={toggleTheme}>
          {theme === "light" ? "🌙 Dark Mode" : "☀️ Light Mode"}
        </button>
      </header>

      {/* Error Alert */}
      {error && (
        <div style={{ background: "#fee2e2", color: "#b91c1c", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          ⚠️ <strong>Connection Notice:</strong> {error}
        </div>
      )}

      {/* Tabs Navigation */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📊 Executive Overview
        </button>
        <button
          className={`tab-btn ${activeTab === "sentiment" ? "active" : ""}`}
          onClick={() => setActiveTab("sentiment")}
        >
          🧠 NLP Review Sentiment
        </button>
        <button
          className={`tab-btn ${activeTab === "funnel" ? "active" : ""}`}
          onClick={() => setActiveTab("funnel")}
        >
          🎯 Conversion Funnel & Pricing
        </button>
        <button
          className={`tab-btn ${activeTab === "streaming" ? "active" : ""}`}
          onClick={() => setActiveTab("streaming")}
        >
          📡 Live Event Stream ({liveEvents.length})
        </button>
      </nav>

      {/* TAB 1: EXECUTIVE OVERVIEW */}
      {activeTab === "overview" && (
        <div>
          {/* KPI Summary Cards */}
          <div className="kpi-grid">
            <KPICard
              label="Catalog Products"
              value={summary?.total_products || "..."}
              color="#6366f1"
            />
            <KPICard
              label="Avg Product Rating"
              value={`⭐ ${summary?.avg_rating || "..."}`}
              color="#f59e0b"
            />
            <KPICard
              label="Avg Discount"
              value={`${summary?.avg_discount_pct || 0}%`}
              color="#10b981"
            />
            <KPICard
              label="Total Reviews Analyzed"
              value={summary?.total_reviews ? Number(summary.total_reviews).toLocaleString() : "..."}
              color="#ec4899"
            />
            <KPICard
              label="Live GMV (Revenue)"
              value={`₹${funnel?.total_gmv ? Number(funnel.total_gmv).toLocaleString() : "..."}`}
              color="#3b82f6"
            />
            <KPICard
              label="Overall Conversion"
              value={`${funnel?.overall_conversion_rate || 0}%`}
              color="#8b5cf6"
            />
          </div>

          {/* Top Categories */}
          <div className="section-box">
            <h2 className="section-title">📦 Top Categories by Product Count</h2>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={categories} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="category" type="category" width={180} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, n) => [v, n === "product_count" ? "Products" : n]} />
                <Bar dataKey="product_count" radius={[0, 4, 4, 0]}>
                  {categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(450px, 1fr))", gap: "1.5rem" }}>
            {/* Most Reviewed Products */}
            <div className="section-box">
              <h2 className="section-title">🔥 Most Reviewed Products</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mostReviewed} margin={{ bottom: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="product_name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" interval={0} />
                  <YAxis />
                  <Tooltip formatter={(v) => [v, "Reviews"]} />
                  <Bar dataKey="review_count" radius={[4, 4, 0, 0]}>
                    {mostReviewed.map((_, i) => <Cell key={i} fill={COLORS[(i + 3) % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Discount Distribution */}
            <div className="section-box">
              <h2 className="section-title">💸 Discount Tiers Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={discountDist}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bucket" />
                  <YAxis />
                  <Tooltip formatter={(v) => [v, "Products"]} />
                  <Bar dataKey="product_count" radius={[4, 4, 0, 0]}>
                    {discountDist.map((_, i) => <Cell key={i} fill={COLORS[(i + 5) % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: NLP REVIEW SENTIMENT */}
      {activeTab === "sentiment" && (
        <div>
          {/* Sentiment KPI Grid */}
          <div className="kpi-grid">
            <KPICard
              label="Positive Sentiment"
              value={`${sentimentOverview?.positive_pct || 0}%`}
              color="#10b981"
            />
            <KPICard
              label="Neutral Sentiment"
              value={`${sentimentOverview?.neutral_pct || 0}%`}
              color="#94a3b8"
            />
            <KPICard
              label="Negative Sentiment"
              value={`${sentimentOverview?.negative_pct || 0}%`}
              color="#ef4444"
            />
            <KPICard
              label="Divergence Alarms"
              value={sentimentOverview?.divergent_count || 0}
              color="#f59e0b"
            />
            <KPICard
              label="Net Polarity Score"
              value={sentimentOverview?.avg_sentiment_score || "+0.00"}
              color="#6366f1"
            />
          </div>

          {/* Divergent Products Alarm Table */}
          <div className="section-box">
            <h2 className="section-title">🚨 Review Divergence Alarm (High Rating vs Negative Content)</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "-0.5rem", marginBottom: "1rem" }}>
              These products have high star ratings (≥ 4.0★) but contain customer reviews with strongly negative sentiment. This highlights potential fake reviews or quality issues.
            </p>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product ID</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Rating</th>
                    <th>Suspicious Reviews</th>
                    <th>Avg Sentiment</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {divergentProducts.map((p) => (
                    <tr key={p.product_id}>
                      <td><code>{p.product_id}</code></td>
                      <td>{p.product_name}</td>
                      <td>{p.category}</td>
                      <td>⭐ {p.rating}</td>
                      <td><span className="badge badge-alarm">{p.divergent_reviews_count} Flagged</span></td>
                      <td>{p.avg_sentiment_score}</td>
                      <td>
                        <button
                          className="theme-toggle-btn"
                          style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                          onClick={() => openProductModal(p.product_id)}
                        >
                          Inspect Reviews 🔍
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CONVERSION FUNNEL & PRICING */}
      {activeTab === "funnel" && (
        <div>
          <div className="kpi-grid">
            <KPICard label="Total Product Views" value={funnel?.total_views || 0} color="#6366f1" />
            <KPICard label="Adds to Cart" value={funnel?.total_adds_to_cart || 0} color="#3b82f6" />
            <KPICard label="Completed Purchases" value={funnel?.total_purchases || 0} color="#10b981" />
            <KPICard label="Cart Abandonments" value={funnel?.total_abandoned_carts || 0} color="#f59e0b" />
            <KPICard label="Order Conversion Rate" value={`${funnel?.overall_conversion_rate || 0}%`} color="#ec4899" />
          </div>

          <div className="section-box">
            <h2 className="section-title">🎯 Real-Time Conversion Funnel Drop-off</h2>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={[
                  { stage: "1. Views", count: funnel?.total_views || 1000 },
                  { stage: "2. Adds to Cart", count: funnel?.total_adds_to_cart || 350 },
                  { stage: "3. Purchases", count: funnel?.total_purchases || 140 },
                  { stage: "4. Abandoned Carts", count: funnel?.total_abandoned_carts || 210 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip formatter={(v) => [v, "Events"]} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  <Cell fill="#6366f1" />
                  <Cell fill="#3b82f6" />
                  <Cell fill="#10b981" />
                  <Cell fill="#f59e0b" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* TAB 4: LIVE EVENT STREAM */}
      {activeTab === "streaming" && (
        <div className="section-box">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 className="section-title" style={{ margin: 0 }}>📡 Real-Time Live Clickstream Ticker</h2>
            <span className="badge badge-positive">Connected (SSE Live)</span>
          </div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 0 }}>
            Streaming purchase and view events emitted by the Kafka producer in real time.
          </p>

          <div className="live-feed-list">
            {liveEvents.length === 0 ? (
              <div style={{ color: "var(--text-muted)", padding: "1.5rem", textAlign: "center" }}>
                Listening for incoming streaming events from Kafka...
              </div>
            ) : (
              liveEvents.map((evt, idx) => (
                <div key={idx} className="feed-item">
                  <div>
                    <span className="badge badge-positive" style={{ marginRight: "0.5rem" }}>
                      💰 {evt.event_type}
                    </span>
                    <strong>{evt.user_id}</strong> bought in <em>{evt.category}</em>
                  </div>
                  <div style={{ fontWeight: 700, color: "var(--accent)" }}>
                    +₹{evt.amount}
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "0.75rem" }}>
                      {evt.timestamp}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* PRODUCT INSPECTION MODAL */}
      {selectedProduct && (
        <div className="modal-overlay" onClick={() => setSelectedProduct(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ margin: 0 }}>{selectedProduct.product?.product_name}</h3>
                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  ID: <code>{selectedProduct.product?.product_id}</code> | Category: {selectedProduct.product?.category}
                </span>
              </div>
              <button className="theme-toggle-btn" onClick={() => setSelectedProduct(null)}>✕ Close</button>
            </div>

            <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
              <div className="kpi-card" style={{ flex: 1, padding: "0.75rem" }}>
                <div className="kpi-label">Rating</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>⭐ {selectedProduct.product?.rating}</div>
              </div>
              <div className="kpi-card" style={{ flex: 1, padding: "0.75rem" }}>
                <div className="kpi-label">Analyzed Sentiment</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                  {selectedProduct.sentiment_summary?.avg_sentiment_score || "0.0"}
                </div>
              </div>
              <div className="kpi-card" style={{ flex: 1, padding: "0.75rem" }}>
                <div className="kpi-label">Divergent Reviews</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#b91c1c" }}>
                  {selectedProduct.sentiment_summary?.divergent_count || 0}
                </div>
              </div>
            </div>

            <h4 style={{ margin: "0 0 0.75rem" }}>Customer Reviews & Sentiment Classification</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {selectedProduct.sample_reviews?.map((r) => (
                <div
                  key={r.review_id}
                  style={{
                    background: "var(--bg)",
                    border: `1px solid ${r.is_divergent ? "#facc15" : "var(--border)"}`,
                    borderRadius: "8px",
                    padding: "0.75rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                    <strong>{r.review_title || "Untitled Review"}</strong>
                    <div>
                      <span className={`badge badge-${r.sentiment_label?.toLowerCase()}`}>
                        {r.sentiment_label} ({r.sentiment_score})
                      </span>
                      {r.is_divergent && (
                        <span className="badge badge-alarm" style={{ marginLeft: "0.4rem" }}>
                          ⚠️ Divergent
                        </span>
                      )}
                    </div>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text)" }}>
                    {r.review_content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function KPICard({ label, value, color }) {
  return (
    <div className="kpi-card" style={{ borderTop: `4px solid ${color}` }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  )
}

function jsonParseSafe(str) {
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}
