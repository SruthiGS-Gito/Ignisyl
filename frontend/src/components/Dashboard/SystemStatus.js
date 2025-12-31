import React from 'react';

const SystemStatus = ({ systemHealth }) => {
  return (
    <div className="section-card">
      <h2 className="text-2xl font-bold mb-4">⚙️ System Status</h2>
      <div className="health-grid">
        {/* CPU Item */}
        <div className="health-item">
          <div className="health-label">CPU Usage</div>
          <div className={`health-value ${systemHealth.cpu_usage > 80 ? 'danger' : systemHealth.cpu_usage > 60 ? 'warning' : ''}`}>
            {(systemHealth.cpu_usage || 0).toFixed(1)}%
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${systemHealth.cpu_usage > 80 ? 'red' : systemHealth.cpu_usage > 60 ? 'yellow' : 'green'}`}
              style={{width: `${systemHealth.cpu_usage || 0}%`}}
            ></div>
          </div>
        </div>

        {/* Memory Item */}
        <div className="health-item">
          <div className="health-label">Memory</div>
          <div className={`health-value ${systemHealth.memory_usage > 80 ? 'danger' : systemHealth.memory_usage > 60 ? 'warning' : ''}`}>
            {(systemHealth.memory_usage || 0).toFixed(1)}%
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${systemHealth.memory_usage > 80 ? 'red' : systemHealth.memory_usage > 60 ? 'yellow' : 'green'}`}
              style={{width: `${systemHealth.memory_usage || 0}%`}}
            ></div>
          </div>
        </div>

        {/* Disk Item */}
        <div className="health-item">
          <div className="health-label">Disk</div>
          <div className={`health-value ${systemHealth.disk_usage > 80 ? 'danger' : systemHealth.disk_usage > 60 ? 'warning' : ''}`}>
            {(systemHealth.disk_usage || 0).toFixed(1)}%
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${systemHealth.disk_usage > 80 ? 'red' : systemHealth.disk_usage > 60 ? 'yellow' : 'green'}`}
              style={{width: `${systemHealth.disk_usage || 0}%`}}
            ></div>
          </div>
        </div>

        {/* Network Item */}
        <div className="health-item">
          <div className="health-label">Network (MB)</div>
          <div className="health-value">
            {(systemHealth.network_throughput || 0).toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;