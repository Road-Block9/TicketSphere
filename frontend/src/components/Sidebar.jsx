import React from "react";
import {
  LayoutDashboard,
  UploadCloud,
  Sparkles,
  Ticket,
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
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 transition-colors duration-200 select-none">
      <div>
        {/* Brand Header */}
        <div className="px-5 py-5 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h1 className="font-semibold text-slate-900 dark:text-slate-100 text-base tracking-tight leading-none">
              TicketSphere
            </h1>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-normal leading-normal mt-1.5">
              Customer Support Analytics & GenAI
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          <p className="px-3 pt-2 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
            Modules
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors duration-150 text-left ${
                  isActive
                    ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 font-semibold"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Backend Status in Sidebar Footer */}
      <div className="p-3.5 border-t border-slate-100 dark:border-slate-800">
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
              <span>Flask API</span>
            </span>
            <span className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-700 dark:text-slate-300">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  backendStatus.online ? "bg-emerald-500 dark:bg-emerald-400" : "bg-rose-500"
                }`}
              />
              <span>{backendStatus.online ? "Connected" : "Offline"}</span>
            </span>
          </div>
          {backendStatus.online && (
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
              Records:{" "}
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {backendStatus.ticketCount}
              </span>
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
