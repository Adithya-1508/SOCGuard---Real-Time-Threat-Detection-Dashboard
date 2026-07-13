import { useState, useEffect } from "react";
import { X, AlertTriangle, Clock, Server, Activity, CheckCircle, Play, User, MessageSquare, Send, Shield, Brain } from "lucide-react";
import clsx from "clsx";
import { formatDistanceToNow } from "date-fns";
import { API_BASE_URL } from "../config";

export default function AlertDetailsModal({ alert, onClose }) {
    const [investigating, setInvestigating] = useState(false);
    const [users, setUsers] = useState([]);
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState("");
    const [assignee, setAssignee] = useState("");
    const [activeRightTab, setActiveRightTab] = useState("case");
    const [copilotMessages, setCopilotMessages] = useState([]);
    const [copilotInput, setCopilotInput] = useState("");
    const [copilotLoading, setCopilotLoading] = useState(false);

    useEffect(() => {
        setAssignee(alert?.assigned_to || "");
        if (alert) {
            setCopilotMessages([
                {
                    role: "assistant",
                    content: `Hi! I am your AI Security Copilot. I have retrieved a matching security playbook for this alert. Ask me how to proceed with this investigation.`
                }
            ]);
            setCopilotInput("");
        }
    }, [alert]);

    useEffect(() => {
        if (alert) {
            // Fetch Users
            fetch(`${API_BASE_URL}/auth/users`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            })
                .then(res => {
                    if (!res.ok) throw new Error("Fetch failed");
                    return res.json();
                })
                .then(data => setUsers(Array.isArray(data) ? data : []))
                .catch(err => {
                    console.error("Failed to fetch users", err);
                    setUsers([]);
                });

            // Fetch Comments
            fetch(`${API_BASE_URL}/api/alerts/${alert.id}/comments`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            })
                .then(res => res.json())
                .then(data => setComments(data))
                .catch(err => console.error("Failed to fetch comments", err));
        }
    }, [alert]);

    if (!alert) return null;

    // Parse details if it's a string
    let details = {};
    try {
        details = typeof alert.details === 'string' ? JSON.parse(alert.details) : alert.details;
    } catch (e) {
        details = { raw: alert.details };
    }

    const handleInvestigate = async () => {
        setInvestigating(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/alerts/${alert.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ status: 'Investigating' })
            });

            if (res.ok) {
                onClose();
            }
        } catch (error) {
            console.error("Failed to investigate:", error);
        } finally {
            setInvestigating(false);
        }
    };

    const handleAssign = async (userId) => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/alerts/${alert.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ assigned_to: userId })
            });
            if (res.ok) {
                setAssignee(userId);
            }
        } catch (error) {
            console.error("Failed to assign:", error);
        }
    };

    const handleAddComment = async (e) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/alerts/${alert.id}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ content: newComment })
            });

            if (res.ok) {
                const comment = await res.json();
                // Optimistically add user name if we know it (current user)
                // For now, re-fetch or just append with "You"
                setComments([...comments, { ...comment, user_name: "You" }]);
                setNewComment("");
            }
        } catch (error) {
            console.error("Failed to add comment:", error);
        }
    };

    const handleAction = async (action) => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/alerts/${alert.id}/actions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ action })
            });

            if (res.ok) {
                const data = await res.json();
                // Refresh comments to show the system action
                fetch(`${API_BASE_URL}/api/alerts/${alert.id}/comments`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                })
                    .then(res => res.json())
                    .then(data => setComments(data));

                alert("Action executed: " + data.message);
            }
        } catch (error) {
            console.error("Failed to execute action:", error);
        }
    };

    const handleCopilotSend = async (e) => {
        e.preventDefault();
        if (!copilotInput.trim() || copilotLoading) return;

        const userMsg = { role: "user", content: copilotInput };
        setCopilotMessages(prev => [...prev, userMsg]);
        setCopilotInput("");
        setCopilotLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/copilot/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    alert_id: alert.id,
                    message: userMsg.content,
                    history: copilotMessages.map(m => ({ role: m.role, content: m.content }))
                })
            });

            if (res.ok) {
                const data = await res.json();
                setCopilotMessages(prev => [...prev, { role: "assistant", content: data.response }]);
            } else {
                setCopilotMessages(prev => [...prev, { role: "assistant", content: "Error: Copilot was unable to answer." }]);
            }
        } catch (err) {
            console.error("Copilot Chat Error:", err);
            setCopilotMessages(prev => [...prev, { role: "assistant", content: "Failed to connect to Copilot." }]);
        } finally {
            setCopilotLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
            <div className="w-full max-w-4xl glass-panel rounded-2xl shadow-2xl animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]" onClick={(e) => e.stopPropagation()}>

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-[var(--border)] shrink-0">
                    <div className="flex items-center gap-4">
                        <div className={clsx(
                            "p-3 rounded-xl",
                            alert.severity === "critical" && "bg-red-500/10 text-red-500",
                            alert.severity === "high" && "bg-orange-500/10 text-orange-500",
                            alert.severity === "medium" && "bg-yellow-500/10 text-yellow-500",
                            alert.severity === "low" && "bg-blue-500/10 text-blue-500",
                        )}>
                            <AlertTriangle size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-[var(--foreground)]">Alert Details</h2>
                            <p className="text-slate-400 text-sm">ID: {alert.id}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-[var(--foreground)] transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex flex-1 overflow-hidden">
                    {/* Left Column: Details */}
                    <div className="flex-1 p-6 space-y-6 overflow-y-auto border-r border-[var(--border)]">

                        {/* Summary */}
                        <div>
                            <h3 className="text-sm font-medium text-slate-400 mb-2">Summary</h3>
                            <p className="text-lg font-medium text-[var(--foreground)]">{alert.summary}</p>
                        </div>

                        {/* AI Explanation */}
                        {alert.explanation && (
                            <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
                                <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                                    <Shield size={14} /> AI Anomaly Explanation
                                </h4>
                                <p className="text-sm text-slate-300 italic">"{alert.explanation}"</p>
                            </div>
                        )}

                        {/* Deep Multi-Agent Report */}
                        {alert.agent_report && (
                            <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/20">
                                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                                    <Brain size={14} /> Autonomous Investigation Report
                                </h4>
                                <div className="text-sm text-slate-300 prose prose-invert max-w-none font-sans overflow-x-auto whitespace-pre-wrap bg-slate-950 p-3 rounded-lg border border-slate-800">
                                    {alert.agent_report}
                                </div>
                            </div>
                        )}

                        {/* Grid Details */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 rounded-lg bg-[var(--card)] border border-[var(--border)]">
                                <span className="text-xs text-slate-400 block mb-1">Severity</span>
                                <span className={clsx(
                                    "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase",
                                    alert.severity === "critical" && "bg-red-500/10 text-red-500",
                                    alert.severity === "high" && "bg-orange-500/10 text-orange-500",
                                    alert.severity === "medium" && "bg-yellow-500/10 text-yellow-500",
                                    alert.severity === "low" && "bg-blue-500/10 text-blue-500",
                                )}>{alert.severity}</span>
                            </div>
                            <div className="p-3 rounded-lg bg-[var(--card)] border border-[var(--border)]">
                                <span className="text-xs text-slate-400 block mb-1">Source</span>
                                <span className="text-sm font-mono text-[var(--foreground)]">{alert.source}</span>
                            </div>
                            <div className="p-3 rounded-lg bg-[var(--card)] border border-[var(--border)]">
                                <span className="text-xs text-slate-400 block mb-1">Time</span>
                                <span className="text-sm text-[var(--foreground)]">
                                    {(() => {
                                        try {
                                            return alert.created_at ? formatDistanceToNow(new Date(alert.created_at), { addSuffix: true }) : 'N/A';
                                        } catch (e) {
                                            console.error("Invalid date:", alert.created_at);
                                            return 'Invalid Date';
                                        }
                                    })()}
                                </span>
                            </div>
                            <div className="p-3 rounded-lg bg-[var(--card)] border border-[var(--border)]">
                                <span className="text-xs text-slate-400 block mb-1">IP Address</span>
                                <span className="text-sm font-mono text-[var(--foreground)]">{alert.ip || 'N/A'}</span>
                            </div>
                        </div>

                        {/* Threat Intel */}
                        <div>
                            <h3 className="text-sm font-medium text-slate-400 mb-2">Threat Intelligence</h3>
                            <div className="p-4 rounded-xl bg-[var(--card)] border border-[var(--border)] flex items-center gap-4">
                                <div className="relative w-16 h-16 flex items-center justify-center">
                                    <svg className="w-full h-full transform -rotate-90">
                                        <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-800" />
                                        <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" strokeDasharray={175.9} strokeDashoffset={175.9 - (175.9 * (alert.reputation_score || 0)) / 100} className={clsx((alert.reputation_score || 0) > 80 ? "text-red-500" : "text-green-500")} />
                                    </svg>
                                    <span className="absolute text-sm font-bold text-[var(--foreground)]">{alert.reputation_score ?? '-'}</span>
                                </div>
                                <div className="flex-1">
                                    <div className="flex flex-wrap gap-2">
                                        {(() => {
                                            try {
                                                if (!alert.threat_tags) return <span className="text-xs text-slate-500">No tags</span>;

                                                let tags = alert.threat_tags;
                                                if (typeof tags === 'string') {
                                                    if (tags.startsWith('[') || tags.startsWith('{')) {
                                                        tags = JSON.parse(tags);
                                                    } else {
                                                        tags = [tags];
                                                    }
                                                }

                                                if (!Array.isArray(tags)) tags = [tags];

                                                return tags.map((tag, i) => (
                                                    <span key={i} className="px-2 py-1 rounded bg-slate-800 text-xs text-slate-300">{tag}</span>
                                                ));
                                            } catch (e) {
                                                console.error("Failed to parse threat_tags:", alert.threat_tags);
                                                return <span className="text-xs text-slate-500">Error parsing tags</span>;
                                            }
                                        })()}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Raw Details */}
                        <div>
                            <h3 className="text-sm font-medium text-slate-400 mb-2">Raw Data</h3>
                            <div className="rounded-lg bg-slate-950 border border-[var(--border)] p-3 overflow-x-auto">
                                <pre className="text-xs font-mono text-slate-400">{JSON.stringify(details, null, 2)}</pre>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Case Management & Copilot */}
                    <div className="w-80 p-6 bg-slate-900/20 flex flex-col gap-4 border-l border-[var(--border)]">
                        
                        {/* Tab Switcher */}
                        <div className="flex border-b border-[var(--border)] shrink-0">
                            <button
                                onClick={() => setActiveRightTab("case")}
                                className={clsx(
                                    "flex-1 pb-2 text-sm font-medium border-b-2 transition-colors",
                                    activeRightTab === "case" ? "text-blue-500 border-blue-500" : "text-slate-400 border-transparent hover:text-slate-200"
                                )}
                            >
                                Case
                            </button>
                            <button
                                onClick={() => setActiveRightTab("copilot")}
                                className={clsx(
                                    "flex-1 pb-2 text-sm font-medium border-b-2 transition-colors flex items-center justify-center gap-2",
                                    activeRightTab === "copilot" ? "text-purple-500 border-purple-500" : "text-slate-400 border-transparent hover:text-slate-200"
                                )}
                            >
                                <Brain size={14} /> AI Copilot
                            </button>
                        </div>

                        {activeRightTab === "case" ? (
                            <div className="flex-1 flex flex-col gap-6 min-h-0">
                                {/* Assignee */}
                                <div>
                                    <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                                        <User size={14} /> Assignee
                                    </h3>
                                    <select
                                        value={assignee}
                                        onChange={(e) => handleAssign(e.target.value)}
                                        className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">Unassigned</option>
                                        {Array.isArray(users) && users.map(u => (
                                            <option key={u.id} value={u.id}>{u.full_name || u.email}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Comments */}
                                <div className="flex-1 flex flex-col min-h-0">
                                    <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                                        <MessageSquare size={14} /> Comments
                                    </h3>
                                    <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2">
                                        {comments.length === 0 ? (
                                            <div className="text-center py-8 text-slate-500 text-xs">No comments yet.</div>
                                        ) : (
                                            comments.map(c => (
                                                <div key={c.id} className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-3">
                                                    <div className="flex justify-between items-start mb-1">
                                                        <span className="text-xs font-bold text-blue-400">{c.user_name || 'User'}</span>
                                                        <span className="text-[10px] text-slate-500">
                                                            {(() => {
                                                                try {
                                                                    return formatDistanceToNow(new Date(c.created_at), { addSuffix: true });
                                                                } catch (e) {
                                                                    return 'unknown time';
                                                                }
                                                            })()}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-slate-300">{c.content}</p>
                                                </div>
                                            ))
                                        )}
                                    </div>

                                    <form onSubmit={handleAddComment} className="relative">
                                        <input
                                            type="text"
                                            value={newComment}
                                            onChange={(e) => setNewComment(e.target.value)}
                                            placeholder="Add a note..."
                                            className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg pl-3 pr-10 py-2 text-sm text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                        <button
                                            type="submit"
                                            disabled={!newComment.trim()}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-500 disabled:opacity-50"
                                        >
                                            <Send size={16} />
                                        </button>
                                    </form>
                                </div>

                                {/* Actions */}
                                <div className="pt-4 border-t border-[var(--border)] space-y-3 shrink-0">
                                    {alert.status !== 'Investigating' && alert.status !== 'Resolved' && (
                                        <button
                                            onClick={handleInvestigate}
                                            disabled={investigating}
                                            className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-lg shadow-blue-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            {investigating ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> : <Play size={16} />}
                                            Start Investigation
                                        </button>
                                    )}

                                    <button
                                        onClick={() => handleAction('investigate')}
                                        className="w-full py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/30 font-medium transition-all flex items-center justify-center gap-2"
                                    >
                                        <Brain size={16} /> Run Multi-Agent Audit
                                    </button>

                                    <button
                                        onClick={() => handleAction('block_ip')}
                                        className="w-full py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 font-medium transition-all flex items-center justify-center gap-2"
                                    >
                                        <Activity size={16} />
                                        Block IP Address
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col min-h-0">
                                <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2">
                                    {copilotMessages.map((m, idx) => (
                                        <div
                                            key={idx}
                                            className={clsx(
                                                "p-3 rounded-lg border text-sm max-w-[90%]",
                                                m.role === "user"
                                                    ? "bg-blue-600/10 border-blue-500/20 text-slate-100 ml-auto"
                                                    : "bg-purple-600/10 border-purple-500/20 text-slate-200"
                                            )}
                                        >
                                            <span className="text-[10px] font-bold block mb-1 uppercase tracking-wider text-slate-400">
                                                {m.role === "user" ? "Analyst" : "Copilot"}
                                            </span>
                                            <p className="whitespace-pre-wrap">{m.content}</p>
                                        </div>
                                    ))}
                                    {copilotLoading && (
                                        <div className="p-3 rounded-lg bg-purple-600/10 border border-purple-500/20 text-sm max-w-[90%] animate-pulse">
                                            <span className="text-[10px] font-bold block mb-1 uppercase tracking-wider text-slate-400">Copilot</span>
                                            <p className="text-xs text-slate-400">Thinking...</p>
                                        </div>
                                    )}
                                </div>

                                <form onSubmit={handleCopilotSend} className="relative mt-auto shrink-0">
                                    <input
                                        type="text"
                                        value={copilotInput}
                                        onChange={(e) => setCopilotInput(e.target.value)}
                                        placeholder="Ask Copilot about this threat..."
                                        className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg pl-3 pr-10 py-2 text-sm text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button
                                        type="submit"
                                        disabled={!copilotInput.trim() || copilotLoading}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-purple-500 disabled:opacity-50"
                                    >
                                        <Send size={16} />
                                    </button>
                                </form>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
