'use client';
import { getCongestionColor, getCongestionLabel } from '@/lib/mapConfig';
import { Activity, TrendingUp, AlertTriangle, Gauge } from 'lucide-react';

interface IntersectionCardProps {
    intersection: any;
    prediction?: any;
    onClick?: () => void;
}

export default function IntersectionCard({ intersection, prediction, onClick }: IntersectionCardProps) {
    const congestion = intersection?.congestion_percent || 0;
    const color = getCongestionColor(congestion);
    const label = getCongestionLabel(congestion);
    const speed = intersection?.current_speed_kmh || 0;
    const freeflow = intersection?.freeflow_speed_kmh || 50;
    const incidents = intersection?.active_incidents?.length || 0;

    return (
        <div
            onClick={onClick}
            className="rounded-xl bg-slate-800/60 border border-slate-700/50 p-4 hover:bg-slate-800/90 transition-all cursor-pointer group backdrop-blur-sm"
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-white truncate">
                        {intersection?.road_names?.[0] || 'Unknown'}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                        {intersection?.road_names?.[1] && `× ${intersection.road_names[1]}`}
                    </p>
                </div>
                <div
                    className="px-2 py-0.5 rounded-full text-xs font-bold"
                    style={{ backgroundColor: `${color}20`, color }}
                >
                    {label}
                </div>
            </div>

            {/* Congestion bar */}
            <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Congestion</span>
                    <span style={{ color }} className="font-mono font-bold">{congestion.toFixed(0)}%</span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(congestion, 100)}%`, backgroundColor: color }}
                    />
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-900/50 rounded-lg p-1.5">
                    <Gauge className="w-3 h-3 mx-auto mb-0.5 text-slate-400" />
                    <p className="text-xs font-mono text-white">{speed.toFixed(0)}</p>
                    <p className="text-[10px] text-slate-500">km/h</p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-1.5">
                    <TrendingUp className="w-3 h-3 mx-auto mb-0.5 text-slate-400" />
                    <p className="text-xs font-mono text-white">{freeflow.toFixed(0)}</p>
                    <p className="text-[10px] text-slate-500">free</p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-1.5">
                    <AlertTriangle className="w-3 h-3 mx-auto mb-0.5 text-slate-400" />
                    <p className="text-xs font-mono text-white">{incidents}</p>
                    <p className="text-[10px] text-slate-500">inc.</p>
                </div>
            </div>

            {prediction && (
                <div className="mt-2 pt-2 border-t border-slate-700/40 flex gap-2 text-[10px]">
                    <span className="text-slate-500">Forecast:</span>
                    <span className="text-yellow-400">15m: {prediction.forecast_15min?.toFixed(0)}%</span>
                    <span className="text-orange-400">30m: {prediction.forecast_30min?.toFixed(0)}%</span>
                    <span className="text-red-400">1h: {prediction.forecast_60min?.toFixed(0)}%</span>
                </div>
            )}
        </div>
    );
}
