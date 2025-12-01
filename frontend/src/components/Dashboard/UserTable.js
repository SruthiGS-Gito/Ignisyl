import React from 'react';
import { getRiskLevelDetails } from '../../utils/helpers';

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

  const users = Object.values(userStats).map((user) => ({
    ...user,
    avgRisk: Math.round(user.totalRisk / user.activities),
  }));

  // Sort by max risk (descending)
  users.sort((a, b) => b.maxRisk - a.maxRisk);

  return (
    <div className="activity-card">
      <h2 className="text-2xl font-bold mb-6">👥 High-Risk Users</h2>

      {users.length === 0 ? (
        <div className="text-center py-12 text-blue-200">
          <div className="text-6xl mb-4">✓</div>
          <div className="text-xl">No user data available</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {users.slice(0, 5).map((user, index) => {
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
