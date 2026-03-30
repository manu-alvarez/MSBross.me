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

export default NeuralCanvas;

