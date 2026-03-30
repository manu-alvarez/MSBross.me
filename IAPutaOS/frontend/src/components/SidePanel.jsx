import React from 'react';

const SidePanel = ({ tools, onAction }) => {
  return (
    <div className="side-panel left-panel hidden md:flex flex-col justify-center gap-3 w-48 z-40 relative">
      <div className="panel-header text-center w-full">ACCESO RÁPIDO</div>
      {tools.map(t => (
        <button
          key={t.id}
          onClick={() => onAction(t)}
          className="w-full flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors group cursor-pointer"
        >
          <t.icon className="w-5 h-5 opacity-70 group-hover:opacity-100" style={{ color: t.color }} />
          <div className="flex flex-col items-start select-none">
            <span className="text-[11px] font-bold text-white/70">{t.label}</span>
            <span className="text-[9px] text-white/40">{t.sub}</span>
          </div>
        </button>
      ))}
    </div>
  );
};

export default SidePanel;
