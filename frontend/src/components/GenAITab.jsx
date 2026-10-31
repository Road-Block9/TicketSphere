import React, { useState } from "react";
import {
  Sparkles,
  ShieldCheck,
  Cpu,
  Clock,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  FileText,
} from "lucide-react";
import { api } from "../api";

export default function GenAITab() {
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

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

  const handleCopy = () => {
    if (reportData?.report) {
      navigator.clipboard.writeText(reportData.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Intro & Prompt Engineering Architecture Card */}
      <div className="bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-transparent p-6 rounded-2xl border border-purple-200/60 dark:border-purple-900/40">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-purple-600 rounded-xl text-white shrink-0 shadow-md shadow-purple-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                GenAI Support Insights Assistant
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                Synthesizes raw SQL metrics into strategic, human-readable executive intelligence using Google Gemini LLM. The system prompt enforces strict numerical grounding: claims must originate from verified database metrics, with zero hallucination.
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="shrink-0 flex items-center space-x-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-purple-500/20 disabled:opacity-50 transition-all duration-150"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Generating Report...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Management Report</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start space-x-3 text-xs text-rose-700 dark:text-rose-300">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-bold block">Generation Error</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Report Display */}
      {reportData ? (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          {/* Metadata Top Bar */}
          <div className="px-6 py-4 bg-slate-50/80 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <span
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                  reportData.is_fallback
                    ? "bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300"
                    : "bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300"
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>{reportData.model_name}</span>
                {reportData.is_fallback && <span>(Deterministic Fallback)</span>}
              </span>

              <span className="inline-flex items-center space-x-1 text-xs text-slate-500 dark:text-slate-400">
                <Clock className="w-3.5 h-3.5" />
                <span>{reportData.generation_time_seconds?.toFixed(2)}s runtime</span>
              </span>
            </div>

            <button
              onClick={handleCopy}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Report</span>
                </>
              )}
            </button>
          </div>

          {/* Strict Grounding Notice */}
          <div className="px-6 py-3 bg-emerald-50/60 dark:bg-emerald-950/20 border-b border-emerald-100 dark:border-emerald-900/30 flex items-center space-x-2 text-xs text-emerald-800 dark:text-emerald-300 font-medium">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <span>{reportData.disclaimer}</span>
          </div>

          {/* Report Markdown Viewer */}
          <div className="p-8">
            <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {reportData.report}
            </div>
          </div>
        </div>
      ) : !loading ? (
        /* Empty State */
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-4">
          <div className="w-14 h-14 mx-auto rounded-full bg-purple-50 dark:bg-purple-950/60 flex items-center justify-center text-purple-600 dark:text-purple-400">
            <FileText className="w-7 h-7" />
          </div>
          <div>
            <h4 className="text-base font-bold text-slate-900 dark:text-white">
              No Report Generated Yet
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
              Click the "Generate Management Report" button above to synthesize the latest ticket analytics into an executive summary with trend observations and operational actions.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
