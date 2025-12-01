import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const RiskChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No risk data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="user" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="risk_score" fill="#ff9800" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default RiskChart;
