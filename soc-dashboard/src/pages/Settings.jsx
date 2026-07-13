import { useState, useEffect } from "react";
import { Save, Server, Shield, Lock, Users, Clock, Globe } from "lucide-react";
import clsx from "clsx";
import { API_BASE_URL } from "../config";

export default function Settings() {
  const [activeTab, setActiveTab] = useState("system");
  const [settings, setSettings] = useState({
    system_name: "SOCGuard",
    version: "1.0.0",
    mode: "dev",
    timezone: "UTC",
    date_format: "YYYY-MM-DD HH:mm:ss",
    retention: "30",
    auth_2fa: false,
    auth_sso: false,
    password_reset: true,
    session_timeout: "30",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/settings/`)
      .then(res => res.json())
      .then(data => {
        if (Object.keys(data).length > 0) {
          setSettings(prev => ({ ...prev, ...data }));
        }
      })
      .catch(err => console.error("Failed to load settings", err));
  }, []);

  const handleSave = () => {
    setLoading(true);
    fetch(`${API_BASE_URL}/api/settings/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ settings })
    })
      .then(res => res.json())
      .then(() => {
        setTimeout(() => setLoading(false), 500);
      })
      .catch(err => {
        console.error("Failed to save", err);
        setLoading(false);
      });
  };

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const tabs = [
    { id: "system", label: "System Info", icon: Server },
    { id: "rbac", label: "RBAC", icon: Users },
    { id: "auth", label: "Authentication", icon: Lock },
  ];

  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">Settings</h2>
        <p className="text-slate-400 mt-1">Manage system configuration and security policies.</p>
      </div>

      <div className="flex gap-6 flex-col md:flex-row">
        {/* Sidebar Tabs */}
        <div className="w-full md:w-64 flex flex-col gap-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium text-left",
                activeTab === tab.id
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-[var(--foreground)]"
              )}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 glass-panel rounded-2xl p-8 min-h-[500px]">

          {/* System Info Tab */}
          {activeTab === "system" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <h3 className="text-xl font-bold text-[var(--foreground)] flex items-center gap-2 border-b border-[var(--border)] pb-4">
                <Server className="text-blue-500" /> System Information
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">System Name</label>
                  <input
                    type="text"
                    value={settings.system_name}
                    onChange={(e) => handleChange("system_name", e.target.value)}
                    className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">Version</label>
                  <input
                    type="text"
                    value={settings.version}
                    readOnly
                    className="w-full bg-slate-900/50 border border-[var(--border)] rounded-lg px-4 py-2 text-slate-500 cursor-not-allowed"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">Deployment Mode</label>
                  <select
                    value={settings.mode}
                    onChange={(e) => handleChange("mode", e.target.value)}
                    className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    <option value="dev">Development</option>
                    <option value="stage">Staging</option>
                    <option value="prod">Production</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">Log Retention (Days)</label>
                  <select
                    value={settings.retention}
                    onChange={(e) => handleChange("retention", e.target.value)}
                    className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  >
                    <option value="30">30 Days</option>
                    <option value="60">60 Days</option>
                    <option value="90">90 Days</option>
                    <option value="365">1 Year</option>
                  </select>
                </div>
              </div>

              <div className="pt-6 border-t border-[var(--border)]">
                <h4 className="text-sm font-bold text-[var(--foreground)] mb-4 flex items-center gap-2">
                  <Globe size={16} /> Localization
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-400">Timezone</label>
                    <select
                      value={settings.timezone}
                      onChange={(e) => handleChange("timezone", e.target.value)}
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    >
                      <option value="UTC">UTC</option>
                      <option value="EST">EST (New York)</option>
                      <option value="PST">PST (Los Angeles)</option>
                      <option value="IST">IST (India)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-400">Date Format</label>
                    <select
                      value={settings.date_format}
                      onChange={(e) => handleChange("date_format", e.target.value)}
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    >
                      <option value="YYYY-MM-DD HH:mm:ss">YYYY-MM-DD HH:mm:ss</option>
                      <option value="DD/MM/YYYY HH:mm">DD/MM/YYYY HH:mm</option>
                      <option value="MM/DD/YYYY HH:mm">MM/DD/YYYY HH:mm</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* RBAC Tab */}
          {activeTab === "rbac" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <h3 className="text-xl font-bold text-[var(--foreground)] flex items-center gap-2 border-b border-[var(--border)] pb-4">
                <Users className="text-purple-500" /> Role-Based Access Control
              </h3>

              <div className="space-y-4">
                {[
                  { role: "Admin", desc: "Full access to all system features and settings.", color: "text-red-400", bg: "bg-red-500/10" },
                  { role: "Analyst", desc: "Can view alerts, dashboard, and manage incidents.", color: "text-blue-400", bg: "bg-blue-500/10" },
                  { role: "Read-only", desc: "Can only view dashboards and reports.", color: "text-green-400", bg: "bg-green-500/10" },
                  { role: "API-only", desc: " programmatic access for integrations.", color: "text-yellow-400", bg: "bg-yellow-500/10" },
                ].map((role) => (
                  <div key={role.role} className="flex items-center justify-between p-4 rounded-xl border border-[var(--border)] bg-[var(--background)]">
                    <div className="flex items-center gap-4">
                      <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center font-bold", role.color, role.bg)}>
                        {role.role[0]}
                      </div>
                      <div>
                        <h4 className="font-bold text-[var(--foreground)]">{role.role}</h4>
                        <p className="text-sm text-slate-400">{role.desc}</p>
                      </div>
                    </div>
                    <button className="text-sm text-blue-400 hover:text-blue-300 font-medium">Edit Permissions</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Authentication Tab */}
          {activeTab === "auth" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
              <h3 className="text-xl font-bold text-[var(--foreground)] flex items-center gap-2 border-b border-[var(--border)] pb-4">
                <Lock className="text-orange-500" /> Authentication Settings
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl border border-[var(--border)] bg-[var(--background)]">
                  <div>
                    <h4 className="font-bold text-[var(--foreground)]">Two-Factor Authentication (2FA)</h4>
                    <p className="text-sm text-slate-400">Require 2FA for all admin accounts.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={settings.auth_2fa === 'true' || settings.auth_2fa === true}
                      onChange={(e) => handleChange("auth_2fa", e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl border border-[var(--border)] bg-[var(--background)]">
                  <div>
                    <h4 className="font-bold text-[var(--foreground)]">SSO Integration</h4>
                    <p className="text-sm text-slate-400">Enable Single Sign-On via SAML/OIDC.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={settings.auth_sso === 'true' || settings.auth_sso === true}
                      onChange={(e) => handleChange("auth_sso", e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--background)] space-y-4">
                  <h4 className="font-bold text-[var(--foreground)] flex items-center gap-2">
                    <Clock size={16} /> Session Policy
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-400">Session Timeout (Minutes)</label>
                      <input
                        type="number"
                        value={settings.session_timeout}
                        onChange={(e) => handleChange("session_timeout", e.target.value)}
                        className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg px-4 py-2 text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="mt-8 pt-6 border-t border-[var(--border)] flex justify-end">
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save size={18} />
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
