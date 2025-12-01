import React from 'react';

const ThreatMap = ({ threats }) => {
  if (!threats || threats.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No threats to display
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {threats.map((threat, index) => (
        <div
          key={index}
          className="p-4 bg-red-50 border-l-4 border-red-500 rounded"
        >
          <div className="flex justify-between items-center">
            <div>
              <div className="font-bold">{threat.user}</div>
              <div className="text-sm text-gray-600">{threat.type}</div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-red-600">
                {threat.risk_score}
              </div>
              <div className="text-xs text-gray-500">{threat.time}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ThreatMap;
