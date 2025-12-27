import React from 'react';
import { getRiskLevelDetails } from '../../utils/helpers';

const HIGH_RISK_THRESHOLD = 60; // Only show users with risk score >= 60

const UserTable = ({ activities }) => {
  // Group activities by user
  const userStats = {};

  activities.forEach((activity) => {
    const userId = activity.full_name;
    if (!userStats[userId]) {
      userStats[userId] = {
        name: userId,
        activities: 0,
        totalRisk: 0,
        maxRisk: 0,
      };
    }
    userStats[userId].activities += 1;
    userStats[userId].totalRisk += activity.risk_score;
    userStats[userId].maxRisk = Math.max(userStats[userId].maxRisk, activity.risk_score);
  });

  const allUsers = Object.values(userStats).map((user) => ({
    ...user,
    avgRisk: Math.round(user.totalRisk / user.activities),
  }));

  // FILTER: Only show users with maxRisk >= 60 (High/Critical risk)
  const highRiskUsers = allUsers.filter(user => user.maxRisk >= HIGH_RISK_THRESHOLD);

  // Sort by max risk (descending) - highest risk first
  highRiskUsers.sort((a, b) => b.maxRisk - a.maxRisk);

  return (
    <div className="activity-card">
      <h2 className="text-2xl font-bold mb-6">
        {highRiskUsers.length > 0 ? '🚨 High-Risk Users' : '👥 High-Risk Users'}
      </h2>

      {highRiskUsers.length === 0 ? (
        <div className="text-center py-12 text-blue-200">
          <div className="text-6xl mb-4">🛡️</div>
          <div className="text-xl font-semibold" style={{color: '#4ade80'}}>No high-risk users detected</div>
          <div className="text-sm mt-2" style={{color: '#86efac'}}>System secure - all users within normal risk parameters</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {highRiskUsers.slice(0, 5).map((user, index) => {
            const riskDetails = getRiskLevelDetails(user.maxRisk);
            return (
              <div
                key={index}
                className="activity-item"
                style={{ borderLeft: `4px solid ${riskDetails.textColor}` }}
              >
                <div className="flex-1">
                  <div className="font-bold text-lg">{user.name}</div>
                  <div className="text-blue-200 text-sm">
                    {user.activities} activities | Avg Risk: {user.avgRisk}
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className="text-3xl font-bold mb-1"
                    style={{ color: riskDetails.textColor }}
                  >
                    {user.maxRisk}
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

export default UserTable;
