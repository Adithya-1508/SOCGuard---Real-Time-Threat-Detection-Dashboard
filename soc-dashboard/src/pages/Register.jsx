import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import { UserPlus, Mail, Lock, User } from "lucide-react";

export default function Register() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [error, setError] = useState("");
    const { login } = useAuth(); // We'll auto-login after register
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        try {
            const res = await fetch("http://localhost:8000/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, full_name: fullName }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Registration failed");
            }

            // Auto login
            await login(email, password);
            navigate("/");
        } catch (err) {
            setError(err.message);
        }
    };

    const handleGoogleLogin = async () => {
        const res = await fetch("http://localhost:8000/auth/google/login");
        const data = await res.json();
        window.location.href = data.url;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--background)] p-4 transition-colors duration-300">
            <div className="w-full max-w-md glass-panel p-8 rounded-2xl shadow-2xl">

                <div className="text-center mb-8">
                    <div className="inline-flex p-3 bg-blue-600/20 rounded-xl mb-4">
                        <UserPlus className="text-blue-500" size={40} />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Create Account</h1>
                    <p className="text-slate-400 mt-2">Join the SOC Dashboard</p>
                </div>

                {error && (
                    <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-[var(--foreground)] mb-2">Full Name</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="text"
                                required
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                placeholder="John Doe"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--foreground)] mb-2">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="email"
                                required
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                placeholder="admin@soc.local"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--foreground)] mb-2">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="password"
                                required
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-500/25 active:scale-[0.98]"
                    >
                        Sign Up
                    </button>
                </form>

                <div className="mt-6">
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-700"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-[var(--card)] text-slate-400">Or continue with</span>
                        </div>
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        className="mt-4 w-full flex items-center justify-center gap-3 bg-white text-slate-900 font-bold py-3 rounded-xl hover:bg-slate-100 transition-all active:scale-[0.98]"
                    >
                        <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
                        Sign up with Google
                    </button>
                </div>

                <div className="mt-6 text-center">
                    <p className="text-slate-400 text-sm">
                        Already have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">Sign In</Link>
                    </p>
                </div>

            </div>
        </div>
    );
}
