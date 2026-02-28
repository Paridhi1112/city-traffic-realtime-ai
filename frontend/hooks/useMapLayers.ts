'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

export function useMapLayers() {
    const [heatmapData, setHeatmapData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const refreshHeatmap = useCallback(async () => {
        try {
            const data = await api.getHeatmap();
            setHeatmapData(data);
        } catch (err) {
            console.error('Failed to load heatmap:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshHeatmap();
        const interval = setInterval(refreshHeatmap, 30000);
        return () => clearInterval(interval);
    }, [refreshHeatmap]);

    return { heatmapData, loading, refreshHeatmap };
}
