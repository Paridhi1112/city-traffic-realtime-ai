'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useTrafficSocket } from '@/hooks/useTrafficSocket';
import DecisionPanel from '@/components/DecisionPanel';
import { Brain, History, Clock } from 'lucide-react';

export default function DecisionsPage() {
    const { decisions: wsDecisions } = useTrafficSocket();
    const [liveDecisions, setLiveDecisions] = useState<any>(null);
    const [history, setHistory] = useState<any>(null);
    const [page, setPage] = useState(1);

    useEffect(() => {
        const fetchDecisions = async () => {
            try {
                const [live, hist] = await Promise.all([
                    api.getLiveDecisions(),
                    api.getDecisionHistory(page),
                ]);
                setLiveDecisions(live);
                setHistory(hist);
            } catch (e) {
                console.error('Failed to fetch decisions:', e);
            }
        };
        fetchDecisions();
        const interval = setInterval(fetchDecisions, 30000);
        return () => clearInterval(interval);
    }, [page]);

    const decisions = wsDecisions || liveDecisions;

    return (
        <div className="p-4 lg:p-6 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                    <Brain className="w-7 h-7 text-cyan-400" />
                    AI Decisions
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                    Kimi AI traffic management decisions
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Live decisions */}
                <div className="glass-card p-4">
                    <DecisionPanel decisions={decisions} />
                </div>

                {/* Decision history */}
                <div className="glass-card p-4 space-y-3">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-slate-400" />
                        <h2 className="text-lg font-bold text-white">Decision History</h2>
                    </div>

                    {history?.decisions?.length > 0 ? (
                        <div className="space-y-2 max-h-[500px] overflow-y-auto">
                            {history.decisions.map((dec: any) => (
                                <div key={dec.id} className="rounded-lg bg-slate-900/50 border border-slate-700/30 p-3">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-xs font-semibold text-cyan-400">{dec.decision_type}</span>
                                        <span className="text-[10px] text-slate-500">
                                            <Clock className="w-3 h-3 inline mr-0.5" />
                                            {dec.created_at ? new Date(dec.created_at).toLocaleString() : 'Unknown'}
                                        </span>
                                    </div>
                                    <p className="text-sm text-white">{dec.action}</p>
                                    <p className="text-xs text-slate-400 mt-1">{dec.explanation}</p>
                                    <div className="flex gap-2 mt-2 text-[10px]">
                                        <span className="text-slate-500">Confidence: {dec.confidence}%</span>
                                        <span className="text-slate-500">Urgency: {dec.urgency}</span>
                                        {dec.approved_by && <span className="text-emerald-400">✓ Approved</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-slate-500">
                            <History className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No history yet</p>
                        </div>
                    )}

                    {history?.total_pages > 1 && (
                        <div className="flex justify-center gap-2 pt-2">
                            <button
                                onClick={() => setPage(Math.max(1, page - 1))}
                                disabled={page <= 1}
                                className="text-xs px-3 py-1 rounded bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
                            >
                                ← Prev
                            </button>
                            <span className="text-xs text-slate-500 py-1">Page {page} of {history.total_pages}</span>
                            <button
                                onClick={() => setPage(page + 1)}
                                disabled={page >= history.total_pages}
                                className="text-xs px-3 py-1 rounded bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
                            >
                                Next →
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
