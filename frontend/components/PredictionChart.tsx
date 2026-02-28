'use client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart, Area } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface PredictionChartProps {
    cityState?: any;
    predictions?: any[];
}

export default function PredictionChart({ cityState, predictions }: PredictionChartProps) {
    // Build chart data from intersections — top 10 by congestion
    const intersections = cityState?.intersections || [];
    const topIntersections = [...intersections]
        .sort((a: any, b: any) => (b.congestion_percent || 0) - (a.congestion_percent || 0))
        .slice(0, 10);

    const chartData = topIntersections.map((inter: any) => ({
        name: (inter.road_names?.[0] || 'Unknown').substring(0, 15),
        current: Math.round(inter.congestion_percent || 0),
        speed: Math.round(inter.current_speed_kmh || 0),
        jam: Math.round((inter.jam_factor || 0) * 10),
    }));

    // Time series for predictions
    const predData = predictions ? predictions.slice(0, 8).map((p: any, i: number) => ({
        name: `Int ${i + 1}`,
        'T+15min': Math.round(p.forecast_15min || 0),
        'T+30min': Math.round(p.forecast_30min || 0),
        'T+60min': Math.round(p.forecast_60min || 0),
    })) : [];

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-400" />
                <h2 className="text-lg font-bold text-white">Congestion Analysis</h2>
            </div>

            {/* Current congestion bar chart */}
            <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-4">
                <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Top Congestion Hotspots</h3>
                <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} domain={[0, 100]} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: 12 }}
                                labelStyle={{ color: '#e2e8f0' }}
                            />
                            <Bar dataKey="current" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Congestion %" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Prediction area chart */}
            {predData.length > 0 && (
                <div className="bg-slate-800/50 rounded-xl border border-slate-700/30 p-4">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Congestion Forecast</h3>
                    <div className="h-[180px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={predData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} domain={[0, 100]} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: 12 }}
                                />
                                <Area type="monotone" dataKey="T+60min" fill="#ef444420" stroke="#ef4444" />
                                <Line type="monotone" dataKey="T+30min" stroke="#f97316" strokeWidth={2} dot={false} />
                                <Line type="monotone" dataKey="T+15min" stroke="#eab308" strokeWidth={2} dot={false} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex gap-4 mt-2 justify-center text-[10px]">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" /> 15 min</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" /> 30 min</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> 60 min</span>
                    </div>
                </div>
            )}
        </div>
    );
}
