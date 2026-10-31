import React from "react";
import { Sun, Moon, RefreshCw, Server } from "lucide-react";

export default function Header({
  activeTab,
  theme,
  setTheme,
  backendStatus,
  onRefresh,
  isRefreshing,
}) {
  const tabTitles = {
    overview: {
      title: "Analytics & Business KPIs",
      subtitle: "Verified SQL metrics computed directly from SQLite database",
    },
    ingestion: {
      title: "Data Pipeline & Ingestion",
      subtitle: "Upload CSV files or pull from REST API with live Data Quality audit",
    },
    genai: {
      title: "GenAI Executive Assistant",
      subtitle: "Grounded business insights powered by Google Gemini & verified metrics",
    },
    tickets: {
      title: "Tickets Explorer",
      subtitle: "Browse, filter, and inspect persisted customer support tickets",
    },
  };

  const currentTabInfo = tabTitles[activeTab] || tabTitles.overview;

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <header className="h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 transition-colors duration-200">
      {/* Title & Subtitle */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-tight">
          {currentTabInfo.title}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {currentTabInfo.subtitle}
        </p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-3">
        {/* Backend Connectivity Status Pill */}
        <div
          className={`hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
            backendStatus.online
              ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-300"
              : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300"
          }`}
          title={
            backendStatus.online
              ? `Connected to Flask API on :5000 (${backendStatus.ticketCount} tickets in SQLite)`
              : "Cannot reach Flask API on http://127.0.0.1:5000"
          }
        >
          <Server className="w-3.5 h-3.5" />
          <span>
            {backendStatus.online ? "Backend Online" : "Backend Offline"}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${
              backendStatus.online ? "bg-emerald-500" : "bg-rose-500"
            }`}
          />
        </div>

        {/* Refresh Data Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors duration-150 disabled:opacity-50"
          title="Refresh analytics and system status"
        >
          <RefreshCw
            className={`w-4 h-4 ${isRefreshing ? "animate-spin text-indigo-600 dark:text-indigo-400" : ""}`}
          />
        </button>

        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors duration-150"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <Sun className="w-4 h-4 text-amber-400 hover:rotate-45 transition-transform" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700 hover:-rotate-12 transition-transform" />
          )}
        </button>
      </div>
    </header>
  );
}
