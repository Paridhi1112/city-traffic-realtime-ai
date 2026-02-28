'use client';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export function usePredictions(intersectionId?: string) {
    const [predictions, setPredictions] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!intersectionId) return;
        const fetchPredictions = async () => {
            try {
                const data = await api.getPredictions(intersectionId);
                setPredictions(data);
            } catch (err) {
                console.error('Failed to fetch predictions:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchPredictions();
        const interval = setInterval(fetchPredictions, 60000);
        return () => clearInterval(interval);
    }, [intersectionId]);

    return { predictions, loading };
}
