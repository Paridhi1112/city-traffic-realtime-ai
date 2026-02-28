const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function createTrafficSocket(onMessage: (data: any) => void) {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;

    function connect() {
        ws = new WebSocket(`${WS_URL}/ws/traffic`);

        ws.onopen = () => {
            console.log('[WS] Connected to Urban Traffic Brain');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch {
                console.warn('[WS] Invalid message:', event.data);
            }
        };

        ws.onclose = () => {
            console.log('[WS] Disconnected — reconnecting in 5s');
            reconnectTimer = setTimeout(connect, 5000);
        };

        ws.onerror = (err) => {
            console.error('[WS] Error:', err);
            ws?.close();
        };
    }

    function disconnect() {
        if (reconnectTimer) clearTimeout(reconnectTimer);
        ws?.close();
        ws = null;
    }

    function sendPing() {
        if (ws?.readyState === WebSocket.OPEN) {
            ws.send('ping');
        }
    }

    return { connect, disconnect, sendPing };
}
