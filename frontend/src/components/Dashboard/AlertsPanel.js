import React from 'react';
import { formatTimestamp, getRiskLevelDetails } from '../../utils/helpers';

const AlertsPanel = ({ activities, onRefresh }) => {
  return (
    <div className="activity-card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">🚨 Recent Threat Alerts</h2>
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-blue-500 bg-opacity-50 hover:bg-opacity-70 rounded-lg transition"
        >
          Refresh
        </button>
      </div>

      {activities.length === 0 ? (
        <div className="text-center py-12 text-blue-200">
          <div className="text-6xl mb-4">✓</div>
          <div className="text-xl">No recent threats detected</div>
          <div className="text-sm mt-2">System is monitoring...</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {activities.map((activity, index) => {
            const riskDetails = getRiskLevelDetails(activity.risk_score);
            return (
              <div
                key={index}
                className="activity-item animate-slideIn"
                style={{ borderLeft: `4px solid ${riskDetails.textColor}` }}
              >
                <div className="flex-1">
                  <div className="font-bold text-lg">{activity.full_name}</div>
                  <div className="text-blue-200 text-sm">{activity.activity}</div>
                  <div className="text-xs text-blue-300 mt-1">
                    {formatTimestamp(activity.timestamp)}
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className="text-3xl font-bold mb-1"
                    style={{ color: riskDetails.textColor }}
                  >
                    {activity.risk_score}
                  </div>
                  <div
                    className={`risk-badge ${riskDetails.label.toLowerCase()}`}
                  >
                    {riskDetails.label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AlertsPanel;
