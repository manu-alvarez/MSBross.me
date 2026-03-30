import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = '/api.php';

function App() {
  const [activeTab, setActiveTab] = useState('routine');
  const [familyTasks, setFamilyTasks] = useState([]);
  const [shoppingList, setShoppingList] = useState([]);
  const [newItem, setNewItem] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const tasksRes = await fetch(`${API_URL}?action=get_family_tasks`);
      const listRes = await fetch(`${API_URL}?action=get_shopping_list`);
      setFamilyTasks(await tasksRes.json());
      setShoppingList(await listRes.json());
      setLoading(false);
    } catch (error) {
      console.error("Error al cargar datos:", error);
      setLoading(false);
    }
  };

  const toggleTask = async (id, done) => {
    const updated = familyTasks.map(t => t.id === id ? { ...t, done: !done } : t);
    setFamilyTasks(updated);
    await fetch(`${API_URL}?action=update_family_task`, {
      method: 'POST',
      body: JSON.stringify({ id, done: !done })
    });
  };

  const toggleShopping = async (id, bought) => {
    const updated = shoppingList.map(item => item.id === id ? { ...item, bought: !bought } : item);
    setShoppingList(updated);
    await fetch(`${API_URL}?action=update_shopping_item`, {
      method: 'POST',
      body: JSON.stringify({ id, bought: !bought })
    });
  };

  const addShoppingItem = async (e) => {
    e.preventDefault();
    if (!newItem) return;
    const res = await fetch(`${API_URL}?action=update_shopping_item`, {
      method: 'POST',
      body: JSON.stringify({ add: true, name: newItem, category: 'General' })
    });
    setShoppingList(await res.json());
    setNewItem('');
  };

  const deleteShoppingItem = async (id) => {
    const res = await fetch(`${API_URL}?action=update_shopping_item`, {
      method: 'POST',
      body: JSON.stringify({ delete: true, id })
    });
    setShoppingList(await res.json());
  };

  if (loading) return <div className="loading">Sincronizando Hogar...</div>;

  return (
    <div className="family-container">
      <header>
        <div className="branding">
          <h1>TaskFlow<span>PRO</span></h1>
          <p>Misión: Logística Familiar</p>
        </div>
        <nav className="tabs">
          <button 
            className={activeTab === 'routine' ? 'active' : ''} 
            onClick={() => setActiveTab('routine')}
          >
            📅 Rutina Diaria
          </button>
          <button 
            className={activeTab === 'shopping' ? 'active' : ''} 
            onClick={() => setActiveTab('shopping')}
          >
            🛒 Lista de Compra
          </button>
        </nav>
      </header>

      <main className="content glass-panel">
        {activeTab === 'routine' ? (
          <div className="routine-view">
            <div className="timeline">
              {familyTasks.map(task => (
                <div key={task.id} className={`task-card ${task.done ? 'done' : ''}`} onClick={() => toggleTask(task.id, task.done)}>
                  <span className="time">{task.time}</span>
                  <div className="task-info">
                    <h3>{task.title}</h3>
                    <span className="category">{task.category}</span>
                  </div>
                  <div className="checkbox">
                    {task.done ? '✓' : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="shopping-view">
            <form className="add-item" onSubmit={addShoppingItem}>
              <input 
                type="text" 
                placeholder="Añadir a la cesta..." 
                value={newItem}
                onChange={(e) => setNewItem(e.target.value)}
              />
              <button type="submit">+</button>
            </form>
            <div className="items-list">
              {shoppingList.map(item => (
                <div key={item.id} className={`shopping-item ${item.bought ? 'bought' : ''}`}>
                  <span className="check" onClick={() => toggleShopping(item.id, item.bought)}>
                    {item.bought ? '🔘' : '⚪'}
                  </span>
                  <span className="name">{item.name}</span>
                  <span className="category-tag">{item.category}</span>
                  <button className="del" onClick={() => deleteShoppingItem(item.id)}>×</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer>
        <div className="status-bar">
          <span>{familyTasks.filter(t => t.done).length}/{familyTasks.length} Tareas</span>
          <span>{shoppingList.filter(i => i.bought).length}/{shoppingList.length} Comprados</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
