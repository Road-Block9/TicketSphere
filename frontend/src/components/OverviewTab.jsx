import React, { useState, useEffect } from "react";
import {
  Inbox,
  Clock,
  AlertTriangle,
  CheckCircle2,
  PieChart as PieIcon,
  BarChart3,
  TrendingUp,
  AlertCircle,
  Filter,
  X,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import { api } from "../api";

export default function OverviewTab({
  kpis: initialKpis,
  loading: initialLoading,
  error: initialError,
  onRefresh,
  theme = "dark",
}) {
  // Local filter states
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");

  // Filtered KPI state
  const [kpis, setKpis] = useState(initialKpis);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync when initialKpis updates and no local filters applied
  useEffect(() => {
    if (!startDate && !endDate && !category && !priority) {
      setKpis(initialKpis);
      setError(initialError);
    }
  }, [initialKpis, initialError]);

  // Fetch with filters
  const applyFilters = async (overrideParams = {}) => {
    const params = {
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      category: category || undefined,
      priority: priority || undefined,
      ...overrideParams,
    };

    setLoading(true);
    setError(null);
    try {
      const res = await api.getKpis(params);
      if (res && res.data) {
        setKpis(res.data);
      }
    } catch (err) {
      setError(err.message || "Failed to load filtered analytics.");
    } finally {
      setLoading(false);
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    applyFilters();
  };

  const handleResetFilters = () => {
    setStartDate("");
    setEndDate("");
    setCategory("");
    setPriority("");
    setKpis(initialKpis);
    setError(initialError);
    if (onRefresh) onRefresh();
  };

  const hasActiveFilters = Boolean(startDate || endDate || category || priority);

  // Recharts theme colors
  const isDark = theme === "dark";
  const gridStroke = isDark ? "#334155" : "#e2e8f0";
  const axisTextColor = isDark ? "#94a3b8" : "#64748b";
  const tooltipBg = isDark ? "#0f172a" : "#ffffff";
  const tooltipBorder = isDark ? "#334155" : "#e2e8f0";
  const tooltipText = isDark ? "#f8fafc" : "#0f172a";

  // Status chart colors
  const STATUS_COLORS = {
    Open: "#f59e0b", // Amber
    Pending: "#3b82f6", // Blue
    Resolved: "#10b981", // Emerald
    Closed: "#64748b", // Slate
  };

  // Safe data accessors
  const currentKpis = kpis || initialKpis || {};
  const total = currentKpis.total_tickets || 0;
  const unresolved = currentKpis.unresolved_tickets || 0;
  const openCount = currentKpis.open_tickets || 0;
  const pendingCount = currentKpis.pending_tickets || 0;
  const resolvedCount = currentKpis.resolved_tickets || 0;
  const closedCount = currentKpis.closed_tickets || 0;
  const unresolvedRate =
    currentKpis.unresolved_rate_pct != null ? currentKpis.unresolved_rate_pct : 0;
  const avgHours =
    currentKpis.avg_resolution_hours != null
      ? currentKpis.avg_resolution_hours.toFixed(1)
      : "0.0";
  const criticalCount =
    (currentKpis.critical_unresolved_count || 0) +
    (currentKpis.high_unresolved_count || 0);

  const categoryData = currentKpis.category_distribution || [];
  const statusData = (currentKpis.status_distribution || []).map((item) => ({
    ...item,
    color: STATUS_COLORS[item.status] || "#6366f1",
  }));
  const volumeTrends = currentKpis.volume_trends || [];
  const unresolvedByCategory = currentKpis.unresolved_by_category || [];

  if (initialLoading && !kpis) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Loading analytics & SQL business metrics...
        </p>
      </div>
    );
  }

  if (initialError && !kpis) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 rounded-xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-lg font-bold text-rose-900 dark:text-rose-200">
          Analytics Service Unavailable
        </h3>
        <p className="text-sm text-rose-700 dark:text-rose-300">
          {initialError || "Unable to retrieve metrics from Flask backend."}
        </p>
        <button
          onClick={onRefresh}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
        >
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters Toolbar */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center space-x-2">
            <SlidersHorizontal className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Interactive Analytics Filters
            </h4>
          </div>
          {hasActiveFilters && (
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 border border-indigo-200/60 dark:border-slate-700">
              Filtered View Active
            </span>
          )}
        </div>

        <form
          onSubmit={handleFilterSubmit}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end text-xs"
        >
          {/* Start Date */}
          <div>
            <label className="block font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block font-semibold text-slate-600 dark:text-slate-400 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Category Dropdown */}
          <div>
            <label className="block font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Categories</option>
              <option value="Billing & Refunds">Billing & Refunds</option>
              <option value="Customer Service">Customer Service</option>
              <option value="Delivery & Shipping">Delivery & Shipping</option>
              <option value="Product Quality">Product Quality</option>
              <option value="Technical Support">Technical Support</option>
            </select>
          </div>

          {/* Priority Dropdown */}
          <div>
            <label className="block font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-sm transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Filter className="w-3.5 h-3.5" />
              )}
              <span>Apply</span>
            </button>

            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="py-2 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                title="Reset all filters"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {error && (
          <div className="mt-3 p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-700 dark:text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 5 KPI Stat Cards with Pastel (Light) & Muted Tinted (Dark) Styling */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Total Tickets (Light: #D6EBFF, Dark: #292F38) */}
        <div className="bg-[#D6EBFF] dark:bg-[#292F38] p-5 rounded-xl border border-[#BBDDFA] dark:border-[#3B4654] shadow-sm flex flex-col justify-between transition-colors duration-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Total Tickets
            </span>
            <div className="p-2 rounded-lg bg-blue-600/10 dark:bg-[#91BFFF]/15 text-blue-700 dark:text-[#91BFFF] border border-blue-600/15 dark:border-[#91BFFF]/25">
              <Inbox className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {total.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              {hasActiveFilters ? "In filtered subset" : "Ingested in database"}
            </p>
          </div>
        </div>

        {/* Card 2: Open Backlog (Light: #EBD5FF, Dark: #302A38) */}
        <div className="bg-[#EBD5FF] dark:bg-[#302A38] p-5 rounded-xl border border-[#DFC3FA] dark:border-[#493B54] shadow-sm flex flex-col justify-between transition-colors duration-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Unresolved Backlog
            </span>
            <div className="p-2 rounded-lg bg-purple-600/10 dark:bg-[#C5A0F5]/15 text-purple-700 dark:text-[#C5A0F5] border border-purple-600/15 dark:border-[#C5A0F5]/25">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {unresolved.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              {openCount} open, {pendingCount} pending
            </p>
          </div>
        </div>

        {/* Card 3: Unresolved Rate (Light: #FFF0BF, Dark: #353025) */}
        <div className="bg-[#FFF0BF] dark:bg-[#353025] p-5 rounded-xl border border-[#F6E19E] dark:border-[#51452F] shadow-sm flex flex-col justify-between transition-colors duration-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Unresolved Rate
            </span>
            <div className="p-2 rounded-lg bg-amber-600/15 dark:bg-[#F0C36D]/15 text-amber-800 dark:text-[#F0C36D] border border-amber-600/20 dark:border-[#F0C36D]/25">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {unresolvedRate}%
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              Of active scope
            </p>
          </div>
        </div>

        {/* Card 4: Avg Resolution Hours (Light: #FFE0D2, Dark: #382A27) */}
        <div className="bg-[#FFE0D2] dark:bg-[#382A27] p-5 rounded-xl border border-[#F5C7B3] dark:border-[#543B35] shadow-sm flex flex-col justify-between transition-colors duration-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Avg Resolution
            </span>
            <div className="p-2 rounded-lg bg-orange-600/15 dark:bg-[#F29A80]/15 text-orange-800 dark:text-[#F29A80] border border-orange-600/20 dark:border-[#F29A80]/25">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {avgHours} {avgHours !== "0.0" ? "hrs" : ""}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              {resolvedCount + closedCount} resolved/closed
            </p>
          </div>
        </div>

        {/* Card 5: Critical Attention (Light: #D6EBFF, Dark: #292F38) */}
        <div className="bg-[#D6EBFF] dark:bg-[#292F38] p-5 rounded-xl border border-[#BBDDFA] dark:border-[#3B4654] shadow-sm flex flex-col justify-between transition-colors duration-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Critical & High Alert
            </span>
            <div className="p-2 rounded-lg bg-blue-600/10 dark:bg-[#91BFFF]/15 text-blue-700 dark:text-[#91BFFF] border border-blue-600/15 dark:border-[#91BFFF]/25">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {criticalCount}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              Immediate management focus
            </p>
          </div>
        </div>
      </div>

      {/* Row 2: Recharts Visualisations (Bar Chart & Status Donut Chart) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recharts Bar Chart: Complaint Categories */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Complaint Categories Volume
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {categoryData.length} categories
            </span>
          </div>

          <div className="h-72 w-full">
            {categoryData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No category data for current filter criteria.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={categoryData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 25 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} opacity={0.6} />
                  <XAxis
                    dataKey="category"
                    tick={{ fill: axisTextColor, fontSize: 10 }}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                  />
                  <YAxis
                    tick={{ fill: axisTextColor, fontSize: 11 }}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: tooltipBg,
                      borderColor: tooltipBorder,
                      borderRadius: "0.75rem",
                      color: tooltipText,
                      fontSize: "12px",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                    formatter={(val, name, item) => [
                      `${val} tickets (${item.payload.percentage || 0}%)`,
                      "Volume",
                    ]}
                  />
                  <Bar
                    dataKey="ticket_count"
                    fill="#6366f1"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Recharts Pie/Donut Chart: Status Distribution */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <PieIcon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Ticket Status Distribution
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Workflow states
            </span>
          </div>

          <div className="h-72 w-full flex items-center justify-center">
            {statusData.length === 0 ? (
              <div className="text-xs text-slate-400">
                No status data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    dataKey="ticket_count"
                    nameKey="status"
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: tooltipBg,
                      borderColor: tooltipBorder,
                      borderRadius: "0.75rem",
                      color: tooltipText,
                      fontSize: "12px",
                    }}
                    formatter={(val, name, item) => [
                      `${val} tickets (${item.payload.percentage || 0}%)`,
                      name,
                    ]}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    formatter={(val) => (
                      <span className="text-xs text-slate-700 dark:text-slate-300 mr-2">
                        {val}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Row 3: Line Chart: Ticket Volume Over Time */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Ticket Volume Trends Over Time
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Temporal trends comparing total volume, unresolved backlog, and resolved tickets
              </p>
            </div>
          </div>
          <span className="text-xs text-slate-400 font-medium">Daily Timeline</span>
        </div>

        <div className="h-72 w-full">
          {volumeTrends.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              No trend data available for current time window.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={volumeTrends}
                margin={{ top: 10, right: 10, left: -20, bottom: 5 }}
              >
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorUnresolved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} opacity={0.6} />
                <XAxis
                  dataKey="ticket_date"
                  tick={{ fill: axisTextColor, fontSize: 10 }}
                />
                <YAxis
                  tick={{ fill: axisTextColor, fontSize: 11 }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: "0.75rem",
                    color: tooltipText,
                    fontSize: "12px",
                  }}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  height={36}
                  formatter={(val) => (
                    <span className="text-xs text-slate-700 dark:text-slate-300">
                      {val}
                    </span>
                  )}
                />
                <Area
                  type="monotone"
                  dataKey="total_volume"
                  name="Total Inflow"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTotal)"
                />
                <Area
                  type="monotone"
                  dataKey="unresolved_volume"
                  name="Unresolved"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorUnresolved)"
                />
                <Area
                  type="monotone"
                  dataKey="resolved_volume"
                  name="Resolved"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorResolved)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Row 4: Categories with Most Unresolved Tickets Table */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Categories with Most Unresolved Tickets (Hotspots)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Prioritised by count of open & pending customer complaints
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300">
            Backlog Distribution
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4 text-center">Total Volume</th>
                <th className="py-3 px-4 text-center">Unresolved Backlog</th>
                <th className="py-3 px-4 text-center">Resolved Count</th>
                <th className="py-3 px-4 text-right">Unresolved Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {unresolvedByCategory.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400">
                    No unresolved ticket records for current criteria.
                  </td>
                </tr>
              ) : (
                unresolvedByCategory.map((row, idx) => {
                  const rate = row.unresolved_rate_pct || 0;
                  return (
                    <tr
                      key={idx}
                      className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100 capitalize">
                        {row.category}
                      </td>
                      <td className="py-3 px-4 text-center text-slate-600 dark:text-slate-400">
                        {row.total_tickets}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded">
                          {row.unresolved_tickets}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center text-slate-600 dark:text-slate-400">
                        {row.resolved_tickets}
                      </td>
                      <td className="py-3 px-4 text-right font-medium">
                        <div className="inline-flex items-center space-x-2">
                          <span
                            className={`font-semibold ${
                              rate > 50
                                ? "text-rose-600 dark:text-rose-400"
                                : rate > 30
                                ? "text-amber-600 dark:text-amber-400"
                                : "text-emerald-600 dark:text-emerald-400"
                            }`}
                          >
                            {rate}%
                          </span>
                          <div className="w-16 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                rate > 50
                                  ? "bg-rose-500"
                                  : rate > 30
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(rate, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
