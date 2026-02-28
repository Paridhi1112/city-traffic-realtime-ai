'use client';
import { Calendar, MapPin, Users } from 'lucide-react';

interface EventsPanelProps {
    events?: any[];
}

export default function EventsPanel({ events }: EventsPanelProps) {
    const eventList = events || [];

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-purple-400" />
                    City Events
                </h2>
                <span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    {eventList.length} active
                </span>
            </div>

            {eventList.length === 0 ? (
                <div className="text-center py-6 text-slate-500">
                    <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No active events</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {eventList.map((event: any, i: number) => (
                        <div key={i} className="rounded-lg bg-slate-800/50 border border-slate-700/40 p-3">
                            <h3 className="text-sm font-semibold text-white mb-1">{event.name}</h3>
                            <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                                {event.expected_attendance > 0 && (
                                    <span className="flex items-center gap-1">
                                        <Users className="w-3 h-3" />
                                        {event.expected_attendance.toLocaleString()} expected
                                    </span>
                                )}
                                {event.start_time && (
                                    <span className="flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                )}
                                <span className="flex items-center gap-1">
                                    <MapPin className="w-3 h-3" />
                                    {event.source}
                                </span>
                            </div>
                            {event.high_impact && (
                                <div className="mt-2 text-[10px] text-orange-400 bg-orange-500/10 py-1 px-2 rounded border border-orange-500/20 inline-block">
                                    ⚠️ High traffic impact — {event.affected_intersections?.length || 0} intersections affected
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
