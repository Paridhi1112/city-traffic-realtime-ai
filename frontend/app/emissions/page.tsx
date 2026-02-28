'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import EmissionTracker from '@/components/EmissionTracker';
import PredictionChart from '@/components/PredictionChart';
import { useTrafficSocket } from '@/hooks/useTrafficSocket';
import { Leaf, BarChart3, Lightbulb } from 'lucide-react';

export default function EmissionsPage() {
    const { cityState } = useTrafficSocket();
    const [emissions, setEmissions] = useState<any>(null);
    const [report, setReport] = useState<any>(null);

    useEffect(() => {
        const fetch = async () => {
            try {
                const [em, rep] = await Promise.all([
                    api.getEmissions(),
                    api.getEmissionReport(),
                ]);
                setEmissions(em);
                setReport(rep);
            } catch (e) {
                console.error(e);
            }
        };
        fetch();
        const interval = setInterval(fetch, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-4 lg:p-6 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                    <Leaf className="w-7 h-7 text-emerald-400" />
                    Emission Tracking
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                    CO₂ emissions correlated with traffic congestion
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <PredictionChart cityState={cityState} />
                </div>
                <div className="space-y-4">
                    <EmissionTracker emissions={emissions} />

                    {report?.recommendations && (
                        <div className="glass-card p-4 space-y-3">
                            <div className="flex items-center gap-2">
                                <Lightbulb className="w-5 h-5 text-yellow-400" />
                                <h3 className="text-sm font-bold text-white">Recommendations</h3>
                            </div>
                            <ul className="space-y-2">
                                {report.recommendations.map((rec: string, i: number) => (
                                    <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                                        <span className="text-emerald-400 mt-0.5">●</span>
                                        {rec}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
