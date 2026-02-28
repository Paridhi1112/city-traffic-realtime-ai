'use client';

import { useState } from 'react';
import CityMap from '@/components/CityMap';
import IntersectionCard from '@/components/IntersectionCard';
import { useMapLayers } from '@/hooks/useMapLayers';
import { useTrafficSocket } from '@/hooks/useTrafficSocket';
import { MapPin, X } from 'lucide-react';

export default function MapPage() {
    const { heatmapData } = useMapLayers();
    const { cityState } = useTrafficSocket();
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const selectedIntersection = cityState?.intersections?.find(
        (i: any) => i.intersection_id === selectedId
    );

    return (
        <div className="h-full relative">
            <CityMap
                heatmapData={heatmapData}
                onIntersectionClick={(id) => setSelectedId(id)}
            />

            {/* Map overlay header */}
            <div className="absolute top-4 left-4 glass-card px-4 py-2">
                <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm font-semibold text-white">
                        {cityState?.city_name || 'Mumbai'} Traffic Map
                    </span>
                    <span className="text-xs text-slate-400 ml-2">
                        {cityState?.total_intersections || 0} intersections
                    </span>
                </div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-6 left-4 glass-card px-4 py-3">
                <p className="text-[10px] text-slate-400 uppercase font-semibold mb-2">Congestion Level</p>
                <div className="flex gap-3 text-[10px]">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Low</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" /> Moderate</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" /> High</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Critical</span>
                </div>
            </div>

            {/* Selected intersection panel */}
            {selectedIntersection && (
                <div className="absolute top-4 right-4 w-80">
                    <div className="relative">
                        <button
                            onClick={() => setSelectedId(null)}
                            className="absolute -top-2 -right-2 z-10 w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-600 transition-colors"
                        >
                            <X className="w-3 h-3" />
                        </button>
                        <IntersectionCard intersection={selectedIntersection} />
                    </div>
                </div>
            )}
        </div>
    );
}
