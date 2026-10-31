import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import OverviewTab from "./components/OverviewTab";
import IngestionTab from "./components/IngestionTab";
import GenAITab from "./components/GenAITab";
import TicketsTab from "./components/TicketsTab";
import { api } from "./api";

function App() {
  const [activeTab, setActiveTab] = useState("overview");

  // Light / Dark Theme State with persistence in localStorage and system preference check
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("theme");
    if (saved) return saved;
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  const [backendStatus, setBackendStatus] = useState({
    online: false,
    ticketCount: 0,
    version: "1.0.0",
  });
  const [kpis, setKpis] = useState(null);
  const [loadingKpis, setLoadingKpis] = useState(true);
  const [kpisError, setKpisError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Sync theme with DOM root
  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  // Load backend health and analytics KPIs
  const loadData = async () => {
    setIsRefreshing(true);
    setLoadingKpis(true);
    setKpisError(null);

    // Step 1: Health check
    try {
      const health = await api.getHealth();
      setBackendStatus({
        online: true,
        ticketCount: health.total_tickets_in_db || 0,
        version: health.version || "1.0.0",
      });
    } catch (err) {
      setBackendStatus({
        online: false,
        ticketCount: 0,
        version: "offline",
      });
      setKpisError(err.message || "Failed to reach Flask backend server.");
      setLoadingKpis(false);
      setIsRefreshing(false);
      return;
    }

    // Step 2: Fetch KPIs
    try {
      const res = await api.getKpis();
      if (res && res.data) {
        setKpis(res.data);
      }
    } catch (err) {
      setKpisError(err.message || "Failed to retrieve analytics KPIs.");
    } finally {
      setLoadingKpis(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 font-sans antialiased text-slate-900 dark:text-slate-100 selection:bg-indigo-500 selection:text-white transition-colors duration-200 overflow-hidden">
      {/* Fixed Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          activeTab={activeTab}
          theme={theme}
          setTheme={setTheme}
          backendStatus={backendStatus}
          onRefresh={loadData}
          isRefreshing={isRefreshing}
        />

        {/* Tab Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {activeTab === "overview" && (
              <OverviewTab
                kpis={kpis}
                loading={loadingKpis}
                error={kpisError}
                onRefresh={loadData}
                theme={theme}
              />
            )}

            {activeTab === "ingestion" && (
              <IngestionTab onIngestionComplete={loadData} />
            )}

            {activeTab === "genai" && <GenAITab />}

            {activeTab === "tickets" && <TicketsTab />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
