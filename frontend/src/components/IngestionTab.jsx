import React, { useState } from "react";
import {
  UploadCloud,
  FileText,
  Globe,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  RotateCcw,
  AlertTriangle,
  Trash2,
  X,
} from "lucide-react";
import { api } from "../api";

export default function IngestionTab({ onIngestionComplete, setActiveTab }) {
  // CSV Ingestion state
  const [selectedFile, setSelectedFile] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvResult, setCsvResult] = useState(null);
  const [csvError, setCsvError] = useState(null);
  const [csvErrorDetails, setCsvErrorDetails] = useState([]);

  // API Ingestion state (dynamically configurable via env or default)
  const defaultMockUrl =
    import.meta.env.VITE_MOCK_API_URL || "http://127.0.0.1:8000/api/v1/tickets";
  const [apiUrl, setApiUrl] = useState(defaultMockUrl);
  const [apiKey, setApiKey] = useState("");
  const [apiLoading, setApiLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [apiError, setApiError] = useState(null);

  // Reset Demo Data state
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState(null);
  const [resetError, setResetError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const maxUploadBytes = 16 * 1024 * 1024; // 16 MB limit
      if (file.size > maxUploadBytes) {
        setCsvError(
          `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the maximum allowed limit of 16 MB.`
        );
        setCsvErrorDetails(["Please select a CSV file smaller than 16 MB."]);
        setSelectedFile(null);
        e.target.value = "";
        return;
      }
      setSelectedFile(file);
      setCsvResult(null);
      setCsvError(null);
      setCsvErrorDetails([]);
    }
  };

  const handleCsvUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setCsvLoading(true);
    setCsvError(null);
    setCsvErrorDetails([]);
    setCsvResult(null);

    try {
      const response = await api.uploadCsv(selectedFile);
      setCsvResult(response);
      if (onIngestionComplete) onIngestionComplete();
    } catch (err) {
      setCsvError(err.message || "Failed to process CSV file.");
      setCsvErrorDetails(err.errors || []);
    } finally {
      setCsvLoading(false);
    }
  };

  const handleApiIngest = async (e) => {
    e.preventDefault();
    setApiLoading(true);
    setApiError(null);
    setApiResult(null);

    try {
      const response = await api.triggerApiIngest(apiUrl, apiKey);
      setApiResult(response);
      if (onIngestionComplete) onIngestionComplete();
    } catch (err) {
      setApiError(err.message || "API ingestion failed.");
    } finally {
      setApiLoading(false);
    }
  };

  const handleResetDemoData = async () => {
    setResetLoading(true);
    setResetError(null);
    setResetMessage(null);

    try {
      const response = await api.resetDemoData();
      setResetMessage(
        response.message ||
          "Demo data successfully reset. The database is restored to a clean baseline."
      );

      // Clear transient form state & previous results
      setSelectedFile(null);
      setCsvResult(null);
      setCsvError(null);
      setCsvErrorDetails([]);
      setApiResult(null);
      setApiError(null);
      setShowResetConfirm(false);

      // Refresh dashboard KPIs, charts, and tickets count in parent
      if (onIngestionComplete) {
        await onIngestionComplete();
      }
    } catch (err) {
      setResetError(err.message || "Failed to reset demo data.");
      setShowResetConfirm(false);
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Overview Intro Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 sm:p-5 rounded-xl transition-colors duration-200">
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
            <UploadCloud className="w-4 h-4" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            End-to-End Ingestion Pipeline
          </h3>
        </div>
      </div>

      {/* Reset Notification Banners */}
      {resetMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300">
          <div className="flex items-center space-x-2.5">
            <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <span className="font-semibold">{resetMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setResetMessage(null)}
            className="text-emerald-600 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-200 p-1"
            title="Dismiss message"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {resetError && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-center justify-between text-xs text-rose-800 dark:text-rose-300">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
            <span className="font-semibold">{resetError}</span>
          </div>
          <button
            type="button"
            onClick={() => setResetError(null)}
            className="text-rose-600 hover:text-rose-800 dark:text-rose-400 dark:hover:text-rose-200 p-1"
            title="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Module 2: CSV File Upload Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 pb-4 border-b border-slate-100 dark:border-slate-800">
              <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <div>
                <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                  CSV File Ingestion
                </h4>
                <p className="text-xs text-slate-500">
                  Validate & load local customer support ticket CSVs
                </p>
              </div>
            </div>

            <form onSubmit={handleCsvUpload} className="mt-5 space-y-4">
              <div className="h-[124px] border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl flex flex-col items-center justify-center px-4 py-2 text-center hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
                <input
                  type="file"
                  id="csv-file-input"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="csv-file-input"
                  className="cursor-pointer flex flex-col items-center space-y-1"
                >
                  <div className="p-1.5 bg-slate-100 dark:bg-slate-800 rounded-full text-indigo-600 dark:text-indigo-400">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
                    {selectedFile ? selectedFile.name : "Choose a CSV file"}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    {selectedFile
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : "Drag & drop or browse from filesystem"}
                  </span>
                </label>
              </div>

              {csvError && (
                <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-700 dark:text-rose-300 space-y-2">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
                    <span className="font-semibold">{csvError}</span>
                  </div>
                  {csvErrorDetails && csvErrorDetails.length > 0 && (
                    <div className="pl-6 pt-1.5 border-t border-rose-200/60 dark:border-rose-900/40">
                      <p className="font-medium text-[11px] text-rose-800 dark:text-rose-200 mb-1">Validation Details:</p>
                      <ul className="list-disc space-y-1 text-[11px] text-rose-600 dark:text-rose-400">
                        {csvErrorDetails.map((detail, idx) => (
                          <li key={idx}>{detail}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedFile || csvLoading}
                className="w-full h-10 flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-150"
              >
                {csvLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing Ingestion Pipeline...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    <span>Run CSV Ingestion Pipeline</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* CSV Result Summary */}
          {csvResult && (
            <div className="mt-6 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
                <CheckCircle className="w-4 h-4" />
                <span>{csvResult.message}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Received / Checked</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {csvResult.ingestion?.records_received} records
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Duplicates Filtered</span>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">
                    {csvResult.data_quality?.duplicates_removed} duplicates
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Inserted into SQLite</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    +{csvResult.database?.records_inserted} new records
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Skipped (Existing)</span>
                  <span className="font-semibold text-slate-600 dark:text-slate-300">
                    {csvResult.database?.records_skipped_duplicate} records
                  </span>
                </div>
              </div>

              {setActiveTab && (
                <div className="pt-2 flex items-center space-x-2 border-t border-slate-200/60 dark:border-slate-700/60">
                  <button
                    type="button"
                    onClick={() => setActiveTab("overview")}
                    className="flex-1 py-1.5 px-3 bg-indigo-50 dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-slate-700 text-indigo-700 dark:text-indigo-300 font-medium rounded-lg text-xs flex items-center justify-center space-x-1 transition-colors"
                  >
                    <span>Explore in Analytics</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab("tickets")}
                    className="py-1.5 px-3 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg text-xs transition-colors"
                  >
                    Browse Tickets
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Module 6: REST API Ingestion Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 pb-4 border-b border-slate-100 dark:border-slate-800">
              <Globe className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <div>
                <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                  REST API Ingestion
                </h4>
                <p className="text-xs text-slate-500">
                  Fetch live tickets from authenticated external endpoint
                </p>
              </div>
            </div>

            <form onSubmit={handleApiIngest} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  API Endpoint URL
                </label>
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  API Key / Bearer Token (Optional)
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Optional (leave blank for local mock or public APIs)"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {apiError && (
                <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-700 dark:text-rose-300 space-y-2">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
                    <span className="font-semibold">{apiError}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-rose-100/70 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800/50 space-y-1 text-[11px]">
                    <span className="font-semibold text-rose-800 dark:text-rose-200 block">
                      Mock API Startup Instructions:
                    </span>
                    <p className="text-slate-600 dark:text-slate-300">
                      The REST API server runs independently from Flask. To start it, run in your terminal:
                    </p>
                    <code className="block mt-1 px-2 py-1 rounded bg-slate-900 text-emerald-400 font-mono text-[11px]">
                      python src/mock_api.py
                    </code>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
                      (Configurable via MOCK_API_PORT and MOCK_API_HOST environment variables)
                    </p>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={apiLoading}
                className="w-full h-10 flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-50 transition-all duration-150"
              >
                {apiLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Connecting to API Service...</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-4 h-4" />
                    <span>Trigger API Ingestion</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* API Result Summary */}
          {apiResult && (
            <div className="mt-6 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
                <CheckCircle className="w-4 h-4" />
                <span>{apiResult.message}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">HTTP Records Fetched</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {apiResult.records_fetched} records
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Data Quality Corrected</span>
                  <span className="font-semibold text-blue-600 dark:text-blue-400">
                    {apiResult.data_quality?.records_corrected || 0} fields
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Inserted into SQLite</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    +{apiResult.database?.records_inserted} new records
                  </span>
                </div>
                <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-400 block">Total Database Count</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {apiResult.database?.total_in_db} records
                  </span>
                </div>
              </div>

              {setActiveTab && (
                <div className="pt-2 flex items-center space-x-2 border-t border-slate-200/60 dark:border-slate-700/60">
                  <button
                    type="button"
                    onClick={() => setActiveTab("overview")}
                    className="flex-1 py-1.5 px-3 bg-indigo-50 dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-slate-700 text-indigo-700 dark:text-indigo-300 font-medium rounded-lg text-xs flex items-center justify-center space-x-1 transition-colors"
                  >
                    <span>Explore in Analytics</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab("tickets")}
                    className="py-1.5 px-3 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg text-xs transition-colors"
                  >
                    Browse Tickets
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Demo Data Management Card */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 bg-rose-50 dark:bg-rose-950/50 border border-rose-200/80 dark:border-rose-900/50 rounded-xl text-rose-600 dark:text-rose-400 shrink-0">
              <RotateCcw className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-2">
              <h4 className="font-bold text-slate-900 dark:text-white text-lg tracking-tight">
                Reset Demo Data
              </h4>
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                Safe Demo Baseline
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowResetConfirm(true)}
            disabled={resetLoading}
            className="shrink-0 self-start sm:self-auto flex items-center space-x-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors duration-150 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-rose-500/30"
          >
            {resetLoading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Resetting...</span>
              </>
            ) : (
              <>
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Demo Data</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Confirmation Dialog Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div
            className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-md w-full p-6 space-y-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reset-dialog-title"
          >
            <div className="flex items-start space-x-3.5">
              <div className="p-2.5 bg-rose-100 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900/60 rounded-xl text-rose-600 dark:text-rose-400 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3
                  id="reset-dialog-title"
                  className="text-base font-bold text-slate-900 dark:text-white"
                >
                  Reset Demo Data?
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                  This will remove all previously ingested ticket records and audit logs from SQLite to restore the demo baseline.
                </p>
              </div>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 rounded-lg p-3 text-xs text-slate-600 dark:text-slate-300 space-y-1.5">
              <div className="flex items-center space-x-2 font-semibold text-slate-800 dark:text-slate-200">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                <span>What happens next:</span>
              </div>
              <ul className="list-disc pl-5 space-y-1 text-[11px] text-slate-500 dark:text-slate-400">
                <li>SQLite tables, schema, and performance indexes remain intact.</li>
                <li>Allows re-uploading the same CSV dataset with fresh insertion.</li>
                <li>Dashboard KPIs, charts, and ticket counts will reflect 0 records.</li>
              </ul>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setShowResetConfirm(false)}
                disabled={resetLoading}
                className="px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResetDemoData}
                disabled={resetLoading}
                className="flex items-center space-x-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-rose-500/30"
              >
                {resetLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Resetting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm Reset</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
