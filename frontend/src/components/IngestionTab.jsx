import React, { useState } from "react";
import {
  UploadCloud,
  FileText,
  Globe,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { api } from "../api";

export default function IngestionTab({ onIngestionComplete, setActiveTab }) {
  // CSV Ingestion state
  const [selectedFile, setSelectedFile] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvResult, setCsvResult] = useState(null);
  const [csvError, setCsvError] = useState(null);

  // API Ingestion state
  const [apiUrl, setApiUrl] = useState("http://127.0.0.1:8000/api/v1/tickets");
  const [apiKey, setApiKey] = useState("capstone-demo-key-2026");
  const [apiLoading, setApiLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [apiError, setApiError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setCsvResult(null);
      setCsvError(null);
    }
  };

  const handleCsvUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setCsvLoading(true);
    setCsvError(null);
    setCsvResult(null);

    try {
      const response = await api.uploadCsv(selectedFile);
      setCsvResult(response);
      if (onIngestionComplete) onIngestionComplete();
    } catch (err) {
      setCsvError(err.message || "Failed to process CSV file.");
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

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Overview Intro Banner */}
      <div className="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-transparent p-6 rounded-2xl border border-indigo-200/60 dark:border-indigo-900/40">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-indigo-600 rounded-xl text-white shrink-0 shadow-md shadow-indigo-500/20">
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              End-to-End Ingestion Pipeline
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
              Files and API records pass through the identical 3-stage pipeline:{" "}
              <strong>Schema Validation</strong> (Module 2),{" "}
              <strong>Data Quality Audit & Normalization</strong> (Module 3), and{" "}
              <strong>Idempotent Storage</strong> (Module 4). Duplicate ticket IDs are automatically skipped to preserve historical record integrity.
            </p>
          </div>
        </div>
      </div>

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
              <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-6 text-center hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
                <input
                  type="file"
                  id="csv-file-input"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="csv-file-input"
                  className="cursor-pointer flex flex-col items-center space-y-2"
                >
                  <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-full text-indigo-600 dark:text-indigo-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
                    {selectedFile ? selectedFile.name : "Choose a CSV file"}
                  </span>
                  <span className="text-xs text-slate-400">
                    {selectedFile
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : "Drag & drop or browse from filesystem"}
                  </span>
                </label>
              </div>

              {csvError && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start space-x-2 text-xs text-rose-700 dark:text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{csvError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedFile || csvLoading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-50 transition-all duration-150"
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
                  API Bearer / Secret Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              {apiError && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start space-x-2 text-xs text-rose-700 dark:text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{apiError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={apiLoading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-500/20 disabled:opacity-50 transition-all duration-150"
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
    </div>
  );
}
