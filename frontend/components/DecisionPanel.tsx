'use client';
import { CheckCircle, XCircle, Clock, AlertTriangle, Zap, ArrowRightLeft, Bell, Target } from 'lucide-react';
import { api } from '@/lib/api';

interface DecisionPanelProps {
    decisions?: any;
}

const typeIcons: Record<string, any> = {
    signal_adjustment: Zap,
    reroute_suggestion: ArrowRightLeft,
    alert: Bell,
    preemptive_action: Target,
};

const urgencyColors: Record<string, string> = {
    immediate: 'text-red-400 bg-red-500/10 border-red-500/30',
    within_5min: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    within_15min: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    informational: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
};

export default function DecisionPanel({ decisions }: DecisionPanelProps) {
    const decisionList = decisions?.decisions || decisions || [];

    const handleApprove = async (id: string) => {
        try { await api.approveDecision(id); } catch (e) { console.error(e); }
    };

    const handleReject = async (id: string) => {
        try { await api.rejectDecision(id); } catch (e) { console.error(e); }
    };

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-cyan-400" />
                    AI Decisions
                </h2>
                <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    {decisionList.length} active
                </span>
            </div>

            {decisions?.city_summary && (
                <p className="text-xs text-slate-400 bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                    {decisions.city_summary}
                </p>
            )}

            {decisionList.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Waiting for AI decisions...</p>
                </div>
            ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                    {decisionList.map((dec: any, i: number) => {
                        const Icon = typeIcons[dec.type] || Bell;
                        const urgencyClass = urgencyColors[dec.urgency] || urgencyColors.informational;

                        return (
                            <div key={dec.decision_id || i} className="rounded-lg bg-slate-800/50 border border-slate-700/40 p-3">
                                <div className="flex items-start gap-2 mb-2">
                                    <Icon className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${urgencyClass}`}>
                                                {dec.urgency?.replace('_', ' ')}
                                            </span>
                                            <span className="text-[10px] text-slate-500 font-mono">
                                                {dec.confidence}% conf.
                                            </span>
                                        </div>
                                        <p className="text-sm text-white leading-snug">{dec.action}</p>
                                        <p className="text-xs text-slate-400 mt-1">{dec.explanation}</p>
                                        {dec.expected_outcome && (
                                            <p className="text-xs text-emerald-400/80 mt-1">→ {dec.expected_outcome}</p>
                                        )}
                                        {dec.emission_impact && (
                                            <p className="text-[10px] text-green-500/70 mt-0.5">🌿 {dec.emission_impact}</p>
                                        )}
                                    </div>
                                </div>

                                {dec.requires_human_approval && (
                                    <div className="flex gap-2 mt-2 pt-2 border-t border-slate-700/30">
                                        <button
                                            onClick={() => handleApprove(dec.decision_id)}
                                            className="flex-1 flex items-center justify-center gap-1 text-xs py-1.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                                        >
                                            <CheckCircle className="w-3 h-3" /> Approve
                                        </button>
                                        <button
                                            onClick={() => handleReject(dec.decision_id)}
                                            className="flex-1 flex items-center justify-center gap-1 text-xs py-1.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                                        >
                                            <XCircle className="w-3 h-3" /> Reject
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
