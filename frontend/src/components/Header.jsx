import { Sun, Moon, RefreshCw } from "lucide-react";

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
    <header className="h-14 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 transition-colors duration-200">
      {/* Title & Subtitle */}
      <div className="min-w-0 pr-4">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 tracking-tight leading-tight">
          {currentTabInfo.title}
        </h2>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
          {currentTabInfo.subtitle}
        </p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-2 shrink-0">
        {/* Compact Backend Connectivity Indicator */}
        <div
          className="hidden sm:inline-flex items-center space-x-2 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 text-slate-700 dark:text-slate-300"
          title={
            backendStatus.online
              ? `Connected to Flask API on :5000 (${backendStatus.ticketCount} tickets in SQLite)`
              : "Cannot reach Flask API on http://127.0.0.1:5000"
          }
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              backendStatus.online
                ? "bg-emerald-500 dark:bg-emerald-400"
                : "bg-rose-500 dark:bg-rose-400"
            }`}
          />
          <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300">
            {backendStatus.online ? "Connected" : "Disconnected"}
          </span>
        </div>

        {/* Refresh Data Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="inline-flex items-center justify-center w-7 h-7 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 transition-colors duration-150 disabled:opacity-50 focus:outline-none focus:ring-1 focus:ring-slate-400 dark:focus:ring-slate-600"
          title="Refresh analytics and system status"
          aria-label="Refresh analytics and system status"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${
              isRefreshing ? "animate-spin text-slate-900 dark:text-slate-100" : ""
            }`}
          />
        </button>

        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={toggleTheme}
          className="inline-flex items-center justify-center w-7 h-7 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 transition-colors duration-150 focus:outline-none focus:ring-1 focus:ring-slate-400 dark:focus:ring-slate-600"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? (
            <Sun className="w-3.5 h-3.5 text-slate-400 hover:text-slate-200" />
          ) : (
            <Moon className="w-3.5 h-3.5 text-slate-600 hover:text-slate-900" />
          )}
        </button>
      </div>
    </header>
  );
}
