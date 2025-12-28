import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-[var(--background)] flex items-center justify-center p-6">
                    <div className="max-w-md w-full glass-panel p-8 rounded-2xl shadow-2xl text-center space-y-6 animate-in fade-in zoom-in-95 duration-300">
                        <div className="inline-flex items-center justify-center p-4 rounded-full bg-red-500/10 text-red-500 mb-2">
                            <AlertCircle size={48} />
                        </div>
                        <div className="space-y-2">
                            <h1 className="text-2xl font-bold text-[var(--foreground)]">Something went wrong</h1>
                            <p className="text-slate-400">
                                The application encountered an unexpected error. This has been logged for review.
                            </p>
                        </div>

                        {import.meta.env.DEV && (
                            <div className="text-left bg-slate-950 p-4 rounded-lg border border-[var(--border)] overflow-auto max-h-48">
                                <pre className="text-xs font-mono text-red-400">
                                    {this.state.error?.toString()}
                                </pre>
                            </div>
                        )}

                        <button
                            onClick={() => window.location.reload()}
                            className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
                        >
                            <RefreshCw size={18} />
                            Reload Application
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
