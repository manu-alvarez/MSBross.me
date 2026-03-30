import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = '/api.php';

const UNIT_PROCESOS = [
  { id: 'pasterizador', name: 'PASTERIZADOR', color: '#ff5f1f', icon: '🔥' },
  { id: 'evaporador', name: 'EVAPORADOR (VACÍO)', color: '#00d4ff', icon: '🌀' },
  { id: 'concentrador', name: 'CONCENTRADOR', color: '#8b5cf6', icon: '⚗️' },
  { id: 'enfriador', name: 'ENFRIADOR / FINAL', color: '#10b981', icon: '❄️' },
  { id: 'cip', name: 'LAVADO CIP (Limpieza)', color: '#ec4899', icon: '🧼' }
];

function App() {
  const [proceso, setProceso] = useState(UNIT_PROCESOS[0]);
  const [timers, setTimers] = useState([]);
  const [valvulas, setValvulas] = useState([
    { id: 'v1', label: 'Válvula Entrada Principal', open: false, type: 'manual' },
    { id: 'v2', label: 'Válvula Retorno CIP', open: false, type: 'manual' },
    { id: 'b1', label: 'Bomba de Alimentación P1', open: false, type: 'pump' },
    { id: 'v3', label: 'Válvula Salida Concentrado', open: false, type: 'manual' }
  ]);
  const [logs, setLogs] = useState([]);
  const [batchId, setBatchId] = useState('');

  const toggleValvula = (id) => {
    setValvulas(prev => prev.map(v => v.id === id ? { ...v, open: !v.open } : v));
    const v = valvulas.find(v => v.id === id);
    addLog(`${v.label} ${!v.open ? 'ABIERTA/ARRANCADA' : 'CERRADA/PARADA'}`);
  };

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [`[${time}] ${msg}`, ...prev].slice(0, 10));
  };

  const startTimer = (label, minutes) => {
    const end = Date.now() + minutes * 60000;
    setTimers(prev => [...prev, { id: Date.now(), label, end, total: minutes * 60 }]);
  };

  return (
    <div className="dohler-enterprise" style={{ '--accent': proceso.color }}>
      <header className="industrial-header">
        <div className="brand-section">
          <div className="logo-box">D</div>
          <div className="title-stack">
            <h1>DÖHLER <span>UNIPEKTIN</span></h1>
            <p>SISTEMA DE CONTROL DE PRODUCCIÓN • FRAGA</p>
          </div>
        </div>
        <div className="batch-info">
          <label>ID LOTE:</label>
          <input 
            type="text" 
            placeholder="P-2026-X" 
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
          />
        </div>
      </header>

      <main className="industrial-grid">
        {/* Left: Process Selection */}
        <aside className="process-sidebar glass-panel">
          <h2>UNIDAD DE PROCESO</h2>
          <div className="process-list">
            {UNIT_PROCESOS.map(p => (
              <button 
                key={p.id} 
                className={proceso.id === p.id ? 'active' : ''}
                onClick={() => {
                  setProceso(p);
                  addLog(`Cambiando a unidad: ${p.name}`);
                }}
              >
                <span className="icon">{p.icon}</span>
                <span className="name">{p.name}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* Center: Control SCADA */}
        <section className="scada-viewport glass-panel">
          <div className="status-banner">
            <span className="status-dot"></span> 
            MODO: {proceso.name} 
            <span className="divider">|</span>
            ESTADO: <span className="highlight">NOMINAL</span>
          </div>
          
          <div className="pipe-diagram">
            {valvulas.map((v, i) => (
              <div key={v.id} className={`device-node ${v.open ? 'active' : ''}`} onClick={() => toggleValvula(v.id)}>
                <div className="device-icon">{v.type === 'pump' ? '⚙️' : '🔘'}</div>
                <div className="device-label">{v.label}</div>
              </div>
            ))}
            <div className="flow-line"></div>
          </div>

          <div className="checklist-industrial">
            <h3>CHECKLIST SEGURIDAD & CONTROL</h3>
            <div className="check-grid">
              <label><input type="checkbox" /> Presión de vacío estable</label>
              <label><input type="checkbox" /> Temperatura de pasterización OK</label>
              <label><input type="checkbox" /> Toma de muestra realizada</label>
              <label><input type="checkbox" /> Nivel de depósito correcto</label>
            </div>
          </div>
        </section>

        {/* Right: Timers & Logs */}
        <aside className="metrics-sidebar">
          <div className="timers-box glass-panel">
            <h3>TEMPORIZADORES</h3>
            <div className="quick-timers">
              <button onClick={() => startTimer('Lavado CIP', 15)}>+15m CIP</button>
              <button onClick={() => startTimer('Muestra', 5)}>+5m Muestra</button>
            </div>
            <div className="active-timers">
              {timers.map(t => (
                <div key={t.id} className="timer-item">
                  <div className="timer-info">
                    <span>{t.label}</span>
                    <span className="remaining">ACTIVO</span>
                  </div>
                  <div className="progress-bar"><div className="fill"></div></div>
                </div>
              ))}
              {timers.length === 0 && <p className="empty">Sin temporizadores activos</p>}
            </div>
          </div>

          <div className="logs-box glass-panel">
            <h3>LOG DE OPERACIÓN</h3>
            <div className="log-list">
              {logs.map((log, i) => <div key={i} className="log-entry">{log}</div>)}
            </div>
          </div>
        </aside>
      </main>

      <footer className="footer-status">
        <div className="sys-metrics">
          <span>CPU_CORE: 24%</span>
          <span className="div">/</span>
          <span>NET_LATENCY: 12ms</span>
          <span className="div">/</span>
          <span>DATA_SYNC: OK</span>
        </div>
        <div className="location">FRAGA_STATION_04</div>
      </footer>
    </div>
  );
}

export default App;
