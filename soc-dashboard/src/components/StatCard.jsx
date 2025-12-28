import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import clsx from "clsx";

export default function StatCard({ title, value, trend, trendValue, icon: Icon, color }) {
    const isPositive = trend === "up";

    const colorStyles = {
        blue: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        green: "bg-green-500/10 text-green-500 border-green-500/20",
        yellow: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
        red: "bg-red-500/10 text-red-500 border-red-500/20",
    };

    return (
        <div className="glass-panel p-6 rounded-2xl hover:border-slate-600/50 transition-colors">
            <div className="flex justify-between items-start mb-4">
                <div className={clsx("p-3 rounded-xl border", colorStyles[color])}>
                    <Icon size={24} />
                </div>
                {trendValue && (
                    <div className={clsx(
                        "flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-lg",
                        isPositive ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"
                    )}>
                        {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        {trendValue}
                    </div>
                )}
            </div>

            <h3 className="text-slate-400 text-sm font-medium mb-1">{title}</h3>
            <p className="text-3xl font-bold text-[var(--foreground)] tracking-tight">{value}</p>
        </div>
    );
}
