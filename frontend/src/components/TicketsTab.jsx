import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Clock,
  User,
  Mail,
  Calendar,
  Layers,
  RefreshCw,
} from "lucide-react";
import { api } from "../api";

export default function TicketsTab({ refreshTrigger }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [expandedTicketId, setExpandedTicketId] = useState(null);

  // Available categories derived dynamically from fetched tickets or fallback
  const availableCategories = useMemo(() => {
    const fromTickets = Array.from(new Set(tickets.map((t) => t.category).filter(Boolean)));
    const canonical = [
      "Billing & Refunds",
      "Customer Service",
      "Delivery & Shipping",
      "Product Quality",
      "Technical Support",
    ];
    return Array.from(new Set([...canonical, ...fromTickets])).sort();
  }, [tickets]);

  const fetchTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const cleanSearch = search.trim().replace(/^["'`]|["'`,;]$/g, "");
      const res = await api.getTickets({
        search: cleanSearch || undefined,
        status: status || undefined,
        category: category || undefined,
        priority: priority || undefined,
        limit: 100,
      });
      setTickets(res.tickets || []);
    } catch (err) {
      setError(err.message || "Failed to load tickets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTickets();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, status, category, priority, refreshTrigger]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTickets();
  };

  const handleClearFilters = () => {
    setSearch("");
    setStatus("");
    setCategory("");
    setPriority("");
  };

  const toggleExpand = (id) => {
    setExpandedTicketId(expandedTicketId === id ? null : id);
  };

  const getPriorityBadge = (p) => {
    const val = (p || "").toLowerCase();
    if (val === "critical")
      return "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border-rose-200 dark:border-rose-800";
    if (val === "high")
      return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-200 dark:border-amber-800";
    if (val === "medium")
      return "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-800";
    return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700";
  };

  const getStatusBadge = (s) => {
    const val = (s || "").toLowerCase();
    if (val === "open")
      return "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800";
    if (val === "pending")
      return "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800";
    if (val === "resolved")
      return "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
    return "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700";
  };

  return (
    <div className="space-y-6">
      {/* Search & Filter Toolbar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by ticket ID, subject, customer, or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-9 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 capitalize"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>

          {/* Category Filter */}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            {availableCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          {/* Priority Filter */}
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 capitalize"
          >
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          {(search || status || category || priority) && (
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}

          <div className="ml-auto text-slate-400 font-medium">
            Showing <strong className="text-slate-700 dark:text-slate-200">{tickets.length}</strong> records
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-center space-x-2 text-xs text-rose-700 dark:text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tickets Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
            <p className="text-xs text-slate-500">Querying database records...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <Layers className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No Tickets Match Criteria
            </h4>
            <p className="text-xs text-slate-400">
              Try adjusting your search terms or filter dropdowns.
            </p>
            {(search || status || category || priority) && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Clear All Filters & Search</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="py-3 px-4">Ticket ID</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Duration</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {tickets.map((t) => {
                  const isExpanded = expandedTicketId === t.ticket_id;
                  return (
                    <React.Fragment key={t.ticket_id}>
                      <tr
                        onClick={() => toggleExpand(t.ticket_id)}
                        className={`cursor-pointer transition-colors ${
                          isExpanded
                            ? "bg-indigo-50/40 dark:bg-slate-800/60"
                            : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                        }`}
                      >
                        <td className="py-3 px-4 font-mono font-semibold text-indigo-600 dark:text-indigo-400">
                          {t.ticket_id}
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-900 dark:text-white font-mono text-[11px]">
                          {t.customer_id || "—"}
                        </td>
                        <td className="py-3 px-4 text-slate-700 dark:text-slate-300 max-w-xs truncate">
                          {t.subject}
                        </td>
                        <td className="py-3 px-4 capitalize text-slate-600 dark:text-slate-400">
                          {t.category}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getPriorityBadge(
                              t.priority
                            )}`}
                          >
                            {t.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase border ${getStatusBadge(
                              t.status
                            )}`}
                          >
                            {t.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-slate-600 dark:text-slate-400 font-mono">
                          {t.resolution_time_hours != null
                            ? `${Number(t.resolution_time_hours).toFixed(1)}h`
                            : "—"}
                        </td>
                        <td className="py-3 px-4 text-center text-slate-400">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 mx-auto" />
                          ) : (
                            <ChevronDown className="w-4 h-4 mx-auto" />
                          )}
                        </td>
                      </tr>

                      {/* Expanded Details Row */}
                      {isExpanded && (
                        <tr className="bg-slate-50/70 dark:bg-slate-800/30">
                          <td colSpan={8} className="p-4 border-b border-slate-200 dark:border-slate-800">
                            <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs border-b border-slate-100 dark:border-slate-800 pb-3">
                                <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                                  <User className="w-4 h-4 text-indigo-500" />
                                  <span>
                                    <strong>Customer:</strong> {t.customer_name}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                                  <Mail className="w-4 h-4 text-indigo-500" />
                                  <span>
                                    <strong>Email:</strong> {t.customer_email || "N/A"}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                                  <Calendar className="w-4 h-4 text-indigo-500" />
                                  <span>
                                    <strong>Created:</strong> {t.created_at}
                                  </span>
                                </div>
                              </div>

                              <div>
                                <h5 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-1">
                                  Complaint Description:
                                </h5>
                                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                                  {t.description || "No detailed description provided."}
                                </p>
                              </div>

                              {t.resolved_at && (
                                <div className="text-xs text-slate-500 flex items-center space-x-1">
                                  <Clock className="w-3.5 h-3.5 text-emerald-500" />
                                  <span>
                                    Resolved on <strong>{t.resolved_at}</strong> ({t.resolution_time_hours} hours duration)
                                  </span>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
