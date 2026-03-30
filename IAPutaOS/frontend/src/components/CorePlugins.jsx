import React from 'react';

const CorePlugins = ({ plugins }) => {
  return (
    <div className="side-panel right-panel">
      <div className="panel-header">CORE PLUGINS</div>
      <div className="plugins-list">
        {plugins.map(plugin => (
          <div key={plugin.id} className="plugin-item">
            <span className="plugin-label">{plugin.label}</span>
            <span className="plugin-status" style={{ color: plugin.color }}>[{plugin.status}]</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CorePlugins;
