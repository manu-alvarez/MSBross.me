import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Timer from './components/Timer';
import TaskList from './components/TaskList';
import { FiTrendingUp, FiCheckCircle, FiClock, FiActivity } from 'react-icons/fi';

const API_BASE = './api.php'; // Cambiado a relativo para el gateway serverless

function App() {
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({ total_pomodoros: 0, completed_tasks: 0 });
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const tasksRes = await axios.get(`${API_BASE}?action=get_tasks`);
      const statsRes = await axios.get(`${API_BASE}?action=get_stats`);
      setTasks(tasksRes.data);
      setStats(statsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error obteniendo datos de Dohler:', error);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const addTask = async (title) => {
    try {
      await axios.post(`${API_BASE}?action=add_task`, { 
        title,
        checklist: [] // Inicializar checklist vacío
      });
      fetchData();
    } catch (error) {
      console.error('Error al añadir tarea:', error);
    }
  };

  const toggleTask = async (id) => {
    try {
      const task = tasks.find((t) => t.id === id);
      await axios.post(`${API_BASE}?action=update_task`, {
        id,
        completed: !task.completed,
      });
      fetchData();
    } catch (error) {
      console.error('Error al actualizar tarea:', error);
    }
  };

  const updateTaskChecklist = async (taskId, checklist) => {
    try {
      await axios.post(`${API_BASE}?action=update_task`, {
        id: taskId,
        checklist: checklist
      });
      fetchData();
    } catch (error) {
      console.error('Error al actualizar checklist:', error);
    }
  };

  const deleteTask = async (id) => {
    try {
      await axios.post(`${API_BASE}?action=delete_task`, { id });
      fetchData();
    } catch (error) {
      console.error('Error al eliminar tarea:', error);
    }
  };

  const handleTimerComplete = async () => {
    try {
      await axios.post(`${API_BASE}?action=save_timer`, { duration: 25 });
      fetchData();
    } catch (error) {
      console.error('Error al guardar sesión de enfoque:', error);
    }
  };

  if (loading)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-cyan-400"></div>
      </div>
    );

  return (
    <div className="min-h-screen p-4 md:p-8">
      <header className="max-w-6xl mx-auto mb-12 flex flex-col md:flex-row justify-between items-center animate-hologram">
        <div>
          <h1 className="text-5xl font-black neon-text mb-2 tracking-tighter">
            DOHLER <span className="text-white opacity-40">SISTEMA</span>
          </h1>
          <p className="text-cyan-400/60 font-mono text-sm tracking-widest uppercase">
            Arquitectura Neuronal de Tareas v2.0
          </p>
        </div>
        <div className="flex gap-4 mt-6 md:mt-0">
          <StatCard icon={<FiActivity />} label="Disponibilidad" value="99.9%" />
          <StatCard
            icon={<FiTrendingUp />}
            label="Velocidad"
            value={`${stats.total_pomodoros * 25}m`}
          />
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Statistics Panel */}
        <section className="lg:col-span-3 space-y-6">
          <div className="glass-card p-6 rounded-3xl border-l-4 border-cyan-500 hover:neon-border transition-all">
            <h3 className="text-cyan-400 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <FiClock /> Ciclos de Enfoque
            </h3>
            <div className="text-4xl font-bold">{stats.total_pomodoros}</div>
            <div className="text-xs text-slate-500 mt-2">Pomodoros Acumulados</div>
          </div>
          <div className="glass-card p-6 rounded-3xl border-l-4 border-indigo-500 hover:neon-border transition-all">
            <h3 className="text-indigo-400 text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <FiCheckCircle /> Completadas
            </h3>
            <div className="text-4xl font-bold">{stats.completed_tasks}</div>
            <div className="text-xs text-slate-500 mt-2">Objetivos Neutralizados</div>
          </div>
        </section>

        {/* Core Operations */}
        <section className="lg:col-span-12 xl:col-span-9 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-8">
            <Timer onComplete={handleTimerComplete} />
          </div>
          <div className="space-y-8">
            <TaskList
              tasks={tasks}
              onToggle={toggleTask}
              onDelete={deleteTask}
              onAdd={addTask}
              onUpdateChecklist={updateTaskChecklist}
            />
          </div>
        </section>
      </main>

      <footer className="mt-20 text-center text-slate-600 text-xs font-mono uppercase tracking-[0.3em]">
        Dohler Task Manager // Ecosistema msbross.me // Serverless Seguro
      </footer>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="glass-card px-4 py-2 rounded-xl flex items-center gap-3 border-white/5">
      <span className="text-cyan-400">{icon}</span>
      <div>
        <div className="text-[10px] text-slate-500 uppercase leading-none">{label}</div>
        <div className="text-sm font-bold">{value}</div>
      </div>
    </div>
  );
}

export default App;
