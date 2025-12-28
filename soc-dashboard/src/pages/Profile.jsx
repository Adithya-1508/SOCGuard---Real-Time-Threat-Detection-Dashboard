import { useAuth } from "../context/AuthContext";
import { User, Mail, Shield, Calendar, Edit } from "lucide-react";

export default function Profile() {
    const { user } = useAuth();

    if (!user) return null;

    return (
        <div className="max-w-4xl space-y-8 animate-in fade-in duration-500">
            <div>
                <h2 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">User Profile</h2>
                <p className="text-slate-400 mt-1">Manage your personal information and preferences.</p>
            </div>

            <div className="glass-panel rounded-2xl p-8 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-blue-600/20 to-purple-600/20"></div>

                <div className="relative flex flex-col md:flex-row items-start md:items-end gap-6 mt-12">
                    <div className="w-24 h-24 rounded-2xl bg-slate-900 border-4 border-[var(--card)] flex items-center justify-center shadow-xl">
                        <span className="text-4xl font-bold text-blue-500">{user.full_name?.charAt(0)}</span>
                    </div>
                    <div className="flex-1 mb-2">
                        <h3 className="text-2xl font-bold text-[var(--foreground)]">{user.full_name}</h3>
                        <p className="text-slate-400">{user.email}</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors mb-2">
                        <Edit size={16} /> Edit Profile
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400">
                            <User size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Full Name</p>
                            <p className="font-medium text-[var(--foreground)]">{user.full_name}</p>
                        </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400">
                            <Mail size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Email Address</p>
                            <p className="font-medium text-[var(--foreground)]">{user.email}</p>
                        </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-green-500/10 text-green-400">
                            <Shield size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Role</p>
                            <p className="font-medium text-[var(--foreground)] capitalize">{user.role || "Analyst"}</p>
                        </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-orange-500/10 text-orange-400">
                            <Calendar size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Member Since</p>
                            <p className="font-medium text-[var(--foreground)]">November 2025</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
