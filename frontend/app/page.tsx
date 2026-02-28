'use client';

import { useEffect, useState } from 'react';
import { useTrafficSocket } from '@/hooks/useTrafficSocket';
import { api } from '@/lib/api';
import WeatherWidget from '@/components/WeatherWidget';
import AlertFeed from '@/components/AlertFeed';
import DecisionPanel from '@/components/DecisionPanel';
import PredictionChart from '@/components/PredictionChart';
import EmissionTracker from '@/components/EmissionTracker';
import DataSourceStatus from '@/components/DataSourceStatus';
import IntersectionCard from '@/components/IntersectionCard';
import { Activity, MapPin, Gauge, AlertTriangle, Wifi, WifiOff } from 'lucide-react';

export default function Dashboard() {
    const { cityState: wsState, decisions: wsDecisions, connected } = useTrafficSocket();
    const [cityState, setCityState] = useState<any>(null);
    const [decisions, setDecisions] = useState<any>(null);
    const [emissions, setEmissions] = useState<any>(null);

    // Initial fetch + periodic refresh
    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [state, dec, em] = await Promise.all([
                    api.getCityState(),
                    api.getLiveDecisions(),
                    api.getEmissions(),
                ]);
                setCityState(state);
                setDecisions(dec);
                setEmissions(em);
            } catch (e) {
                console.error('Fetch failed:', e);
            }
        };
        fetchAll();
        const interval = setInterval(fetchAll, 15000);
        return () => clearInterval(interval);
    }, []);

    // Use WebSocket data when available
    const state = wsState || cityState;
    const dec = wsDecisions || decisions;
    const intersections = state?.intersections || [];
    const topIntersections = [...intersections]
        .sort((a: any, b: any) => (b.congestion_percent || 0) - (a.congestion_percent || 0))
        .slice(0, 6);

    const avgCongestion = state?.average_congestion_percent || 0;
    const totalIntersections = state?.total_intersections || 0;
    const incidentCount = state?.active_incidents_count || 0;

    return (
        <div className="p-4 lg:p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Activity className="w-7 h-7 text-cyan-400" />
                        Urban Traffic Brain
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">
                        {state?.city_name || 'Loading...'} • Real-time monitoring
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${connected ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-red-400 bg-red-500/10 border-red-500/20'}`}>
                        {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                        {connected ? 'Live' : 'Offline'}
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Gauge className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs text-slate-400">Avg. Congestion</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{avgCongestion.toFixed(0)}%</p>
                    <div className="h-1 bg-slate-800 rounded-full mt-2">
                        <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                                width: `${Math.min(avgCongestion, 100)}%`,
                                backgroundColor: avgCongestion < 30 ? '#22c55e' : avgCongestion < 60 ? '#eab308' : '#ef4444',
                            }}
                        />
                    </div>
                </div>

                <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <MapPin className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-slate-400">Intersections</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{totalIntersections}</p>
                    <p className="text-[10px] text-slate-500 mt-1">monitored live</p>
                </div>

                <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-orange-400" />
                        <span className="text-xs text-slate-400">Incidents</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{incidentCount}</p>
                    <p className="text-[10px] text-slate-500 mt-1">active now</p>
                </div>

                <div className="glass-card p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-purple-400" />
                        <span className="text-xs text-slate-400">AI Decisions</span>
                    </div>
                    <p className="text-3xl font-bold text-white font-mono">{dec?.decisions?.length || 0}</p>
                    <p className="text-[10px] text-slate-500 mt-1">latest round</p>
                </div>
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left column — charts + intersections */}
                <div className="lg:col-span-2 space-y-6">
                    <PredictionChart cityState={state} />

                    <div>
                        <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                            <MapPin className="w-5 h-5 text-blue-400" />
                            Top Congestion Hotspots
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {topIntersections.map((inter: any) => (
                                <IntersectionCard key={inter.intersection_id} intersection={inter} />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right column — widgets */}
                <div className="space-y-4">
                    <WeatherWidget weather={state?.weather} />
                    <DataSourceStatus />
                    <EmissionTracker emissions={emissions} />
                    <DecisionPanel decisions={dec} />
                    <AlertFeed cityState={state} />
                </div>
            </div>
        </div>
    );
}
