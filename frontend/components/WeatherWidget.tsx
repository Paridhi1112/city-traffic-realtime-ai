'use client';
import { Cloud, Sun, CloudRain, CloudFog, Wind, Eye, Droplets, Thermometer } from 'lucide-react';

interface WeatherWidgetProps {
    weather?: any;
}

const conditionIcons: Record<string, any> = {
    Clear: Sun,
    Cloudy: Cloud,
    Rain: CloudRain,
    'Light Rain': CloudRain,
    'Heavy Rain': CloudRain,
    Drizzle: CloudRain,
    Fog: CloudFog,
    Haze: CloudFog,
    Thunderstorm: CloudRain,
};

export default function WeatherWidget({ weather }: WeatherWidgetProps) {
    if (!weather) return null;

    const Icon = conditionIcons[weather.condition] || Cloud;
    const impactFactor = weather.weather_impact_factor || 1.0;
    const hasImpact = impactFactor > 1.1;

    return (
        <div className="rounded-xl bg-slate-800/50 border border-slate-700/30 p-4">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Icon className={`w-6 h-6 ${hasImpact ? 'text-yellow-400' : 'text-cyan-400'}`} />
                    <div>
                        <p className="text-sm font-semibold text-white">{weather.condition}</p>
                        <p className="text-[10px] text-slate-400 capitalize">{weather.source}</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-2xl font-bold text-white font-mono">{weather.temperature_c}°</p>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-900/50 rounded-lg p-2">
                    <Droplets className="w-3 h-3 mx-auto mb-1 text-blue-400" />
                    <p className="text-xs font-mono text-white">{weather.precipitation_mm}</p>
                    <p className="text-[10px] text-slate-500">mm/hr</p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-2">
                    <Eye className="w-3 h-3 mx-auto mb-1 text-slate-400" />
                    <p className="text-xs font-mono text-white">{(weather.visibility_m / 1000).toFixed(1)}</p>
                    <p className="text-[10px] text-slate-500">km vis</p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-2">
                    <Wind className="w-3 h-3 mx-auto mb-1 text-teal-400" />
                    <p className="text-xs font-mono text-white">{weather.wind_speed_kmh?.toFixed(0)}</p>
                    <p className="text-[10px] text-slate-500">km/h</p>
                </div>
            </div>

            {hasImpact && (
                <div className="mt-2 px-2 py-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-center">
                    <p className="text-[10px] text-yellow-400">
                        ⚠️ Weather impact: {((impactFactor - 1) * 100).toFixed(0)}% traffic slowdown
                    </p>
                </div>
            )}
        </div>
    );
}
