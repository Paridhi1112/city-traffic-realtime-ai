'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

export default function DataSourceStatus() {
    const [status, setStatus] = useState<any>(null);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const data = await api.getDatasourceStatus();
                setStatus(data);
            } catch (e) {
                console.error('Failed to fetch datasource status:', e);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const sources = status ? Object.entries(status) : [];

    const statusColor = (s: string) => {
        switch (s) {
            case 'ok': return 'text-emerald-400 bg-emerald-500/10';
            case 'simulated': return 'text-yellow-400 bg-yellow-500/10';
            case 'cached': return 'text-blue-400 bg-blue-500/10';
            case 'error': return 'text-red-400 bg-red-500/10';
            default: return 'text-slate-400 bg-slate-500/10';
        }
    };

    const statusIcon = (s: string) => {
        switch (s) {
            case 'ok': return <Wifi className="w-3 h-3" />;
            case 'simulated': return <RefreshCw className="w-3 h-3" />;
            case 'cached': return <RefreshCw className="w-3 h-3" />;
            default: return <WifiOff className="w-3 h-3" />;
        }
    };

    const formatName = (name: string) => {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    return (
        <div className="rounded-xl bg-slate-800/50 border border-slate-700/30 p-4">
            <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Data Sources</h3>
            <div className="grid grid-cols-2 gap-2">
                {sources.map(([name, info]: [string, any]) => (
                    <div key={name} className={`flex items-center gap-2 px-2 py-1.5 rounded-lg ${statusColor(info?.status)}`}>
                        {statusIcon(info?.status)}
                        <span className="text-[11px] font-medium">{formatName(name)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
