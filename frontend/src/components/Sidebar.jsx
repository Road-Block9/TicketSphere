import React from "react";
import {
  LayoutDashboard,
  UploadCloud,
  Sparkles,
  Ticket,
  ShieldCheck,
  Activity,
} from "lucide-react";

export default function Sidebar({ activeTab, setActiveTab, backendStatus }) {
  const navItems = [
    { id: "overview", label: "Analytics & KPIs", icon: LayoutDashboard },
    { id: "ingestion", label: "Data Ingestion", icon: UploadCloud },
    { id: "genai", label: "AI Insights Assistant", icon: Sparkles },
    { id: "tickets", label: "Tickets Explorer", icon: Ticket },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 transition-colors duration-200">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 dark:text-white text-base leading-tight">
                SupportSense AI
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Ticket Analytics & GenAI
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1.5">
          <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Modules
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Icon
                  className={`w-5 h-5 ${
                    isActive
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Backend Status Card in Sidebar Footer */}
      <div className="p-4 border-t border-slate-100 dark:border-slate-800">
        <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-500" />
              <span>Flask API</span>
            </span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                backendStatus.online
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300"
                  : "bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-300"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                  backendStatus.online ? "bg-emerald-500" : "bg-rose-500"
                }`}
              ></span>
              {backendStatus.online ? "Connected" : "Offline"}
            </span>
          </div>
          {backendStatus.online && (
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1.5">
              Total DB Records:{" "}
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {backendStatus.ticketCount}
              </span>
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
