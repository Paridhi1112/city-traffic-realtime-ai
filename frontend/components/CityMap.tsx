'use client';
import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MAPBOX_TOKEN, MAP_CONFIG, CIRCLE_LAYER, HEATMAP_LAYER } from '@/lib/mapConfig';

interface CityMapProps {
    heatmapData?: any;
    onIntersectionClick?: (id: string) => void;
}

export default function CityMap({ heatmapData, onIntersectionClick }: CityMapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<mapboxgl.Map | null>(null);

    useEffect(() => {
        if (!mapContainer.current || map.current) return;

        mapboxgl.accessToken = MAPBOX_TOKEN;

        const mapInstance = new mapboxgl.Map({
            container: mapContainer.current,
            style: MAP_CONFIG.style,
            center: MAP_CONFIG.center,
            zoom: MAP_CONFIG.zoom,
            pitch: MAP_CONFIG.pitch,
            bearing: MAP_CONFIG.bearing,
        });

        mapInstance.addControl(new mapboxgl.NavigationControl(), 'top-right');
        mapInstance.addControl(new mapboxgl.ScaleControl(), 'bottom-left');

        mapInstance.on('load', () => {
            // Add empty source — will be updated when data arrives
            mapInstance.addSource('congestion', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] },
            });

            mapInstance.addLayer(HEATMAP_LAYER as any, 'waterway-label');
            mapInstance.addLayer(CIRCLE_LAYER as any, 'waterway-label');

            // Click handler for intersection points
            mapInstance.on('click', 'congestion-points', (e) => {
                if (e.features?.[0]?.properties?.intersection_id) {
                    onIntersectionClick?.(e.features[0].properties.intersection_id);
                }
            });

            mapInstance.on('mouseenter', 'congestion-points', () => {
                mapInstance.getCanvas().style.cursor = 'pointer';
            });

            mapInstance.on('mouseleave', 'congestion-points', () => {
                mapInstance.getCanvas().style.cursor = '';
            });
        });

        map.current = mapInstance;

        return () => {
            mapInstance.remove();
            map.current = null;
        };
    }, [onIntersectionClick]);

    // Update heatmap data
    useEffect(() => {
        if (!map.current || !heatmapData) return;
        const source = map.current.getSource('congestion') as mapboxgl.GeoJSONSource;
        if (source) {
            source.setData(heatmapData);
        }
    }, [heatmapData]);

    return (
        <div className="relative w-full h-full rounded-xl overflow-hidden border border-slate-700/50">
            <div ref={mapContainer} className="w-full h-full" />
            {!MAPBOX_TOKEN && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur-sm">
                    <div className="text-center p-8">
                        <div className="text-4xl mb-4">🗺️</div>
                        <h3 className="text-xl font-semibold text-white mb-2">Map Token Required</h3>
                        <p className="text-slate-400 text-sm max-w-sm">
                            Set <code className="px-1.5 py-0.5 bg-slate-800 rounded text-cyan-400">NEXT_PUBLIC_MAPBOX_TOKEN</code> in your .env file
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
