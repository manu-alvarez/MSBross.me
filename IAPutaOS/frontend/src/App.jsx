import { useState, useRef, useEffect } from 'react';
import NeuralOrb from './components/NeuralOrb.jsx';
import Orb3D from './components/Orb3D.jsx';
import './index.css';

// API Configuration from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

import { 
  IconEye, IconCamera, IconMonitor, IconGlobe, 
  IconCalendar, IconMail, IconSend, IconTerminal, 
  IconMic, IconMicOff, IconTrash2, IconSmartphone 
} from './components/Icons.jsx';


import { CORE_PLUGINS, TOOLS } from './config/plugins.js';
import CorePlugins from './components/CorePlugins.jsx';
import SidePanel from './components/SidePanel.jsx';
import MobileDrawer from './components/MobileDrawer.jsx';
import ControlFooter from './components/ControlFooter.jsx';

function App() {
  const [orbState, setOrbState] = useState('ready');
  const [volume, setVolume] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // Advanced State
  const [transcript, setTranscript] = useState(null);
  const [visionImage, setVisionImage] = useState(null);
  const [userInput, setUserInput] = useState('');
  const [showTools, setShowTools] = useState(false);
  const [useOrb3D, setUseOrb3D] = useState(false);

  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDate = (date) => {
    const options = { weekday: 'long', day: 'numeric', month: 'long' };
    return date.toLocaleDateString('es-ES', options);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  };

  const initAudio = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
  };

  const handleAudioPlayback = async (url) => {
    if (!url) { setOrbState('ready'); return; }
    try {
      initAudio();
      const res = await fetch(url);
      if (!res.ok) throw new Error("Audio fetch failed");
      const buffer = await audioContextRef.current.decodeAudioData(await res.arrayBuffer());
      const source = audioContextRef.current.createBufferSource();
      source.buffer = buffer;
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      analyserRef.current.connect(audioContextRef.current.destination);
      dataArrayRef.current = new Uint8Array(analyserRef.current.frequencyBinCount);
      setOrbState('speaking');
      source.start(0);
      
      const updateVolume = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArrayRef.current);
          const vol = dataArrayRef.current.reduce((a, b) => a + b) / dataArrayRef.current.length;
          setVolume(vol / 255); // Normalize 0-1
          requestAnimationFrame(updateVolume);
        }
      };
      updateVolume();
      source.onended = () => { setOrbState('ready'); setVolume(0); };
    } catch (err) {
      console.error("Audio err:", err);
      setOrbState('ready');
    }
  };

  const sendCommand = async (endpoint, payload, isJson = true) => {
    initAudio();
    setOrbState('processing');
    setVisionImage(null);
    try {
      const options = { 
        method: 'POST', 
        headers: { 'x-api-key': API_KEY }, 
        body: payload 
      };
      if (isJson) options.headers['Content-Type'] = 'application/json';
      const fullUrl = `${API_BASE_URL}${endpoint}`;
      const res = await fetch(fullUrl, options);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      
      if (data.vision_url) setVisionImage(data.vision_url);

      const responseText = data.response || data.error || data.transcript || '';
      
      // Intercept __VISION_REQUEST__ markers from the backend
      if (responseText.startsWith('__VISION_REQUEST__:')) {
        const visionType = responseText.split(':')[1];
        setTranscript({ type: 'system', text: visionType === 'webcam' ? '◈ ACTIVANDO WEBCAM...' : '◈ CAPTURANDO PANTALLA...' });
        if (visionType === 'webcam') {
          await captureWebcam();
        } else {
          await captureScreenshot();
        }
        return;
      }

      setTranscript({ type: 'bot', text: responseText });
      handleAudioPlayback(data.audio_url);
    } catch (err) {
      setOrbState('error');
      setTranscript({ type: 'error', text: `Error: ${err.message}` });
    }
  };

  // ═══ VISION: Capture screenshot via getDisplayMedia (Fallback to Gallery on Mobile) ═══
  const captureScreenshot = async () => {
    try {
      setOrbState('processing');
      
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
      const isSupported = navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia;

      // Pantallas móviles no soportan getDisplayMedia nativo, usamos un selector de archivos como fallback
      if (isMobile || !isSupported) {
        setTranscript({ type: 'system', text: '◈ SELECCIONA UNA CAPTURA DE TU GALERÍA...' });
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => {
          const file = e.target.files[0];
          if (!file) {
            setOrbState('ready');
            setTranscript({ type: 'system', text: '◈ OPERACIÓN CANCELADA.' });
            return;
          }
          const reader = new FileReader();
          reader.onload = async (event) => {
            setTranscript({ type: 'system', text: '◈ ANALIZANDO IMAGEN...' });
            await sendVisionToBackend(event.target.result, 'screenshot');
          };
          reader.readAsDataURL(file);
        };
        input.click();
        return;
      }

      setTranscript({ type: 'system', text: '◈ SELECCIONA LA PANTALLA A CAPTURAR...' });
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' } });
      const track = stream.getVideoTracks()[0];
      const imageCapture = new ImageCapture(track);
      const bitmap = await imageCapture.grabFrame();
      track.stop();

      const canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(bitmap, 0, 0);
      const base64 = canvas.toDataURL('image/jpeg', 0.8);

      setTranscript({ type: 'system', text: '◈ ANALIZANDO PANTALLA...' });
      await sendVisionToBackend(base64, 'screenshot');
    } catch (err) {
      console.error('Screenshot error:', err);
      setOrbState('error');
      setTranscript({ type: 'error', text: `Error captura pantalla: ${err.message}` });
    }
  };

  // ═══ VISION: Capture webcam photo via getUserMedia ═══
  const captureWebcam = async () => {
    let stream = null;
    try {
      setOrbState('processing');
      setTranscript({ type: 'system', text: '◈ ACTIVANDO CÁMARA...' });
      
      const constraints = { 
        video: { 
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      };
      
      stream = await navigator.mediaDevices.getUserMedia(constraints);

      const video = document.createElement('video');
      video.srcObject = stream;
      video.setAttribute('playsinline', 'true');
      video.muted = true;
      
      await new Promise((resolve, reject) => {
        video.onloadedmetadata = () => {
          video.play().then(resolve).catch(reject);
        };
        video.onerror = reject;
      });

      // Wait for focus/lighting stabilization
      await new Promise(r => setTimeout(r, 800));

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      const base64 = canvas.toDataURL('image/jpeg', 0.85);

      setTranscript({ type: 'system', text: '◈ ANALIZANDO IMAGEN...' });
      await sendVisionToBackend(base64, 'webcam');
    } catch (err) {
      console.error('Webcam error:', err);
      setOrbState('error');
      setTranscript({ type: 'error', text: `Error cámara: ${err.name === 'NotAllowedError' ? 'Permiso denegado' : err.message}` });
    } finally {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    }
  };

  // ═══ Send captured image to backend for AI analysis ═══
  const sendVisionToBackend = async (base64Image, source) => {
    try {
      const res = await fetch(`${API_BASE_URL}/vision-analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': API_KEY },
        body: JSON.stringify({ image: base64Image, source })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      if (data.vision_url) setVisionImage(data.vision_url);
      setTranscript({ type: 'bot', text: data.response });
      handleAudioPlayback(data.audio_url);
    } catch (err) {
      setOrbState('error');
      setTranscript({ type: 'error', text: `Error análisis: ${err.message}` });
    }
  };

  const handleToolAction = (tool) => {
    if (tool.action === 'screenshot') {
      captureScreenshot();
    } else if (tool.action === 'webcam') {
      captureWebcam();
    } else if (tool.cmd) {
      handleTextInput(tool.cmd);
    }
  };

  const handleTextInput = (text) => {
    if (!text.trim()) return;
    setTranscript({ type: 'user', text });
    setUserInput('');
    setShowTools(false);
    setTimeout(() => sendCommand('/text-command', JSON.stringify({ text })), 400);
  };

  const clearMemory = async () => {
    try {
      await fetch(`${API_BASE_URL}/clear-memory`, { 
        method: 'POST',
        headers: { 'x-api-key': API_KEY }
      });
      setTranscript({ type: 'system', text: '◈ MEMORIA PURGADA.' });
    } catch (err) {
      console.error(err);
    }
  };

  const toggleMic = async () => {
    initAudio();
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        chunksRef.current = [];

        mediaRecorderRef.current.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        mediaRecorderRef.current.onstop = async () => {
          setOrbState('processing');
          setTranscript({ type: 'system', text: '◈ PROCESANDO AUDIO...' });
          setVisionImage(null);
          
          const type = navigator.userAgent.includes('Safari') && !navigator.userAgent.includes('Chrome') ? 'audio/mp4' : 'audio/wav';
          const audioBlob = new Blob(chunksRef.current, { type });
          const formData = new FormData();
          formData.append('audio_file', audioBlob); // Backend expects 'audio_file' due to routes.py
          await sendCommand('/voice-command', formData, false);
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorderRef.current.start();
        setOrbState('listening');
        setTranscript({ type: 'system', text: '◈ ESCUCHANDO...' });
      } catch (err) {
        console.error("Mic error:", err);
        setOrbState('error');
        setTranscript({ type: 'error', text: `Mic: ${err.message}` });
      }
    } else {
      mediaRecorderRef.current.stop();
    }
  };

  return (
    <div className="premium-container">
      {/* Background Ambient Particles */}
      <div className="ambient-background" />
      
      {/* Top Contextual Info & Tools Button (Mobile) */}
      <div className="top-info-bar flex justify-between items-center w-full px-4">
        <span>Hoy es {formatDate(currentTime)}. Son las {formatTime(currentTime)}.</span>
        <button 
          onClick={() => setShowTools(!showTools)}
          className="md:hidden w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/50"
        >
          <IconSmartphone className="w-4 h-4" />
        </button>
      </div>

      <main className="main-interface">
        {/* Left Panel (Tools - Desktop) */}
        <SidePanel tools={TOOLS} onAction={handleToolAction} />

        {/* Center Panel (Orb, Neural Title & Transcript) */}
        <div className="center-panel relative w-full h-full">
          <div className="orb-wrapper w-full h-full flex flex-col items-center justify-center">
            
            {/* The Animated Orb — Switch between NeuralOrb (CSS) and Orb3D (THREE.js) */}
            {useOrb3D ? (
              <Orb3D audioLevel={volume} orbState={orbState} />
            ) : (
              <NeuralOrb audioLevel={volume} orbState={orbState} />
            )}
            
            <div className="text-center mt-8">
              <div 
                className="neural-title-v7 cursor-pointer select-none" 
                onClick={() => setUseOrb3D(!useOrb3D)}
                title={`Orbe: ${useOrb3D ? '3D Plasma' : 'Neural CSS'} — Click para cambiar`}
              >
                IAPuta OS:
              </div>
              <div className="text-white/50 text-sm tracking-[0.3em] mt-2 uppercase font-mono">Welcome to the Next Level</div>
              <div 
                className="text-[9px] text-white/20 mt-1 font-mono tracking-widest cursor-pointer hover:text-white/40 transition-colors"
                onClick={() => setUseOrb3D(!useOrb3D)}
              >
                [{useOrb3D ? '3D PLASMA' : 'NEURAL CSS'}] ↻
              </div>
            </div>

            {/* Transcript overlay — only show system/error/user/vision, NOT bot text responses */}
            {transcript && (transcript.type === 'system' || transcript.type === 'error' || transcript.type === 'user' || visionImage) && (
              <div className="absolute bottom-12 left-1/2 -translate-x-1/2 w-full max-w-lg z-20 pointer-events-none px-4">
                <div className="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 shadow-2xl pointer-events-auto">
                  {visionImage && (
                    <div className="mb-3 w-32 h-auto rounded-lg overflow-hidden border border-white/10 shadow-lg">
                      <img src={visionImage} alt="Vision" className="w-full h-full object-cover" />
                    </div>
                  )}
                  {transcript.type === 'user' ? (
                    <div>
                      <span className="text-[10px] text-white/30 tracking-wider font-mono">TÚ</span>
                      <p className="text-sm text-white/70 mt-1">{transcript.text}</p>
                      <span className="text-[10px] text-purple-400 animate-pulse mt-2 block font-mono">◈ PROCESANDO...</span>
                    </div>
                  ) : transcript.type === 'system' ? (
                    <span className={`text-sm font-bold tracking-wider animate-pulse font-mono ${orbState === 'listening' ? 'text-red-400' : 'text-purple-400'}`}>
                      {transcript.text}
                    </span>
                  ) : transcript.type === 'error' ? (
                    <span className="text-sm text-red-400 font-bold">{transcript.text}</span>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel (Core Plugins) */}
        <CorePlugins plugins={CORE_PLUGINS} />
      </main>

      {/* ── MOBILE TOOLS DRAWER ── */}
      <MobileDrawer 
        tools={TOOLS}
        showTools={showTools}
        setShowTools={setShowTools}
        onAction={handleToolAction}
      />

      {/* Bottom Interface (Mic, Input, Memory) */}
      <ControlFooter 
        orbState={orbState}
        userInput={userInput}
        setUserInput={setUserInput}
        onTextInput={handleTextInput}
        onToggleMic={toggleMic}
        onClearMemory={clearMemory}
      />
    </div>
  );
}

export default App;
