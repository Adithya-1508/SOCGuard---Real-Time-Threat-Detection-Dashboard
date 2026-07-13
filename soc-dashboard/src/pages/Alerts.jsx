import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Filter, AlertTriangle, MoreVertical, ChevronLeft, ChevronRight, X } from "lucide-react";
import clsx from "clsx";
import AlertDetailsModal from "../components/AlertDetailsModal";
import { API_BASE_URL, WS_BASE_URL } from "../config";

export default function Alerts() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);

  // Filters
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [severity, setSeverity] = useState(searchParams.get("severity") || "");
  const [status, setStatus] = useState(searchParams.get("status") || "");
  const [source, setSource] = useState(searchParams.get("source") || "");
  const [showFilters, setShowFilters] = useState(false);

  // Sync state with URL
  useEffect(() => {
    const params = {};
    if (search) params.search = search;
    if (severity) params.severity = severity;
    if (status) params.status = status;
    if (source) params.source = source;
    if (searchParams.get("start_time")) params.start_time = searchParams.get("start_time");
    if (searchParams.get("end_time")) params.end_time = searchParams.get("end_time");
    setSearchParams(params);
  }, [search, severity, status, source]);

  useEffect(() => {
    setLoading(true);
    const skip = (page - 1) * limit;

    const params = new URLSearchParams({
      skip,
      limit,
      ...(search && { search }),
      ...(severity && { severity }),
      ...(status && { status }),
      ...(source && { source }),
      ...(searchParams.get("start_time") && { start_time: searchParams.get("start_time") }),
      ...(searchParams.get("end_time") && { end_time: searchParams.get("end_time") }),
    });

    fetch(`${API_BASE_URL}/api/alerts/?${params}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error("API not reachable");
      })
      .then(data => {
        setAlerts(data.items || []);
        setTotal(data.total || 0);
      })
      .catch(err => console.log("Using empty data", err))
      .finally(() => setLoading(false));
  }, [page, limit, search, severity, status, source, searchParams]);

  // WebSocket Connection
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/api/alerts/ws`);

    ws.onopen = () => {
      console.log("Connected to WebSocket");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "new_alert") {
          const newAlert = data.payload;
          // Only prepend if on the first page and matches current filters (basic check)
          if (page === 1 && !search && !severity && !status && !source) {
            setAlerts(prev => [newAlert, ...prev].slice(0, limit));
            setTotal(prev => prev + 1);
          }
        }
      } catch (e) {
        console.error("WS error:", e);
      }
    };

    return () => {
      ws.close();
    };
  }, [page, limit, search, severity, status, source]);

  const totalPages = Math.ceil(total / limit);

  const clearFilters = () => {
    setSearch("");
    setSeverity("");
    setStatus("");
    setSource("");
    setSearchParams({});
  };

  return (
    <>
      <div className="space-y-6 animate-in fade-in duration-500">

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">Alerts</h2>
            <p className="text-slate-400 mt-1">Manage and triage security incidents.</p>
          </div>

          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Search alerts..."
                className="bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] pl-10 pr-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 w-full md:w-64 placeholder:text-slate-500 transition-all"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                "p-2 border rounded-lg transition-colors",
                showFilters ? "bg-blue-600 border-blue-600 text-white" : "bg-[var(--card)] border-[var(--border)] text-slate-400 hover:text-[var(--foreground)]"
              )}
            >
              <Filter size={20} />
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-800/30 rounded-xl border border-[var(--border)] animate-in slide-in-from-top-2">
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            >
              <option value="">All Statuses</option>
              <option value="Open">Open</option>
              <option value="Investigating">Investigating</option>
              <option value="Resolved">Resolved</option>
              <option value="Closed">Closed</option>
            </select>

            <input
              type="text"
              placeholder="Source (e.g. Firewall)"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />

            <button onClick={clearFilters} className="flex items-center justify-center gap-2 text-slate-400 hover:text-white transition-colors">
              <X size={16} /> Clear Filters
            </button>
          </div>
        )}

        <div className="glass-panel rounded-xl overflow-hidden flex flex-col shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] bg-slate-800/30 text-slate-400 text-sm uppercase tracking-wider">
                  <th className="p-4 font-medium">Severity</th>
                  <th className="p-4 font-medium">ID</th>
                  <th className="p-4 font-medium">Source</th>
                  <th className="p-4 font-medium">IP Address</th>
                  <th className="p-4 font-medium">Threat</th>
                  <th className="p-4 font-medium">Summary</th>
                  <th className="p-4 font-medium">Status</th>
                  <th className="p-4 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {loading ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-slate-500">
                      <div className="flex justify-center items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        Loading alerts...
                      </div>
                    </td>
                  </tr>
                ) : alerts.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-slate-500">No alerts found matching your criteria.</td>
                  </tr>
                ) : (
                  alerts.map((a) => (
                    <tr
                      key={a.id}
                      onClick={() => setSelectedAlert(a)}
                      className="hover:bg-slate-800/30 transition-colors group cursor-pointer"
                    >
                      <td className="p-4">
                        <div className={clsx(
                          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide",
                          a.severity === "critical" && "bg-red-500/10 text-red-500 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.2)]",
                          a.severity === "high" && "bg-orange-500/10 text-orange-500 border border-orange-500/20",
                          a.severity === "medium" && "bg-yellow-500/10 text-yellow-500 border border-yellow-500/20",
                          a.severity === "low" && "bg-blue-500/10 text-blue-500 border border-blue-500/20",
                        )}>
                          <AlertTriangle size={12} />
                          {a.severity}
                        </div>
                      </td>
                      <td className="p-4 text-slate-400 font-mono text-sm">#{a.id}</td>
                      <td className="p-4 text-slate-400">{a.source}</td>
                      <td className="p-4 text-slate-400 font-mono text-sm">{a.ip}</td>
                      <td className="p-4">
                        {a.reputation_score > 0 ? (
                          <span className={clsx(
                            "px-2 py-1 rounded text-xs font-bold",
                            a.reputation_score > 80 ? "bg-red-500/20 text-red-500" : "bg-orange-500/20 text-orange-500"
                          )}>
                            {a.reputation_score}
                          </span>
                        ) : (
                          <span className="text-slate-600 text-xs">-</span>
                        )}
                      </td>
                      <td className="p-4 text-[var(--foreground)] font-medium">{a.summary}</td>
                      <td className="p-4">
                        <span className={clsx(
                          "px-2 py-1 rounded text-xs font-medium",
                          a.status === "Open" && "bg-red-500/10 text-red-400",
                          a.status === "Investigating" && "bg-yellow-500/10 text-yellow-400",
                          a.status === "Resolved" && "bg-green-500/10 text-green-400",
                          a.status === "Closed" && "bg-slate-700 text-slate-400",
                        )}>
                          {a.status}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <button className="p-1 text-slate-500 hover:text-[var(--foreground)] transition-colors opacity-0 group-hover:opacity-100">
                          <MoreVertical size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="p-4 border-t border-[var(--border)] flex items-center justify-between bg-slate-800/30">
            <div className="text-sm text-slate-400">
              Showing <span className="font-medium text-[var(--foreground)]">{alerts.length > 0 ? (page - 1) * limit + 1 : 0}</span> to <span className="font-medium text-[var(--foreground)]">{Math.min(page * limit, total)}</span> of <span className="font-medium text-[var(--foreground)]">{total}</span> results
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="p-2 rounded-lg border border-[var(--border)] text-slate-400 hover:text-[var(--foreground)] hover:bg-[var(--card)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm font-medium text-[var(--foreground)] px-2">
                Page {page} of {totalPages || 1}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || loading}
                className="p-2 rounded-lg border border-[var(--border)] text-slate-400 hover:text-[var(--foreground)] hover:bg-[var(--card)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <AlertDetailsModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
      />
    </>
  );
}
