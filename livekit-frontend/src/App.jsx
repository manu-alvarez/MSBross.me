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

// Premium Loading Spinner Component
const LoadingSpinner = ({ message = "Cargando..." }) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
    }}>
        <div style={{
            width: '60px',
            height: '60px',
            border: '4px solid rgba(255,255,255,0.3)',
            borderTop: '4px solid white',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginBottom: '20px'
        }} />
        <p style={{ fontSize: '18px', fontWeight: 300 }}>{message}</p>
        <style>{`
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `}</style>
    </div>
);
                <div className="orb" />
                <div className="orb-ring orb-ring-1" />
                <div className="orb-ring orb-ring-2" />
            </div>

            {/* Status Badge */}
            <div className={`status-badge ${config.statusClass}`}>
                <span className="dot" />
                {config.label}
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Active Session Logic & UI
// ---------------------------------------------------------------------------
const ActiveSession = ({ onDisconnect }) => {
    const room = useRoomContext();
    const [messages, setMessages] = useState([]);
    const [showTranscript, setShowTranscript] = useState(false);
    
    // UI states mapped to AI speech
    const [currentCategory, setCurrentCategory] = useState(null);
    const [highlightItem, setHighlightItem] = useState(null);
    const [highlightTable, setHighlightTable] = useState(null);

    // Keyword mappings
    const keywords = {
        entrante: ['entrante', 'jamón', 'ibérico', 'croquetas', 'txangurro', 'ensalada', 'burrata'],
        principal: ['principal', 'lomo', 'bacalao', 'chuletón', 'arroz', 'meloso'],
        postre: ['postre', 'tarta', 'queso', 'torrija', 'caramelizada'],
        items: [
            'jamón ibérico', 'croquetas de txangurro', 'ensalada de burrata',
            'lomo de bacalao', 'chuletón madurado', 'arroz meloso',
            'tarta de queso', 'torrija caramelizada'
        ]
    };

    useEffect(() => {
        if (!room) return;
        
        const handleData = (payload, participant, kind, topic) => {
            if (topic === 'chat' || topic === 'lk-chat') {
                const text = new TextDecoder().decode(payload);
                try {
                    const data = JSON.parse(text);
                    setMessages(prev => [...prev.slice(-10), { id: data.id || Date.now(), text: data.message, isUser: false, name: 'Nikolina' }]);
                } catch (e) {
                    setMessages(prev => [...prev.slice(-10), { id: Date.now(), text: text, isUser: false, name: 'Nikolina' }]);
                }
            }
        };

        const handleTranscription = (segments, participant) => {
            const text = segments.map(s => s.text).join(' ');
            if (text.trim().length === 0) return;
            const isUser = participant?.identity !== 'msb-assistant';
            const name = isUser ? 'Tú' : 'Nikolina';
            
            // Parse Nikolina's speech for UI updates
            if (!isUser) {
                const lowerText = text.toLowerCase();
                
                // Detect categories
                if (keywords.entrante.some(k => lowerText.includes(k))) setCurrentCategory('entrante');
                else if (keywords.principal.some(k => lowerText.includes(k))) setCurrentCategory('principal');
                else if (keywords.postre.some(k => lowerText.includes(k))) setCurrentCategory('postre');
                
                // Detect specific items
                const foundItem = keywords.items.find(k => lowerText.includes(k));
                if (foundItem) setHighlightItem(foundItem);
                
                // Detect tables
                const tableMatch = lowerText.match(/mesa\s+(\d)/);
                if (tableMatch) setHighlightTable(tableMatch[1]);
                else if (lowerText.includes("terraza") && !highlightTable) setHighlightTable("1"); // Default Terraza
                else if (lowerText.includes("interior") && !highlightTable) setHighlightTable("4"); // Default Interior
            }

            setMessages(prev => {
                const newMsgs = [...prev];
                const last = newMsgs[newMsgs.length - 1];
                if (last && last.isUser === isUser && (Date.now() - (last.timestamp || 0) < 3000)) {
                    last.text = text;
                    return newMsgs;
                }
                const updated = [...prev, { id: Date.now(), text, isUser, name, timestamp: Date.now() }];
                return updated.slice(-10); // Keep only last 10 messages
            });
        };

        room.on(RoomEvent.DataReceived, handleData);
        room.on(RoomEvent.TranscriptionReceived, handleTranscription);
        return () => {
             room.off(RoomEvent.DataReceived, handleData);
             room.off(RoomEvent.TranscriptionReceived, handleTranscription);
        };
    }, [room, highlightTable]);

    return (
        <div style={{ width: '100vw', height: '100vh', position: 'absolute', top: 0, left: 0, overflow: 'hidden' }}>
            {/* Left Panel: Menu & Map */}
            <div style={{ 
                position: 'absolute', 
                left: '40px', 
                top: '50%', 
                transform: 'translateY(-50%)', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '24px', 
                zIndex: 10,
                opacity: (currentCategory || highlightItem || highlightTable) ? 1 : 0,
                transition: 'opacity 0.5s ease',
                pointerEvents: (currentCategory || highlightItem || highlightTable) ? 'auto' : 'none'
            }}>
                {(currentCategory || highlightItem) && (
                    <InteractiveMenu currentCategory={currentCategory} highlightItem={highlightItem} />
                )}
                {highlightTable && (
                    <RestaurantMap highlightTable={highlightTable} />
                )}
            </div>

            {/* Center: Orb */}
            <div style={{ 
                position: 'absolute', 
                left: showTranscript ? '40%' : '50%', 
                top: '45%', 
                transform: 'translate(-50%, -50%)', 
                zIndex: 5,
                transition: 'left 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
            }}>
                <OrbVisualizer />
            </div>

            {/* Bottom Controls */}
            <div style={{ position: 'absolute', bottom: '60px', left: showTranscript ? '40%' : '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: '16px', zIndex: 20, transition: 'left 0.6s cubic-bezier(0.16, 1, 0.3, 1)' }}>
                <VoiceAssistantControlBar controls={{ leave: false }} />
                <button className="btn-disconnect" onClick={onDisconnect}>Colgar</button>
                <button className={`btn-toggle-transcript ${showTranscript ? 'active' : ''}`} onClick={() => setShowTranscript(!showTranscript)}>
                    {showTranscript ? 'Ocultar Transcripción' : 'Ver Transcripción'}
                </button>
            </div>

            {/* Right Panel: Transcript */}
            <div className={`transcript-panel ${showTranscript ? 'open' : ''}`}>
                <div style={{ padding: '24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '12px', fontFamily: '"Outfit", sans-serif', fontWeight: 700 }}>
                        <span style={{ fontSize: '1.4rem' }}>💬</span> Registro de Conversación
                    </h3>
                </div>
                <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', height: 'calc(100% - 75px)' }}>
                    {messages.length === 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'rgba(255,255,255,0.3)', gap: '16px' }}>
                            <div className="orb-inactive" style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
                            <p style={{ letterSpacing: '1px', fontSize: '0.9rem' }}>Esperando mensajes...</p>
                        </div>
                    )}
                    {messages.map((msg, idx) => (
                        <div key={msg.id} style={{
                            alignSelf: msg.isUser ? 'flex-end' : 'flex-start',
                            backgroundColor: msg.isUser ? 'var(--primary-dark)' : 'rgba(20,20,25,0.8)',
                            padding: '16px 20px', 
                            borderRadius: '16px',
                            borderBottomRightRadius: msg.isUser ? '4px' : '16px',
                            borderBottomLeftRadius: msg.isUser ? '16px' : '4px',
                            maxWidth: '90%', 
                            border: msg.isUser ? '1px solid rgba(212, 175, 55, 0.3)' : '1px solid rgba(255,255,255,0.05)',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                            animation: 'fadeInUp 0.3s ease-out'
                        }}>
                            <strong style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', letterSpacing: '1px', textTransform: 'uppercase', color: msg.isUser ? 'rgba(255,255,255,0.7)' : 'var(--primary-main)', marginBottom: '8px' }}>
                                {msg.isUser ? 'Tú' : 'Nikolina'}
                            </strong>
                            <span style={{ fontSize: '1rem', color: '#fff', lineHeight: 1.6, fontWeight: 300 }}>{msg.text}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Main Application App
// ---------------------------------------------------------------------------
export default function App() {
    const [token, setToken] = useState("");
    const [roomName] = useState("voice-assistant-room");
    const [connecting, setConnecting] = useState(false);
    const MODELS = [
        { label: "Gemini 3.1", id: "gemini-3.1-flash-live-preview" },
        { label: "Gemini 2.5", id: "gemini-2.5-flash-native-audio-preview-12-2025" },
        { label: "Gemini 2.0", id: "gemini-2.0-flash-exp" },
    ];
    const [selectedPipeline, setSelectedPipeline] = useState(MODELS[0].id);
    const serverUrl = import.meta.env.VITE_LIVEKIT_URL;

    const handleConnect = async () => {
        if (token) { setToken(""); return; }
        setConnecting(true);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());

            const apiUrl = (import.meta.env.VITE_API_URL || "").replace("http://", "https://");
            const response = await fetch(`${apiUrl}/api/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    participant_identity: `Invitado_${Math.floor(Math.random() * 1000)}`,
                    room_name: roomName,
                    pipeline_id: selectedPipeline
                })
            });
            if (!response.ok) throw new Error(`Error Backend: ${response.status}`);
            const data = await response.json();
            if (data.accessToken) setToken(data.accessToken);
            else throw new Error(data.detail || "Error en token");
        } catch (e) {
            console.error(e);
            alert(`Fallo de conexión: ${e.message}`);
        } finally { setConnecting(false); }
    };

    return (
        <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden', backgroundColor: '#050508' }}>
            <NeuralCanvas />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', padding: '40px 24px' }}>
                <div style={{ position: 'absolute', top: '40px', textAlign: 'center', animation: 'fadeInUp 0.6s ease-out', zIndex: 10 }}>
                    <div style={{ fontFamily: 'JetBrains Mono', fontSize: '0.7rem', color: 'var(--primary-main)', letterSpacing: '3px', marginBottom: '8px' }}>NEURAL VOICE ENGINE</div>
                    <h1 style={{ fontFamily: 'Outfit', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 900, textTransform: 'uppercase' }} className="gradient-text">
                        Nikolina AI
                    </h1>
                </div>

                {!token ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '40px', animation: 'fadeInUp 0.8s ease-out 0.2s both', marginTop: '10vh', zIndex: 10 }}>
                        <div className="orb-container orb-inactive">
                            <div className="orb" /><div className="orb-ring orb-ring-1" /><div className="orb-ring orb-ring-2" />
                        </div>
                        <div style={{ textAlign: 'center', maxWidth: '360px' }}>
                            <h2 style={{ fontSize: '1.3rem', fontWeight: 600, marginBottom: '8px', color: '#fff' }}>Asistente Vocal Inteligente</h2>
                            <p style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.5)', lineHeight: 1.6 }}>Agente vocal nativo con latencia zero.<br />Selecciona tu motor Gemini y conecta.</p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '6px', borderRadius: '30px', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                            {MODELS.map(m => (
                                <button key={m.id} onClick={() => setSelectedPipeline(m.id)} style={{
                                    padding: '8px 16px', borderRadius: '20px', border: 'none', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.3s ease',
                                    backgroundColor: selectedPipeline === m.id ? 'var(--primary-main)' : 'transparent', color: selectedPipeline === m.id ? '#000' : 'rgba(255,255,255,0.4)'
                                }}>{m.label}</button>
                            ))}
                        </div>
                        <button className="btn-premium" onClick={handleConnect} disabled={connecting} style={{ opacity: connecting ? 0.7 : 1, width: '250px' }}>
                            {connecting ? '⏳ Conectando...' : '📞  Llamar Asistente'}
                        </button>
                    </div>
                ) : (
                    <LiveKitRoom serverUrl={serverUrl} token={token} connect={true} audio={true} video={false} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}>
                        <ActiveSession onDisconnect={handleConnect} />
                        <RoomAudioRenderer />
                    </LiveKitRoom>
                )}
            </div>
        </div>
    );
}
