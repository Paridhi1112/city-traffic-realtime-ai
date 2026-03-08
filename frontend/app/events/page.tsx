'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import EventsPanel from '@/components/EventsPanel';
import WeatherWidget from '@/components/WeatherWidget';
import { useTrafficSocket } from '@/hooks/useTrafficSocket';
import { CalendarDays } from 'lucide-react';

export default function EventsPage() {
    const { cityState } = useTrafficSocket();
    const [weeklyData, setWeeklyData] = useState<any>(null);
    const [weather, setWeather] = useState<any>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [weekly, w] = await Promise.all([
                    api.getUpcomingEvents(),
                    api.getWeather(),
                ]);
                setWeeklyData(weekly);
                setWeather(w);
            } catch (e) {
                console.error('Events fetch failed:', e);
            }
        };
        fetchData();
        // Refresh every 5 minutes (events don't change that fast)
        const interval = setInterval(fetchData, 300000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-4 lg:p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <CalendarDays className="w-7 h-7 text-purple-400" />
                        City Events & Weather
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">
                        Events and weather conditions affecting traffic
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Events Calendar — takes 2 columns */}
                <div className="lg:col-span-2 glass-card p-4">
                    <EventsPanel
                        weeklyData={weeklyData}
                        activeEvents={cityState?.active_events}
                    />
                </div>

                {/* Right sidebar — weather */}
                <div className="space-y-4">
                    <WeatherWidget weather={cityState?.weather || weather} />
                    <div className="glass-card p-4">
                        <h3 className="text-sm font-bold text-white mb-3">Weather Impact on Traffic</h3>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-400">Rain &gt; 2mm/hr</span>
                                <span className="text-yellow-400">30% slowdown</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-400">Fog visibility &lt; 200m</span>
                                <span className="text-orange-400">50% slowdown</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-400">Wind &gt; 60 km/h</span>
                                <span className="text-red-400">20% slowdown</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-400">Normal conditions</span>
                                <span className="text-emerald-400">No impact</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
