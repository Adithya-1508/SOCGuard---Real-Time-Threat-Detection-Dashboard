import { useState } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[var(--background)] text-[var(--foreground)] font-sans transition-colors duration-300">

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-[var(--card)] backdrop-blur-md border-b border-[var(--border)] flex items-center justify-between px-4 z-50">
        <span className="font-bold text-xl tracking-tight text-blue-500">SOCGUARD</span>
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="p-2 rounded-lg hover:bg-slate-800/10 transition-colors text-[var(--foreground)]"
        >
          <Menu size={24} />
        </button>
      </div>

      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 pt-20 md:pt-8 overflow-x-hidden w-full max-w-[1600px] mx-auto">
        {children}
      </main>
    </div>
  );
}
