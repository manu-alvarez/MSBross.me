import React from 'react';
import { IconTrash2, IconMic, IconMicOff } from './Icons.jsx';

const ControlFooter = ({ 
  orbState, 
  userInput, 
  setUserInput, 
  onTextInput, 
  onToggleMic, 
  onClearMemory 
}) => {
  return (
    <footer className="interface-footer relative z-50">
      <div className="controls-center flex items-center justify-center gap-4 w-full max-w-2xl px-4">
        
        <button
          onClick={onClearMemory}
          className="hidden md:flex flex-shrink-0 w-12 h-12 rounded-full bg-[#151515] border border-white/10 items-center justify-center hover:bg-red-500/10 hover:border-red-500/30 transition-all group pointer-events-auto"
          title="Purgar Memoria"
        >
          <IconTrash2 className="w-5 h-5 text-white/30 group-hover:text-red-400" />
        </button>

        <button 
          className={`mic-trigger flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center ${orbState === 'listening' ? 'active bg-red-500/20 border-red-500/50' : 'bg-[#151515] border-white/10'}`}
          onClick={onToggleMic}
        >
          {orbState === 'listening' ? <IconMicOff className="text-red-400 w-6 h-6" /> : <IconMic className="text-white/70 w-6 h-6" />}
        </button>
        
        <div className="cmd-line flex-1 w-full bg-[#151515] border border-white/10 rounded-full overflow-hidden flex items-center px-4 h-12 pointer-events-auto">
          <span className="prompt text-white/30 mr-3 font-mono text-sm">&gt;</span>
          <input 
            type="text" 
            placeholder="Escribe un comando o petición..." 
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onTextInput(userInput);
            }}
            className="w-full bg-transparent border-none outline-none text-white/80 text-sm placeholder:text-white/20"
          />
        </div>
      </div>
    </footer>
  );
};

export default ControlFooter;
