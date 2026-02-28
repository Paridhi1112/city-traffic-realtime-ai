export const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

export const MAP_CONFIG = {
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [72.88, 19.08] as [number, number], // Mumbai
    zoom: 12,
    pitch: 45,
    bearing: -17.6,
};

export const CONGESTION_COLORS = {
    low: '#22c55e',      // green
    moderate: '#eab308', // yellow
    high: '#f97316',     // orange
    critical: '#ef4444', // red
};

export function getCongestionColor(percent: number): string {
    if (percent < 25) return CONGESTION_COLORS.low;
    if (percent < 50) return CONGESTION_COLORS.moderate;
    if (percent < 75) return CONGESTION_COLORS.high;
    return CONGESTION_COLORS.critical;
}

export function getCongestionLabel(percent: number): string {
    if (percent < 25) return 'Low';
    if (percent < 50) return 'Moderate';
    if (percent < 75) return 'High';
    return 'Critical';
}

// Heatmap layer config for Mapbox
export const HEATMAP_LAYER = {
    id: 'congestion-heat',
    type: 'heatmap' as const,
    paint: {
        'heatmap-weight': ['interpolate', ['linear'], ['get', 'congestion'], 0, 0, 100, 1],
        'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 15, 3],
        'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, 'rgb(34,197,94)',
            0.4, 'rgb(234,179,8)',
            0.6, 'rgb(249,115,22)',
            0.8, 'rgb(239,68,68)',
            1, 'rgb(185,28,28)',
        ],
        'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 2, 15, 30],
    },
};

export const CIRCLE_LAYER = {
    id: 'congestion-points',
    type: 'circle' as const,
    minzoom: 10,
    paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 4, 15, 12],
        'circle-color': [
            'interpolate', ['linear'], ['get', 'congestion'],
            0, CONGESTION_COLORS.low,
            25, CONGESTION_COLORS.low,
            50, CONGESTION_COLORS.moderate,
            75, CONGESTION_COLORS.high,
            100, CONGESTION_COLORS.critical,
        ],
        'circle-stroke-color': '#1e293b',
        'circle-stroke-width': 2,
        'circle-opacity': 0.85,
    },
};
