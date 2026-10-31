import React from "react";
import {
  Inbox,
  Clock,
  AlertTriangle,
  CheckCircle2,
  PieChart,
  BarChart3,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  Layers,
} from "lucide-react";

export default function OverviewTab({ kpis, loading, error, onRefresh }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Loading analytics & SQL business metrics...
        </p>
      </div>
    );
  }

  if (error || !kpis) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 rounded-xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-lg font-bold text-rose-900 dark:text-rose-200">
          Analytics Service Unavailable
        </h3>
        <p className="text-sm text-rose-700 dark:text-rose-300">
          {error || "Unable to retrieve metrics from Flask backend."}
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

  // Formatting helpers
  const total = kpis.total_tickets || 0;
  const unresolved = kpis.unresolved_tickets || 0;
  const unresolvedRate = kpis.unresolved_rate_pct != null ? kpis.unresolved_rate_pct : 0;
  const avgHours = kpis.avg_resolution_hours != null ? kpis.avg_resolution_hours.toFixed(1) : "N/A";
  const criticalCount = (kpis.critical_unresolved_count || 0) + (kpis.high_unresolved_count || 0);

  const categoryData = kpis.category_distribution || [];
  const statusData = kpis.status_distribution || [];
  const resolutionByCategory = kpis.resolution_by_category || [];
  const attentionTickets = kpis.management_attention_tickets || [];

  return (
    <div className="space-y-6">
      {/* 5 KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Tickets */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              Total Tickets
            </span>
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <Inbox className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {total.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Ingested & stored in SQLite
            </p>
          </div>
        </div>

        {/* Open Backlog */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              Unresolved Backlog
            </span>
            <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {unresolved.toLocaleString()}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {kpis.open_tickets || 0} open, {kpis.pending_tickets || 0} pending
            </p>
          </div>
        </div>

        {/* Unresolved % */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              Unresolved Rate
            </span>
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {unresolvedRate}%
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Of all ingested records
            </p>
          </div>
        </div>

        {/* Avg Resolution Hours */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              Avg Resolution
            </span>
            <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              {avgHours} {avgHours !== "N/A" ? "hrs" : ""}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Resolved/closed tickets
            </p>
          </div>
        </div>

        {/* Critical & High Attention */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">
              High / Critical Alert
            </span>
            <div className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-rose-600 dark:text-rose-400">
              {criticalCount}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {kpis.critical_unresolved_count || 0} critical, {kpis.high_unresolved_count || 0} high
            </p>
          </div>
        </div>
      </div>

      {/* Row 2: Category Distribution & Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <PieChart className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Ticket Volume by Category
              </h3>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {categoryData.length} categories
            </span>
          </div>

          <div className="space-y-3.5">
            {categoryData.map((item, idx) => {
              const catName = item.category || "Unknown";
              const count = item.ticket_count || 0;
              const pct = total > 0 ? Math.round((count / total) * 100) : 0;
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-700 dark:text-slate-300 capitalize">
                      {catName}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">
                      {count} tickets ({pct}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 dark:bg-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Status Breakdown */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Status Breakdown
              </h3>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Workflow states
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40">
              <span className="text-xs font-semibold text-amber-800 dark:text-amber-400 uppercase tracking-wider">
                Open
              </span>
              <p className="text-2xl font-bold text-amber-900 dark:text-amber-200 mt-1">
                {kpis.open_tickets || 0}
              </p>
              <p className="text-xs text-amber-700/80 dark:text-amber-400/80 mt-1">
                Awaiting initial agent pickup
              </p>
            </div>

            <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40">
              <span className="text-xs font-semibold text-blue-800 dark:text-blue-400 uppercase tracking-wider">
                Pending
              </span>
              <p className="text-2xl font-bold text-blue-900 dark:text-blue-200 mt-1">
                {kpis.pending_tickets || 0}
              </p>
              <p className="text-xs text-blue-700/80 dark:text-blue-400/80 mt-1">
                Awaiting customer or technical team
              </p>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-900/40">
              <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider">
                Resolved
              </span>
              <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-200 mt-1">
                {kpis.resolved_tickets || 0}
              </p>
              <p className="text-xs text-emerald-700/80 dark:text-emerald-400/80 mt-1">
                Solution provided to customer
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-100/70 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Closed
              </span>
              <p className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-1">
                {kpis.closed_tickets || 0}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Completed & finalized tickets
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Resolution Time by Category & Management Attention Hotspots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resolution Time by Category */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Average Resolution Time by Category
              </h3>
            </div>
            <span className="text-xs text-slate-400">Hours</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase">
                <tr>
                  <th className="pb-2 font-semibold">Category</th>
                  <th className="pb-2 font-semibold text-right">Resolved Count</th>
                  <th className="pb-2 font-semibold text-right">Avg Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {resolutionByCategory.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-slate-400">
                      No resolved ticket duration data available.
                    </td>
                  </tr>
                ) : (
                  resolutionByCategory.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="py-2.5 font-medium text-slate-800 dark:text-slate-200 capitalize">
                        {row.category}
                      </td>
                      <td className="py-2.5 text-right text-slate-600 dark:text-slate-400">
                        {row.resolved_count}
                      </td>
                      <td className="py-2.5 text-right font-semibold text-indigo-600 dark:text-indigo-400">
                        {row.avg_resolution_hours != null
                          ? `${Number(row.avg_resolution_hours).toFixed(1)} hrs`
                          : "N/A"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Management Attention Tickets */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                Immediate Management Attention Hotspots
              </h3>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300">
              Critical & High
            </span>
          </div>

          <div className="space-y-2.5">
            {attentionTickets.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">
                No high or critical unresolved tickets in backlog.
              </p>
            ) : (
              attentionTickets.slice(0, 5).map((t, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 flex items-center justify-between"
                >
                  <div className="space-y-0.5 min-w-0 pr-3">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                        {t.ticket_id}
                      </span>
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
                        {t.subject}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 truncate">
                      {t.customer_name} • {t.category}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 shrink-0">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                        t.priority?.toLowerCase() === "critical"
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                          : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                      }`}
                    >
                      {t.priority}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 uppercase">
                      {t.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
