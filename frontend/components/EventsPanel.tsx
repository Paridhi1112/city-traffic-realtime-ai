'use client';
import { Calendar, MapPin, Users, Clock, Globe, ChevronRight, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';

interface EventsPanelProps {
    weeklyData?: any;
    activeEvents?: any[];
}

const CATEGORY_STYLES: Record<string, { bg: string; text: string; border: string }> = {
    sports: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
    entertainment: { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20' },
    festival: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
    exhibition: { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/20' },
    public: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20' },
};

function formatTime(isoStr: string): string {
    try {
        return new Date(isoStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return '';
    }
}

function formatDate(isoStr: string): string {
    try {
        return new Date(isoStr).toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
        return '';
    }
}

function EventCard({ event }: { event: any }) {
    const catStyle = CATEGORY_STYLES[event.category] || CATEGORY_STYLES.public;

    return (
        <div className="rounded-lg bg-slate-800/50 border border-slate-700/40 p-3 hover:border-slate-600/60 transition-colors">
            <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="text-sm font-semibold text-white leading-tight">{event.name}</h3>
                <span className={`text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap ${catStyle.bg} ${catStyle.text} border ${catStyle.border}`}>
                    {event.category}
                </span>
            </div>
            <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                {event.start_time && (
                    <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(event.start_time)}
                        {event.end_time && ` – ${formatTime(event.end_time)}`}
                    </span>
                )}
                {event.expected_attendance > 0 && (
                    <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {event.expected_attendance.toLocaleString()}
                    </span>
                )}
                <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {event.source}
                </span>
            </div>
            {event.high_impact && (
                <div className="mt-2 text-[10px] text-orange-400 bg-orange-500/10 py-1 px-2 rounded border border-orange-500/20 inline-block">
                    ⚠️ High traffic impact — {event.affected_intersections?.length || 0} intersections
                </div>
            )}
        </div>
    );
}

function DaySection({ day }: { day: any }) {
    const isToday = day.is_today;
    const isTomorrow = day.is_tomorrow;

    let label = `${day.day_of_week}, ${formatDate(day.date)}`;
    if (isToday) label = `Today — ${day.day_of_week}, ${formatDate(day.date)}`;
    if (isTomorrow) label = `Tomorrow — ${day.day_of_week}, ${formatDate(day.date)}`;

    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2">
                <div className={`h-px flex-1 ${isToday ? 'bg-cyan-500/30' : 'bg-slate-700/50'}`} />
                <span className={`text-xs font-semibold px-2 ${isToday ? 'text-cyan-400' : isTomorrow ? 'text-purple-400' : 'text-slate-500'}`}>
                    {label}
                </span>
                <div className={`h-px flex-1 ${isToday ? 'bg-cyan-500/30' : 'bg-slate-700/50'}`} />
            </div>
            <div className="space-y-2">
                {day.events.map((event: any, i: number) => (
                    <EventCard key={`${day.date}-${i}`} event={event} />
                ))}
            </div>
        </div>
    );
}

export default function EventsPanel({ weeklyData, activeEvents }: EventsPanelProps) {
    const [currentTime, setCurrentTime] = useState<Date | null>(null);

    useEffect(() => {
        setCurrentTime(new Date());
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const tz = weeklyData?.timezone;
    const days = weeklyData?.days || [];
    const totalEvents = weeklyData?.total_events || 0;
    const cityName = weeklyData?.city_name || 'Mumbai';

    // Fallback: if no weekly data, show old active events list
    if (!weeklyData && activeEvents) {
        return (
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-purple-400" />
                        City Events
                    </h2>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        {activeEvents.length} active
                    </span>
                </div>
                {activeEvents.length === 0 ? (
                    <div className="text-center py-6 text-slate-500">
                        <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">No active events</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {activeEvents.map((event: any, i: number) => (
                            <EventCard key={i} event={event} />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Date/Time/Timezone Header */}
            <div className="rounded-xl bg-gradient-to-r from-slate-800/80 to-slate-800/40 border border-slate-700/40 p-4">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-purple-400" />
                        {cityName} Events
                    </h2>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        {totalEvents} this week
                    </span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan-400" />
                        <span className="text-white font-mono text-lg">
                            {currentTime?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) || '--:--:--'}
                        </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                        <Globe className="w-3.5 h-3.5" />
                        <span className="text-xs">
                            {tz?.abbr || 'UTC'} ({tz?.utc_offset || '+00:00'})
                        </span>
                    </div>
                    <div className="text-xs text-slate-500">
                        {currentTime?.toLocaleDateString([], { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) || ''}
                    </div>
                </div>
            </div>

            {/* Weekly Calendar */}
            {days.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                    <Calendar className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No events scheduled this week</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {days.map((day: any) => (
                        <DaySection key={day.date} day={day} />
                    ))}
                </div>
            )}
        </div>
    );
}
