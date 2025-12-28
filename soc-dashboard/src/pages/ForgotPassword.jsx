import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import { KeyRound, Mail, ArrowRight, CheckCircle } from "lucide-react";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [step, setStep] = useState(1); // 1: Email, 2: OTP
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const { setToken } = useAuth(); // We need to access setToken directly or add a method
    const navigate = useNavigate();

    const handleRequestOtp = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");
        try {
            const res = await fetch("http://localhost:8000/auth/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            if (!res.ok) throw new Error("Failed to send OTP");

            setMessage("OTP sent to your email.");
            setStep(2);
        } catch (err) {
            setError("Failed to send OTP. Please try again.");
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        setError("");
        try {
            const res = await fetch("http://localhost:8000/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, otp }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Invalid OTP");
            }

            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            // Force reload to pick up token in context or use a context method if available
            // Ideally useAuth should expose a method to set token manually
            window.location.href = "/";
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--background)] p-4 transition-colors duration-300">
            <div className="w-full max-w-md glass-panel p-8 rounded-2xl shadow-2xl">

                <div className="text-center mb-8">
                    <div className="inline-flex p-3 bg-blue-600/20 rounded-xl mb-4">
                        <KeyRound className="text-blue-500" size={40} />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Reset Password</h1>
                    <p className="text-slate-400 mt-2">
                        {step === 1 ? "Enter your email to receive an OTP" : "Enter the OTP sent to your email"}
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                        {error}
                    </div>
                )}

                {message && (
                    <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm text-center">
                        {message}
                    </div>
                )}

                {step === 1 ? (
                    <form onSubmit={handleRequestOtp} className="space-y-6">
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

                        <button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-500/25 active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            Send OTP <ArrowRight size={18} />
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleVerifyOtp} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-[var(--foreground)] mb-2">Enter OTP</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    required
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-center text-2xl tracking-widest text-white placeholder:text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                    placeholder="000000"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-green-500/25 active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            Verify & Login <CheckCircle size={18} />
                        </button>

                        <button
                            type="button"
                            onClick={() => setStep(1)}
                            className="w-full text-slate-400 hover:text-white text-sm mt-2"
                        >
                            Change Email
                        </button>
                    </form>
                )}

                <div className="mt-6 text-center">
                    <Link to="/login" className="text-sm text-slate-500 hover:text-blue-400 transition-colors">Back to Login</Link>
                </div>

            </div>
        </div>
    );
}
