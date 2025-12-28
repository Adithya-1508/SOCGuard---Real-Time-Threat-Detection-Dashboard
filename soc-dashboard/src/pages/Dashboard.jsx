import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, AlertOctagon, Users, Activity, Download } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import StatCard from "../components/StatCard";
import RecentAlerts from "../components/RecentAlerts";

import WorldMap from "../components/WorldMap";

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    active_alerts: 0,
    recent_alerts: 0,
    high_severity: 0,
    system_health: 100
  });
  const [chartData, setChartData] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);

  useEffect(() => {
    // 1. Initial Fetch
    const fetchInitialData = async () => {
      try {
        const currentToken = localStorage.getItem('token');
        if (!currentToken) {
          console.warn("⚠️ [Dashboard] No token found during fetch attempt");
          return;
        }
        const headers = { 'Authorization': `Bearer ${currentToken}` };
        const [statsRes, chartRes, alertsRes] = await Promise.all([
          fetch("http://localhost:8000/api/alerts/stats/", { headers }),
          fetch("http://localhost:8000/api/alerts/chart/", { headers }),
          fetch("http://localhost:8000/api/alerts/?limit=50", { headers })
        ]);

        if (statsRes.ok) setStats(await statsRes.json());
        if (chartRes.ok) setChartData(await chartRes.json());
        if (alertsRes.ok) setRecentAlerts(((await alertsRes.json()).items || []));
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      }
    };
    fetchInitialData();

    // 2. WebSocket Connection for Real-Time Updates
    let ws = null;
    let reconnectTimer = null;

    const connectWebSocket = () => {
      ws = new WebSocket("ws://localhost:8000/api/alerts/ws");

      ws.onopen = () => {
        console.log("✅ [Dashboard] Connected to WebSocket");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "new_alert") {
            const newAlert = data.payload;
            console.log("🔔 [Dashboard] New Alert:", newAlert);
            setStats(prev => ({ ...prev, active_alerts: prev.active_alerts + 1, recent_alerts: prev.recent_alerts + 1 }));
            setRecentAlerts(prev => [newAlert, ...prev].slice(0, 50));
          }
        } catch (e) {
          console.error("Error parsing WS message:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("❌ [Dashboard] WebSocket Error:", err);
      };

      ws.onclose = () => {
        console.log("⚠️ [Dashboard] WebSocket Closed. Reconnecting in 3s...");
        reconnectTimer = setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.onclose = null; // Prevent reconnect on unmount
        ws.close();
      }
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  const handleChartClick = (data) => {
    if (data && data.activePayload && data.activePayload.length > 0) {
      const item = data.activePayload[0].payload;
      if (item.timestamp) {
        const startDate = new Date(item.timestamp);
        const endDate = new Date(startDate.getTime() + 60 * 60 * 1000); // +1 hour
        navigate(`/alerts?start_time=${item.timestamp}&end_time=${endDate.toISOString()}`);
      }
    }
  };

  const handleExport = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/alerts/export", {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'alerts.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">Security Overview</h2>
          <p className="text-slate-400 mt-1">Real-time threat monitoring and system status.</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700"
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Alerts"
          value={stats.active_alerts}
          trend="up"
          trendValue="+2"
          icon={AlertOctagon}
          color="red"
        />
        <StatCard
          title="High Severity"
          value={stats.high_severity}
          trend="up"
          trendValue="+1"
          icon={Activity}
          color="yellow"
        />
        <StatCard
          title="Recent (24h)"
          value={stats.recent_alerts}
          trend="down"
          trendValue="-5%"
          icon={Shield}
          color="blue"
        />
        <StatCard
          title="System Health"
          value={`${stats.system_health}%`}
          trend="up"
          trendValue="Stable"
          icon={Users}
          color="green"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Chart Section */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl min-h-[400px]">
          <h3 className="text-lg font-bold text-[var(--foreground)] mb-6">Alert Volume (24h)</h3>
          <div className="h-[300px] w-full" style={{ minWidth: 0 }}>
            <ResponsiveContainer width="100%" height="100%" minHeight={300}>
              <AreaChart data={chartData} onClick={handleChartClick} className="cursor-pointer">
                <defs>
                  <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                  itemStyle={{ color: '#3b82f6' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Area
                  type="monotone"
                  dataKey="alerts"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorAlerts)"
                  activeDot={{ r: 6, strokeWidth: 0 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Alerts Section */}
        <div className="lg:col-span-1">
          <RecentAlerts />
        </div>

        {/* World Map Section */}
        <div className="lg:col-span-3 h-[400px]">
          <WorldMap alerts={recentAlerts} />
        </div>

      </div>
    </div>
  );
}
