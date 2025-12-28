import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Bell, Settings, X, LogOut, Moon, Sun, Shield } from "lucide-react";
import clsx from "clsx";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const links = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Alerts", path: "/alerts", icon: Bell },
    { name: "Settings", path: "/settings", icon: Settings },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={clsx(
        "fixed inset-y-0 left-0 z-50 w-64 bg-[var(--card)] border-r border-[var(--border)] transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:h-screen flex flex-col",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-xl shadow-lg shadow-blue-500/20">
              <Shield size={24} className="text-white" />
            </div>
            <h1 className="text-xl font-bold text-[var(--foreground)] tracking-wider">SOC<span className="text-blue-500">GUARD</span></h1>
          </div>
          <button onClick={onClose} className="md:hidden text-slate-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <nav className="p-4 space-y-2 flex-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => onClose && onClose()}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium",
                  isActive
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                )}
              >
                <Icon size={20} />
                {link.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[var(--border)] space-y-4">

          {/* User Profile */}
          {user && (
            <Link to="/profile" className="flex items-center gap-3 px-3 py-2 rounded-xl bg-[var(--background)] border border-[var(--border)] hover:bg-slate-800/50 transition-colors group">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--foreground)] truncate group-hover:text-blue-400 transition-colors">{user.full_name || "User"}</p>
                <p className="text-xs text-slate-400 truncate">{user.email || "user@example.com"}</p>
              </div>
            </Link>
          )}

          <button
            onClick={toggleTheme}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-800/50 hover:text-[var(--foreground)] transition-all duration-200 font-medium"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>

          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all duration-200 font-medium"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>
    </>
  );
}
