import React, { useState } from 'react'
import { FiTrash2, FiPlus, FiCheck, FiChevronDown, FiChevronUp } from 'react-icons/fi'

const TaskItem = ({ task, onToggle, onDelete, onUpdateChecklist }) => {
  const [showChecklist, setShowChecklist] = useState(false)
  const [newItem, setNewItem] = useState('')

  const handleAddChecklistItem = (e) => {
    e.preventDefault()
    if (!newItem.trim()) return
    const updatedChecklist = [
      ...(task.checklist || []),
      { id: Date.now(), text: newItem, completed: false }
    ]
    onUpdateChecklist(task.id, updatedChecklist)
    setNewItem('')
  }

  const toggleChecklistItem = (itemId) => {
    const updatedChecklist = task.checklist.map(item => 
      item.id === itemId ? { ...item, completed: !item.completed } : item
    )
    onUpdateChecklist(task.id, updatedChecklist)
  }

  const deleteChecklistItem = (itemId) => {
    const updatedChecklist = task.checklist.filter(item => item.id !== itemId)
    onUpdateChecklist(task.id, updatedChecklist)
  }

  return (
    <div className={`group flex flex-col p-4 rounded-2xl transition-all border ${
      task.completed 
      ? 'bg-slate-900/30 border-slate-800 opacity-60' 
      : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)]'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1">
          <button
            onClick={() => onToggle(task.id)}
            className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
              task.completed 
              ? 'bg-cyan-500 border-cyan-500 text-slate-900' 
              : 'border-slate-600 group-hover:border-cyan-400'
            }`}
          >
            {task.completed && <FiCheck size={14} strokeWidth={4} />}
          </button>
          
          <span className={`text-sm font-medium transition-all ${
            task.completed ? 'line-through text-slate-500' : 'text-slate-200'
          }`}>
            {task.title}
          </span>
        </div>

        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => setShowChecklist(!showChecklist)}
            className={`p-2 hover:text-cyan-400 border border-transparent hover:border-cyan-400/20 rounded-lg transition-all ${showChecklist ? 'text-cyan-400' : 'text-slate-500'}`}
            title="Checklist"
          >
            {showChecklist ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
          </button>
          <button
            onClick={() => onDelete(task.id)}
            className="p-2 text-slate-500 hover:text-rose-400 border border-transparent hover:border-rose-400/20 rounded-lg transition-all"
            title="Eliminar"
          >
            <FiTrash2 size={16} />
          </button>
        </div>
      </div>

      {showChecklist && (
        <div className="mt-4 pl-10 border-l border-slate-700 space-y-3 animate-slideDown">
          {task.checklist?.map(item => (
            <div key={item.id} className="flex items-center justify-between group/item">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => toggleChecklistItem(item.id)}
                  className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${item.completed ? 'bg-cyan-500 border-cyan-500 text-slate-900' : 'border-slate-600'}`}
                >
                  {item.completed && <FiCheck size={10} strokeWidth={4} />}
                </button>
                <span className={`text-xs ${item.completed ? 'line-through text-slate-500' : 'text-slate-400'}`}>
                  {item.text}
                </span>
              </div>
              <button 
                onClick={() => deleteChecklistItem(item.id)}
                className="opacity-0 group-item/hover:opacity-100 p-1 text-slate-600 hover:text-rose-400 transition-all"
              >
                <FiTrash2 size={12} />
              </button>
            </div>
          ))}
          
          <form onSubmit={handleAddChecklistItem} className="flex items-center gap-2 mt-2">
            <input
              type="text"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              placeholder="Añadir sub-tarea..."
              className="bg-transparent border-b border-slate-700 text-xs py-1 flex-1 focus:outline-none focus:border-cyan-500 transition-all text-slate-300"
            />
            <button type="submit" className="text-cyan-500 hover:scale-110 transition-all">
              <FiPlus size={16} />
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default TaskItem
