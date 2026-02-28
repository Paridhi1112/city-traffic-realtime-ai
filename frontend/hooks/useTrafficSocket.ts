'use client';
import { useEffect, useState, useCallback, useRef } from 'react';
import { createTrafficSocket } from '@/lib/socket';

export function useTrafficSocket() {
    const [cityState, setCityState] = useState<any>(null);
    const [predictions, setPredictions] = useState<any>(null);
    const [decisions, setDecisions] = useState<any>(null);
    const [connected, setConnected] = useState(false);
    const socketRef = useRef<any>(null);

    useEffect(() => {
        const socket = createTrafficSocket((data) => {
            switch (data.type) {
                case 'connected':
                    setConnected(true);
                    break;
                case 'city_state_update':
                    setCityState(data.data);
                    break;
                case 'predictions_update':
                    setPredictions(data.data);
                    break;
                case 'ai_decisions_update':
                    setDecisions(data.data);
                    break;
            }
        });

        socketRef.current = socket;
        socket.connect();

        // Ping every 30s
        const pingInterval = setInterval(() => socket.sendPing(), 30000);

        return () => {
            clearInterval(pingInterval);
            socket.disconnect();
        };
    }, []);

    return { cityState, predictions, decisions, connected };
}
