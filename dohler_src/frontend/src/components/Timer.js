import React, { useState, useEffect, useCallback } from 'react';
import { FiPlay, FiPause, FiRefreshCw, FiZap } from 'react-icons/fi';

const Timer = ({ onComplete }) => {
  const [minutes, setMinutes] = useState(25);
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [mode, setMode] = useState('focus'); // focus, break

  const toggle = () => setIsActive(!isActive);

  const reset = useCallback(() => {
    setIsActive(false);
    setMinutes(mode === 'focus' ? 25 : 5);
    setSeconds(0);
  }, [mode]);

  useEffect(() => {
    let interval = null;
    if (isActive) {
      interval = setInterval(() => {
        if (seconds > 0) {
          setSeconds(seconds - 1);
        } else if (minutes > 0) {
          setMinutes(minutes - 1);
          setSeconds(59);
        } else {
          clearInterval(interval);
          setIsActive(false);
          if (mode === 'focus') {
            onComplete();
            setMode('break');
          } else {
            setMode('focus');
          }
        }
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isActive, minutes, seconds, mode, onComplete]);

  useEffect(() => {
    reset();
  }, [mode, reset]);

  return (
    <div className="glass-card rounded-[3rem] p-10 flex flex-col items-center justify-center relative overflow-hidden group">
      {/* Decorative pulse */}
      <div className={`absolute inset-0 bg-gradient-to-br ${mode === 'focus' ? 'from-cyan-500/10' : 'from-emerald-500/10'} to-transparent opacity-50 group-hover:opacity-100 transition-opacity`}></div>
      
      <div className="relative z-10 flex flex-col items-center">
        <span className={`text-[10px] font-black uppercase tracking-[0.5em] mb-4 ${mode === 'focus' ? 'text-cyan-400' : 'text-emerald-400'} flex items-center gap-2 animate-pulse`}>
          <FiZap /> {mode === 'focus' ? 'Procesamiento Neuronal' : 'Refrigeración del Sistema'}
        </span>
        
        <div className="text-8xl font-black tabular-nums tracking-tighter mb-8 flex items-baseline">
          {String(minutes).padStart(2, '0')}
          <span className="opacity-20 animate-pulse mx-1">:</span>
          {String(seconds).padStart(2, '0')}
        </div>

        <div className="flex gap-4">
          <button
            onClick={toggle}
            className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${
              isActive 
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/50 hover:bg-rose-500/30' 
              : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/30'
            }`}
            title={isActive ? 'Pausar' : 'Iniciar'}
          >
            {isActive ? <FiPause size={24} /> : <FiPlay size={24} className="ml-1" />}
          </button>
          
          <button
            onClick={reset}
            className="w-16 h-16 rounded-2xl bg-slate-800/50 text-slate-400 border border-slate-700 flex items-center justify-center hover:bg-slate-700 transition-all"
            title="Reiniciar"
          >
            <FiRefreshCw size={24} />
          </button>
        </div>

        <div className="mt-8 flex gap-2">
          <button 
            onClick={() => setMode('focus')}
            className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all ${mode === 'focus' ? 'bg-cyan-500 text-slate-900 shadow-[0_0_15px_rgba(6,182,212,0.5)]' : 'bg-slate-800 text-slate-500'}`}
          >
            Enfoque
          </button>
          <button 
            onClick={() => setMode('break')}
            className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all ${mode === 'break' ? 'bg-emerald-500 text-slate-900 shadow-[0_0_15px_rgba(16,185,129,0.5)]' : 'bg-slate-800 text-slate-500'}`}
          >
            Descanso
          </button>
        </div>
      </div>
    </div>
  );
};

export default Timer;
