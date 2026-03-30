import { useState, useEffect, useRef, Suspense, lazy } from 'react';
import {
    LiveKitRoom,
    VoiceAssistantControlBar,
    RoomAudioRenderer,
    useVoiceAssistant,
    useLocalParticipant,
    useRoomContext,
    useParticipants,
    useRemoteParticipants
} from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import '@livekit/components-styles';
import './index.css';

// Lazy load components for better performance
const InteractiveMenu = lazy(() => import('./InteractiveMenu'));
const RestaurantMap = lazy(() => import('./RestaurantMap'));

// State mapping for Spanish labels and CSS classes
const STATE_CONFIG = {
    listening: { label: 'ESCUCHANDO', cssClass: 'orb-listening', statusClass: 'status-listening' },
    speaking: { label: 'HABLANDO', cssClass: 'orb-speaking', statusClass: 'status-speaking' },
    thinking: { label: 'PENSANDO', cssClass: 'orb-thinking', statusClass: 'status-thinking' },
    initializing: { label: 'INICIANDO', cssClass: 'orb-inactive', statusClass: 'status-initializing' },
    connecting: { label: 'CONECTANDO', cssClass: 'orb-inactive', statusClass: 'status-initializing' },
};

// --- CORE VOICE ASSISTANT COMPONENT ---
const VoiceAssistantInner = () => {
    const { state, audioTrack } = useVoiceAssistant();
    const { localParticipant } = useLocalParticipant();
    const [currentCategory, setCurrentCategory] = useState(null);
    const [highlightItem, setHighlightItem] = useState(null);
    const [highlightTable, setHighlightTable] = useState(null);
    const [showTranscript, setShowTranscript] = useState(false);

    // Sync metadata from the agent to the UI
    useEffect(() => {
        if (!localParticipant?.metadata) return;
        try {
            const meta = JSON.parse(localParticipant.metadata);
            if (meta.category) setCurrentCategory(meta.category);
            if (meta.item) setHighlightItem(meta.item);
            if (meta.table) setHighlightTable(meta.table);
        } catch (e) {
            console.error("Metadata parse error", e);
        }
    }, [localParticipant?.metadata]);

    const activeConfig = STATE_CONFIG[state] || { label: 'LISTO', cssClass: '', statusClass: 'status-inactive' };

    return (
        <div className="main-layout" style={{ 
            display: 'flex', 
            width: '100vw', 
            height: '100vh', 
            padding: '40px',
            position: 'relative',
            zIndex: 10
        }}>
            {/* Left Column: Contextual UI (Menu/Map) */}
            <div className="left-side" style={{ flex: '0 0 400px', display: 'flex', flexDirection: 'column' }}>
                <Suspense fallback={<div className="glass-panel" style={{padding: '24px'}}>Cargando Menú...</div>}>
                    <InteractiveMenu currentCategory={currentCategory} highlightItem={highlightItem} />
                    <RestaurantMap highlightTable={highlightTable} />
                </Suspense>
            </div>

            {/* Center: The Neural Orb & Controls */}
            <div className="center-side" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className={`orb-container ${activeConfig.cssClass}`}>
                    <div className="orb-ring orb-ring-1" />
                    <div className="orb-ring orb-ring-2" />
                    <div className="orb" />
                </div>

                <div className="status-container" style={{ marginTop: '40px', textAlign: 'center' }}>
                    <div className={`status-badge ${activeConfig.statusClass}`}>
                        <span className="dot" />
                        {activeConfig.label}
                    </div>
                    <h1 className="gradient-text" style={{ 
                        fontFamily: '"Playfair Display", serif', 
                        fontSize: '3.5rem', 
                        marginTop: '16px',
                        fontWeight: 700 
                    }}>
                        Nikolina AI
                    </h1>
                    <p style={{ color: 'rgba(255,255,255,0.4)', letterSpacing: '4px', fontSize: '0.8rem', textTransform: 'uppercase', marginTop: '8px' }}>
                        Neural Restaurant Agent v2.5
                    </p>
                </div>

                <div className="controls-wrapper" style={{ marginTop: '60px' }}>
                    <VoiceAssistantControlBar />
                </div>
            </div>

            {/* Bottom Actions */}
            <div style={{ position: 'absolute', bottom: '40px', right: '40px', display: 'flex', gap: '16px' }}>
                <button 
                  className={`btn-toggle-transcript ${showTranscript ? 'active' : ''}`}
                  onClick={() => setShowTranscript(!showTranscript)}
                >
                    {showTranscript ? 'CERRAR LOGS' : 'VER TRANSCRIPCIÓN'}
                </button>
            </div>
            
            {/* Right Side Transcript Panel (Overlay) */}
            <div className={`transcript-panel glass-panel ${showTranscript ? 'open' : ''}`} style={{ padding: '32px' }}>
                <h3 style={{ marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
                    Logs de Sesión
                </h3>
                <div style={{ flex: 1, overflowY: 'auto', fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' }}>
                    {/* LiveKit provides transcript hooks if needed, or we can pipe from state */}
                    <div style={{ padding: '8px', borderLeft: '2px solid var(--accent-violet)', marginBottom: '12px', background: 'rgba(255,255,255,0.03)' }}>
                        [SISTEMA] Conexión establecida con el núcleo neural.
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- ORCHESTRATOR COMPONENT ---
const App = () => {
    const [token, setToken] = useState(null);
    const [error, setError] = useState(null);
    
    // LiveKit credentials from environment
    const serverUrl = import.meta.env.VITE_LIVEKIT_URL || 'wss://livekit.alvarezconsult.com';
    const apiBase = import.meta.env.VITE_API_URL || 'https://livekit.alvarezconsult.com';

    useEffect(() => {
        const fetchToken = async () => {
            try {
                // Generate a unique identity
                const identity = 'user_' + Math.random().toString(36).substring(7);
                const room = 'nikolina_session';
                
                const response = await fetch(`${apiBase}/api/token`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        participant_identity: identity,
                        room_name: room
                    })
                });
                
                if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
                const data = await response.json();
                setToken(data.accessToken);
            } catch (err) {
                console.error("Token fetch failed:", err);
                setError(err.message);
            }
        };

        fetchToken();
    }, [apiBase]);

    if (error) {
        return (
            <div className="error-screen" style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', color: '#ff4d4d' }}>
                <h2>Error de Conexión</h2>
                <p>{error}</p>
                <button onClick={() => window.location.reload()} style={{ marginTop: '20px', padding: '10px 20px', background: '#333', border: '1px solid #555', color: '#fff', borderRadius: '8px' }}>Reintentar</button>
            </div>
        );
    }

    if (!token) {
        return (
            <div className="loading-screen" style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                <div className="orb-thinking" style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--accent-violet)', animation: 'thinkingPulse 2s infinite' }} />
                <p style={{ marginTop: '24px', letterSpacing: '2px', color: 'rgba(255,255,255,0.5)' }}>DESPERTANDO A NIKOLINA...</p>
            </div>
        );
    }

    return (
        <LiveKitRoom
            serverUrl={serverUrl}
            token={token}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={() => setToken(null)}
            className="lk-container-custom"
        >
            <NeuralCanvas />
            <VoiceAssistantInner />
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
};

// Neural Canvas Component for Liquid Aura effect
const NeuralCanvas = () => {
    const canvasRef = useRef(null);
    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let width, height, particles = [];

        function initCanvas() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            particles = [];
            for (let i = 0; i < 80; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    vx: (Math.random() - 0.5) * 0.4,
                    vy: (Math.random() - 0.5) * 0.4,
                    size: Math.random() * 1 + 0.5
                });
            }
        }

        window.addEventListener('resize', initCanvas);
        initCanvas();

        let animationFrame;
        function animate() {
            ctx.clearRect(0, 0, width, height);
            ctx.strokeStyle = 'rgba(139, 92, 246, 0.1)';
            ctx.lineWidth = 0.4;
            particles.forEach((p, i) => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                ctx.fill();
                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const d = Math.sqrt((p.x - p2.x)**2 + (p.y - p2.y)**2);
                    if (d < 100) {
                        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                    }
                }
            });
            animationFrame = requestAnimationFrame(animate);
        }
        animate();
        return () => {
            window.removeEventListener('resize', initCanvas);
            cancelAnimationFrame(animationFrame);
        };
    }, []);
    return <canvas ref={canvasRef} id="neural-canvas" style={{ position: 'fixed', top: 0, left: 0, zIndex: -1, opacity: 0.5, pointerEvents: 'none' }} />;
};

export default App;
