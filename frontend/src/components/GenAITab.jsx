import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Sparkles,
  Cpu,
  Clock,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  FileText,
  Code,
  Eye,
  Inbox,
  AlertTriangle,
  Timer,
} from "lucide-react";
import { api } from "../api";

export default function GenAITab() {
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState("rendered"); // "rendered" | "raw"

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.generateAiReport();
      setReportData(response);
    } catch (err) {
      setError(err.message || "Failed to generate AI executive report.");
    } finally {
      setLoading(false);
    }
  };

  const cleanReport = (reportData?.report || "").replace(
    /^>\s*\*\*Deterministic Analytical Fallback Mode:\*\*.*?\n\n?/gm,
    ""
  );

  const handleCopy = () => {
    if (cleanReport) {
      navigator.clipboard.writeText(cleanReport);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Safe custom component renderers for ReactMarkdown (never executes raw HTML)
  const markdownComponents = {
    h1: ({ children }) => (
      <h1 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white tracking-tight pb-2.5 mb-3.5 border-b border-slate-200 dark:border-slate-800">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-sm md:text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight mt-5 mb-2.5 flex items-center gap-2">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-xs md:text-sm font-semibold text-slate-800 dark:text-slate-200 mt-3.5 mb-2">
        {children}
      </h3>
    ),
    p: ({ children }) => (
      <p className="text-xs md:text-sm leading-relaxed text-slate-700 dark:text-slate-300 mb-3">
        {children}
      </p>
    ),
    ul: ({ children }) => (
      <ul className="list-disc list-outside pl-4 space-y-1.5 mb-3.5 text-xs md:text-sm text-slate-700 dark:text-slate-300">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-outside pl-4 space-y-1.5 mb-3.5 text-xs md:text-sm text-slate-700 dark:text-slate-300">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="leading-relaxed">
        {children}
      </li>
    ),
    strong: ({ children }) => (
      <strong className="font-semibold text-slate-900 dark:text-white">
        {children}
      </strong>
    ),
    code: ({ children }) => (
      <code className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 font-semibold border border-slate-200 dark:border-slate-700">
        {children}
      </code>
    ),
    blockquote: ({ children }) => (
      <blockquote className="border-l-2 border-indigo-500 bg-indigo-50/30 dark:bg-indigo-950/20 px-3.5 py-2 rounded-r-md my-2.5 text-xs text-slate-600 dark:text-slate-300 italic">
        {children}
      </blockquote>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto my-3.5 rounded-lg border border-slate-200 dark:border-slate-700">
        <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300 border-collapse">
          {children}
        </table>
      </div>
    ),
    th: ({ children }) => (
      <th className="bg-slate-100 dark:bg-slate-800 px-3 py-2 font-semibold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-700">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-3 py-2 border-b border-slate-100 dark:border-slate-800/60">
        {children}
      </td>
    ),
  };

  const metrics = reportData?.metrics;

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Restrained, Compact Report Generation Panel */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 sm:p-5 rounded-xl transition-colors duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                Support Insights Assistant
              </h3>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                AI-assisted
              </span>
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="shrink-0 self-start sm:self-auto flex items-center space-x-2 px-3.5 py-2 bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white rounded-lg text-xs font-medium transition-colors duration-150 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Generating report...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate report</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start space-x-3 text-xs text-rose-700 dark:text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Generation Error</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Report Display */}
      {reportData ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden transition-colors duration-200">
          {/* Metadata Top Bar */}
          <div className="px-5 py-3 bg-slate-50/60 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center flex-wrap gap-2.5">
              <span
                className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-medium border ${
                  reportData.is_fallback
                    ? "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200/80 dark:border-amber-800/60"
                    : "bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 border-purple-200/80 dark:border-purple-800/60"
                }`}
              >
                <Cpu className="w-3 h-3" />
                <span>{reportData.model_name}</span>
              </span>

              {reportData.generation_time_seconds != null && (
                <span className="inline-flex items-center space-x-1 text-[11px] text-slate-500 dark:text-slate-400">
                  <Clock className="w-3 h-3" />
                  <span>{reportData.generation_time_seconds.toFixed(2)}s runtime</span>
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Formatted vs Raw Markdown Toggle */}
              <button
                onClick={() => setViewMode(viewMode === "rendered" ? "raw" : "rendered")}
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
                title="Toggle between formatted HTML and raw Markdown"
              >
                {viewMode === "rendered" ? (
                  <>
                    <Code className="w-3 h-3 text-slate-400" />
                    <span>View Raw</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-3 h-3 text-indigo-500" />
                    <span>View Formatted</span>
                  </>
                )}
              </button>

              <button
                onClick={handleCopy}
                className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-500" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy Report</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Compact Verified KPI Metric Cards */}
          {metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-4 bg-slate-50/40 dark:bg-slate-800/20 border-b border-slate-200 dark:border-slate-800">
              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/70 dark:border-slate-800 flex items-center space-x-2.5">
                <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  <Inbox className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 block uppercase tracking-wider">
                    Total
                  </span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {metrics.total_tickets}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/70 dark:border-slate-800 flex items-center space-x-2.5">
                <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 block uppercase tracking-wider">
                    Backlog
                  </span>
                  <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                    {metrics.unresolved_tickets}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/70 dark:border-slate-800 flex items-center space-x-2.5">
                <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-purple-600 dark:text-purple-400">
                  <Clock className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 block uppercase tracking-wider">
                    Backlog Rate
                  </span>
                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                    {metrics.unresolved_rate_pct}%
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/70 dark:border-slate-800 flex items-center space-x-2.5">
                <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400">
                  <Timer className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 block uppercase tracking-wider">
                    Mean SLA
                  </span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    {metrics.avg_resolution_hours}h
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Report Content Viewport */}
          <div className="p-5 sm:p-7">
            {viewMode === "rendered" ? (
              <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 font-sans">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {cleanReport}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="relative">
                <pre className="p-4 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                  {cleanReport}
                </pre>
              </div>
            )}
          </div>
        </div>
      ) : !loading ? (
        /* Empty State */
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-8 text-center space-y-3">
          <div className="w-10 h-10 mx-auto rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
              No Report Generated Yet
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
              Click the "Generate report" button above to synthesize current ticket volume, SLA bottlenecks, and management escalations.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
