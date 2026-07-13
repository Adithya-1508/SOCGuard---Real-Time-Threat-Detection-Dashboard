import { useEffect, useState } from "react";
import { AlertTriangle, Clock } from "lucide-react";
import clsx from "clsx";
import { formatDistanceToNow } from "date-fns";
import { Link } from "react-router-dom";
import AlertDetailsModal from "./AlertDetailsModal";
import { API_BASE_URL } from "../config";

export default function RecentAlerts() {
    const [alerts, setAlerts] = useState([]);
    const [selectedAlert, setSelectedAlert] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE_URL}/api/alerts/?limit=5`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
            .then(res => {
                if (res.ok) return res.json();
                throw new Error("Failed to fetch alerts");
            })
            .then(data => setAlerts(data.items || []))
            .catch(err => console.log("Using empty alerts", err));
    }, []);

    return (
        <>
            <div className="glass-panel rounded-2xl p-6 h-full">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-[var(--foreground)]">Recent Alerts</h3>
                    <Link to="/alerts" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">View All</Link>
                </div>

                <div className="space-y-4">
                    {alerts.length === 0 ? (
                        <p className="text-slate-500 text-center py-4">No recent alerts.</p>
                    ) : (
                        alerts.map((alert) => (
                            <div
                                key={alert.id}
                                onClick={() => setSelectedAlert(alert)}
                                className="flex items-start gap-4 p-3 rounded-xl hover:bg-slate-800/50 transition-colors border border-transparent hover:border-slate-700/50 cursor-pointer"
                            >
                                <div className={clsx(
                                    "mt-1 p-2 rounded-lg",
                                    alert.severity === "critical" && "bg-red-500/10 text-red-500",
                                    alert.severity === "high" && "bg-orange-500/10 text-orange-500",
                                    alert.severity === "medium" && "bg-yellow-500/10 text-yellow-500",
                                    alert.severity === "low" && "bg-blue-500/10 text-blue-500",
                                )}>
                                    <AlertTriangle size={18} />
                                </div>

                                <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-medium text-[var(--foreground)] truncate">{alert.summary}</h4>
                                    <p className="text-xs text-slate-400 mt-0.5">Source: {alert.source}</p>
                                </div>

                                <div className="flex flex-col items-end gap-1">
                                    <span className={clsx(
                                        "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full",
                                        alert.severity === "critical" && "bg-red-500/10 text-red-500",
                                        alert.severity === "high" && "bg-orange-500/10 text-orange-500",
                                        alert.severity === "medium" && "bg-yellow-500/10 text-yellow-500",
                                        alert.severity === "low" && "bg-blue-500/10 text-blue-500",
                                    )}>
                                        {alert.severity}
                                    </span>
                                    <span className="text-xs text-slate-500 flex items-center gap-1">
                                        <Clock size={10} />
                                        {alert.created_at ? formatDistanceToNow(new Date(alert.created_at), { addSuffix: true }) : 'Unknown'}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            <AlertDetailsModal
                alert={selectedAlert}
                onClose={() => setSelectedAlert(null)}
            />
        </>
    );
}
