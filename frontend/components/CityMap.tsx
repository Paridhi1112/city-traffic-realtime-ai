'use client';
import React, { useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MAP_CONFIG, CIRCLE_LAYER, HEATMAP_LAYER } from '@/lib/mapConfig';

interface CityMapProps {
    heatmapData?: any;
    onIntersectionClick?: (id: string) => void;
}

export default function CityMap({ heatmapData, onIntersectionClick }: CityMapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const mapLoaded = useRef(false);
    const pendingData = useRef<any>(null);

    // Stable callback ref to avoid re-creating the map when the callback changes
    const onClickRef = useRef(onIntersectionClick);
    onClickRef.current = onIntersectionClick;

    const applyData = useCallback((mapInstance: maplibregl.Map, data: any) => {
        const source = mapInstance.getSource('congestion') as maplibregl.GeoJSONSource;
        if (source) {
            source.setData(data);
        }
    }, []);

    useEffect(() => {
        if (!mapContainer.current || map.current) return;

        const mapInstance = new maplibregl.Map({
            container: mapContainer.current,
            style: MAP_CONFIG.style,
            center: MAP_CONFIG.center,
            zoom: MAP_CONFIG.zoom,
            pitch: MAP_CONFIG.pitch,
            bearing: MAP_CONFIG.bearing,
        });

        mapInstance.addControl(new maplibregl.NavigationControl(), 'top-right');
        mapInstance.addControl(new maplibregl.ScaleControl(), 'bottom-left');

        mapInstance.on('load', () => {
            mapLoaded.current = true;

            // Add the GeoJSON source
            mapInstance.addSource('congestion', {
                type: 'geojson',
                data: { type: 'FeatureCollection', features: [] },
            });

            // Add layers — source is already set in the layer config
            mapInstance.addLayer(HEATMAP_LAYER as any);
            mapInstance.addLayer(CIRCLE_LAYER as any);

            // If data arrived before the map loaded, apply it now
            if (pendingData.current) {
                applyData(mapInstance, pendingData.current);
                pendingData.current = null;
            }

            // Click handler for intersection points
            mapInstance.on('click', 'congestion-points', (e: any) => {
                if (e.features?.[0]?.properties?.intersection_id) {
                    onClickRef.current?.(e.features[0].properties.intersection_id);
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
            mapLoaded.current = false;
            mapInstance.remove();
            map.current = null;
        };
    }, []); // No dependencies — only create the map once

    // Update heatmap data whenever it changes
    useEffect(() => {
        if (!heatmapData) return;

        if (map.current && mapLoaded.current) {
            applyData(map.current, heatmapData);
        } else {
            // Map hasn't loaded yet — store until it does
            pendingData.current = heatmapData;
        }
    }, [heatmapData, applyData]);

    return (
        <div className="relative w-full h-full rounded-xl overflow-hidden border border-slate-700/50">
            <div ref={mapContainer} className="w-full h-full" />
        </div>
    );
}
