'use client';
import { AlertTriangle, Bell, Info, CheckCircle } from 'lucide-react';

interface AlertFeedProps {
    cityState?: any;
}

const severityConfig: Record<string, { icon: any; color: string; bg: string }> = {
    critical: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    warning: { icon: Bell, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
    info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
};

export default function AlertFeed({ cityState }: AlertFeedProps) {
    // Generate alerts from city state
    const alerts: any[] = [];

    if (cityState?.intersections) {
        for (const inter of cityState.intersections) {
            if (inter.congestion_percent > 80) {
                alerts.push({
                    id: `cong-${inter.intersection_id}`,
                    type: 'congestion',
                    severity: 'critical',
                    message: `Critical congestion at ${inter.road_names?.[0] || 'intersection'}: ${inter.congestion_percent.toFixed(0)}%`,
                    time: inter.timestamp,
                });
            }
            for (const inc of (inter.active_incidents || [])) {
                alerts.push({
                    id: `inc-${inter.intersection_id}`,
                    type: 'incident',
                    severity: inc.severity >= 2 ? 'critical' : 'warning',
                    message: inc.description || `${inc.incident_type} near ${inter.road_names?.[0] || 'intersection'}`,
                    time: inc.detected_at,
                });
            }
        }
    }

    if (cityState?.weather?.weather_impact_factor > 1.2) {
        alerts.push({
            id: 'weather',
            type: 'weather',
            severity: 'warning',
            message: `Weather impact: ${cityState.weather.condition} — ${((cityState.weather.weather_impact_factor - 1) * 100).toFixed(0)}% traffic slowdown expected`,
            time: cityState.weather.timestamp,
        });
    }

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Bell className="w-5 h-5 text-yellow-400" />
                    Live Alerts
                </h2>
                <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                    {alerts.length}
                </span>
            </div>

            {alerts.length === 0 ? (
                <div className="text-center py-6 text-slate-500">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-500/50" />
                    <p className="text-sm">All clear — no active alerts</p>
                </div>
            ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                    {alerts.slice(0, 10).map((alert) => {
                        const config = severityConfig[alert.severity] || severityConfig.info;
                        const Icon = config.icon;
                        return (
                            <div key={alert.id} className={`rounded-lg border p-3 flex items-start gap-2 ${config.bg}`}>
                                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${config.color}`} />
                                <div className="min-w-0">
                                    <p className="text-xs text-white leading-snug">{alert.message}</p>
                                    <p className="text-[10px] text-slate-500 mt-1">
                                        {alert.time ? new Date(alert.time).toLocaleTimeString() : 'just now'}
                                    </p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
