import { useEffect, useState } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from "recharts"
import axios from "axios"

const API    = "http://localhost:8000/api"
const COLORS = ["#6366f1","#8b5cf6","#ec4899","#f59e0b","#10b981",
                 "#3b82f6","#ef4444","#14b8a6","#f97316","#84cc16"]

export default function App() {
  const [summary,      setSummary]      = useState(null)
  const [categories,   setCategories]   = useState([])
  const [topRated,     setTopRated]     = useState([])
  const [discountDist, setDiscountDist] = useState([])

  useEffect(() => {
    axios.get(`${API}/kpi-summary`).then(r => setSummary(r.data))
    axios.get(`${API}/top-categories`).then(r => setCategories(r.data))
    axios.get(`${API}/top-rated-products`).then(r => setTopRated(r.data))
    axios.get(`${API}/discount-distribution`).then(r => setDiscountDist(r.data))
  }, [])

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", background: "#f8fafc", minHeight: "100vh" }}>
      <h1 style={{ color: "#1e293b" }}>🛒 Amazon Product Intelligence</h1>

      {/* KPI Cards */}
      {summary && (
        <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem", flexWrap: "wrap" }}>
          <KPICard label="Total Products"  value={summary.total_products}              color="#6366f1" />
          <KPICard label="Avg Rating"      value={`⭐ ${summary.avg_rating}`}           color="#f59e0b" />
          <KPICard label="Avg Discount"    value={`${summary.avg_discount_pct}%`}       color="#10b981" />
          <KPICard label="Total Reviews"   value={Number(summary.total_reviews).toLocaleString()} color="#ec4899" />
        </div>
      )}

      {/* Top Categories */}
      <Section title="📦 Top Categories by Product Count">
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
      </Section>

      {/* Top Rated Products */}
      <Section title="⭐ Top Rated Products (≥ 500 ratings)">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topRated} margin={{ bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="product_name"
              tick={{ fontSize: 10 }}
              angle={-30}
              textAnchor="end"
              interval={0}
            />
            <YAxis domain={[0, 5]} />
            <Tooltip
              formatter={(v) => [`${v} ★`, "Rating"]}
              labelFormatter={(l) => l}
            />
            <Bar dataKey="rating" radius={[4, 4, 0, 0]}>
              {topRated.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Discount Distribution */}
      <Section title="💸 Discount Distribution">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={discountDist}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bucket" />
            <YAxis />
            <Tooltip formatter={(v) => [v, "Products"]} />
            <Bar dataKey="product_count" radius={[4, 4, 0, 0]}>
              {discountDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  )
}

function KPICard({ label, value, color }) {
  return (
    <div style={{
      background: "#fff", borderRadius: "10px", padding: "1.2rem 2rem",
      flex: "1 1 180px", textAlign: "center",
      boxShadow: "0 1px 4px rgba(0,0,0,.08)",
      borderTop: `4px solid ${color}`,
    }}>
      <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.3rem" }}>{label}</div>
      <div style={{ fontSize: "1.8rem", fontWeight: "bold", color: "#1e293b" }}>{value}</div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{
      background: "#fff", borderRadius: "10px", padding: "1.5rem",
      marginBottom: "2rem", boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    }}>
      <h2 style={{ marginTop: 0, color: "#1e293b" }}>{title}</h2>
      {children}
    </div>
  )
}
