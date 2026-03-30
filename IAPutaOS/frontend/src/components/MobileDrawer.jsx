import React from 'react';

const MobileDrawer = ({ tools, showTools, setShowTools, onAction }) => {
  if (!showTools) return null;

  return (
    <div className="fixed inset-x-0 bottom-[100px] z-50 p-4 md:hidden">
      <div className="bg-black/80 backdrop-blur-xl border border-white/10 rounded-3xl p-4 shadow-2xl animate-fade-in">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-1 rounded-full bg-white/20" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          {tools.map(t => (
            <button
              key={t.id}
              onClick={() => onAction(t)}
              className="flex flex-col items-center gap-2 p-3 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10"
            >
              <t.icon className="w-6 h-6" style={{ color: t.color }} />
              <div className="flex flex-col items-center">
                <span className="text-[10px] text-white/70 font-bold">{t.label}</span>
                <span className="text-[8px] text-white/30 truncate w-full text-center">{t.sub}</span>
              </div>
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowTools(false)}
          className="w-full mt-4 py-3 rounded-xl bg-white/5 text-[11px] font-bold text-white/40 tracking-wider hover:bg-white/10 uppercase"
        >
          Cerrar Panel
        </button>
      </div>
    </div>
  );
};

export default MobileDrawer;
