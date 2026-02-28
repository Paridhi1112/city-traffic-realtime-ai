import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'Urban Traffic Brain',
    description: 'AI-Powered City-Wide Traffic Management System',
};

const navLinks = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/map', label: 'Live Map', icon: '🗺️' },
    { href: '/decisions', label: 'AI Decisions', icon: '🧠' },
    { href: '/emissions', label: 'Emissions', icon: '🌿' },
    { href: '/events', label: 'Events', icon: '📅' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className="dark">
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
            </head>
            <body className="bg-slate-950 text-slate-100 font-sans antialiased">
                <div className="flex h-screen overflow-hidden">
                    {/* Sidebar */}
                    <aside className="w-16 lg:w-56 bg-slate-900/80 border-r border-slate-800/50 flex flex-col shrink-0 backdrop-blur-xl">
                        <div className="p-3 lg:p-4 border-b border-slate-800/50">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-bold text-white shadow-lg shadow-cyan-500/20">
                                    TB
                                </div>
                                <div className="hidden lg:block">
                                    <p className="text-sm font-bold text-white leading-tight">Traffic Brain</p>
                                    <p className="text-[10px] text-cyan-400">AI Powered</p>
                                </div>
                            </div>
                        </div>
                        <nav className="flex-1 p-2 space-y-1">
                            {navLinks.map((link) => (
                                <a
                                    key={link.href}
                                    href={link.href}
                                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all group"
                                >
                                    <span className="text-base">{link.icon}</span>
                                    <span className="hidden lg:block text-sm font-medium">{link.label}</span>
                                </a>
                            ))}
                        </nav>
                        <div className="p-3 border-t border-slate-800/50">
                            <div className="hidden lg:flex items-center gap-2 px-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[10px] text-slate-500">System Active</span>
                            </div>
                        </div>
                    </aside>

                    {/* Main Content */}
                    <main className="flex-1 overflow-y-auto">
                        {children}
                    </main>
                </div>
            </body>
        </html>
    );
}
