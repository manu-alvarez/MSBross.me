import React, { useState } from 'react';
import TaskItem from './TaskItem';
import { FiPlus, FiTarget } from 'react-icons/fi';

const TaskList = ({ tasks, onToggle, onDelete, onAdd, onUpdateChecklist }) => {
  const [newTask, setNewTask] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (newTask.trim()) {
      onAdd(newTask)
      setNewTask('')
    }
  }

  return (
    <div className="glass-card rounded-[2.5rem] p-8 flex flex-col h-[600px]">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xl font-bold flex items-center gap-3">
          <FiTarget className="text-cyan-400" />
          Objetivos de Misión
        </h2>
        <span className="bg-slate-800 text-slate-400 text-[10px] px-3 py-1 rounded-full font-mono">
          {tasks.filter((t) => !t.completed).length} ACTIVOS
        </span>
      </div>

      <form onSubmit={handleSubmit} className="mb-8 flex gap-2">
        <input
          type="text"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          placeholder="Desplegar nuevo objetivo..."
          className="flex-1 bg-slate-900/50 border border-slate-700 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:neon-border transition-all placeholder:text-slate-600"
        />
        <button
          type="submit"
          className="bg-cyan-500 text-slate-900 w-14 h-14 rounded-2xl flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)]"
        >
          <FiPlus size={24} />
        </button>
      </form>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
            <FiTarget size={48} className="mb-4" />
            <p className="font-mono text-xs uppercase tracking-widest">Sin protocolos activos</p>
          </div>
        ) : (
          tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggle={onToggle}
              onDelete={onDelete}
              onUpdateChecklist={onUpdateChecklist}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default TaskList;
