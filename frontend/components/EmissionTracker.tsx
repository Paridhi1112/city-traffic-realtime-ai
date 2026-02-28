'use client';
import { Leaf, TrendingDown, TrendingUp, Factory } from 'lucide-react';

interface EmissionTrackerProps {
    emissions?: any;
}

export default function EmissionTracker({ emissions }: EmissionTrackerProps) {
    const rate = emissions?.current_emission_rate_kg_hr || 0;
    const baseline = emissions?.baseline_kg_hr || 1200;
    const vsBaseline = emissions?.vs_baseline_percent || 0;
    const isAbove = vsBaseline > 0;

    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-bold text-white">Emissions</h2>
            </div>

            <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center">
                        <p className="text-2xl font-bold text-white font-mono">{rate}</p>
                        <p className="text-xs text-slate-400">kg CO₂/hr</p>
                    </div>
                    <div className="text-center">
                        <div className={`flex items-center justify-center gap-1 text-lg font-bold ${isAbove ? 'text-red-400' : 'text-emerald-400'}`}>
                            {isAbove ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {Math.abs(vsBaseline).toFixed(1)}%
                        </div>
                        <p className="text-xs text-slate-400">vs baseline</p>
                    </div>
                </div>

                {/* Emission bar */}
                <div className="mb-3">
                    <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-slate-500">Baseline: {baseline} kg/hr</span>
                        <span className={isAbove ? 'text-red-400' : 'text-emerald-400'}>Current: {rate} kg/hr</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden relative">
                        <div className="absolute h-full bg-slate-600 rounded-full" style={{ width: `${(baseline / Math.max(rate, baseline) * 100)}%` }} />
                        <div
                            className={`absolute h-full rounded-full transition-all duration-500 ${isAbove ? 'bg-red-500' : 'bg-emerald-500'}`}
                            style={{ width: `${(rate / Math.max(rate, baseline) * 100)}%` }}
                        />
                    </div>
                </div>

                {/* Top emitters */}
                {emissions?.top_emitters && (
                    <div className="mt-3 pt-3 border-t border-slate-700/30">
                        <p className="text-[10px] text-slate-500 uppercase font-semibold mb-2">Top Emitters</p>
                        {emissions.top_emitters.slice(0, 3).map((e: any, i: number) => (
                            <div key={i} className="flex items-center justify-between text-xs py-1">
                                <span className="text-slate-300 truncate flex-1 mr-2">
                                    <Factory className="w-3 h-3 inline mr-1 text-slate-500" />
                                    {e.road_names?.[0] || 'Unknown'}
                                </span>
                                <span className="text-red-400 font-mono">{e.estimated_co2_kg_hr} kg/hr</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
