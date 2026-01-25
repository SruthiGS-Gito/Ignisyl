import React, { useState, useEffect, useMemo } from 'react';
import { reportAPI, userAPI } from '../../services/api';
import Sidebar from '../Common/Sidebar';
import Loading from '../Common/Loading';
import { useToast } from '../Common/Toast';
import '../Admin/AdminDashboard.css';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState({});
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [dateRange, setDateRange] = useState('7days');
  const [generatingBulk, setGeneratingBulk] = useState(false);
  const [generationProgress, setGenerationProgress] = useState({ active: false, current: 0, total: 8, section: '' });
  const toast = useToast();

  // Simulate report generation progress
  const simulateProgress = (callback) => {
    const sections = [
      'Header & Metadata',
      'User Profile',
      'Activity History',
      'Threat Analysis',
      'Behavioral Patterns',
      'ML Predictions',
      'Actions Taken',
      'Executive Summary'
    ];

    setGenerationProgress({ active: true, current: 0, total: 8, section: sections[0] });

    let currentSection = 0;
    const interval = setInterval(() => {
      currentSection++;
      if (currentSection < sections.length) {
        setGenerationProgress({
          active: true,
          current: currentSection,
          total: 8,
          section: sections[currentSection]
        });
      } else {
        clearInterval(interval);
      }
    }, 400); // Progress every 400ms

    return () => {
      clearInterval(interval);
      setGenerationProgress({ active: false, current: 0, total: 8, section: '' });
    };
  };

  // Get high-risk users (risk score >= 60)
  const highRiskUsers = users.filter(u => (u.current_risk_score || 0) >= 60);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [reportsRes, usersRes] = await Promise.all([
        reportAPI.listReports(),
        userAPI.getUsers()
      ]);
      setReports(reportsRes.data.reports || []);
      setUsers(usersRes.data.users || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const loadReports = async () => {
    try {
      const response = await reportAPI.listReports();
      setReports(response.data.reports || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading reports:', error);
      setLoading(false);
    }
  };

  // Filter users based on search query
  const filteredUsers = useMemo(() => {
    if (!userSearchQuery.trim()) return users;
    const query = userSearchQuery.toLowerCase();
    return users.filter(user =>
      user.username?.toLowerCase().includes(query) ||
      user.full_name?.toLowerCase().includes(query) ||
      user.email?.toLowerCase().includes(query) ||
      user.department?.toLowerCase().includes(query)
    );
  }, [users, userSearchQuery]);

  // Get selected user details - use user_id (string) instead of id
  const selectedUser = useMemo(() => {
    if (!selectedUserId) return null;
    return users.find(u => u.user_id === selectedUserId);
  }, [users, selectedUserId]);

  // Get risk level color and label
  const getRiskLevel = (score) => {
    if (score >= 75) return { level: 'CRITICAL', color: '#8b0000', bg: 'rgba(139, 0, 0, 0.2)' };
    if (score >= 50) return { level: 'HIGH', color: '#dc3545', bg: 'rgba(220, 53, 69, 0.2)' };
    if (score >= 30) return { level: 'MEDIUM', color: '#ff8c00', bg: 'rgba(255, 140, 0, 0.2)' };
    return { level: 'LOW', color: '#28a745', bg: 'rgba(40, 167, 69, 0.2)' };
  };

  const generateReport = async (type, title) => {
    setGenerating(prev => ({ ...prev, [type]: true }));
    const cleanup = simulateProgress();

    try {
      // Pass date range to API for filtering
      const response = await reportAPI.generateReport(type, { date_range: dateRange });

      // response.data is already a Blob - use it directly
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `IGNISYL_${type}_Report_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success(`${title} generated successfully!`);
      loadReports();
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error('Failed to generate report: ' + (error.response?.data?.detail || error.message));
    }
    cleanup();
    setGenerating(prev => ({ ...prev, [type]: false }));
  };

  const handleGenerateUserReport = () => {
    if (!selectedUserId) {
      toast.error('Please select a user');
      return;
    }
    setShowConfirmDialog(true);
  };

  const confirmGenerateUserReport = async () => {
    setShowConfirmDialog(false);

    if (!selectedUserId) {
      toast.error('Please select a user');
      return;
    }

    setGenerating(prev => ({ ...prev, user_report: true }));
    try {
      const response = await reportAPI.generateUserReport(selectedUserId);

      // response.data is already a Blob - use it directly
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      const username = selectedUser ? selectedUser.username : 'user';
      a.download = `IGNISYL_User_Report_${username}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success('Individual User Report generated successfully!');
      loadReports();
    } catch (error) {
      console.error('Error generating user report:', error);
      toast.error('Failed to generate user report: ' + (error.response?.data?.detail || error.message));
    }
    setGenerating(prev => ({ ...prev, user_report: false }));
  };

  const downloadReport = async (filename) => {
    try {
      const response = await reportAPI.downloadReport(filename);
      // response.data is already a Blob - use it directly
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded!');
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  // Generate reports for all high-risk users
  const generateHighRiskReports = async () => {
    if (highRiskUsers.length === 0) {
      toast.warning('No high-risk users found (risk score >= 60)');
      return;
    }

    if (!window.confirm(`Generate reports for ${highRiskUsers.length} high-risk user(s)?`)) {
      return;
    }

    setGeneratingBulk(true);
    let successCount = 0;
    let failCount = 0;

    for (const user of highRiskUsers) {
      try {
        const response = await reportAPI.generateUserReport(user.user_id);
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = `IGNISYL_User_Report_${user.username}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        successCount++;
      } catch (error) {
        console.error(`Failed to generate report for ${user.username}:`, error);
        failCount++;
      }
    }

    setGeneratingBulk(false);
    loadReports();

    if (failCount === 0) {
      toast.success(`Generated ${successCount} reports successfully!`);
    } else {
      toast.warning(`Generated ${successCount} reports, ${failCount} failed`);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Extract report type from filename
  const getReportType = (filename) => {
    if (filename.includes('comprehensive')) return { type: 'Comprehensive', icon: '📊', color: '#667eea' };
    if (filename.includes('individual') || filename.includes('threat_report')) return { type: 'User Report', icon: '👤', color: '#28a745' };
    if (filename.includes('ml_report') || filename.includes('ml_performance')) return { type: 'ML Performance', icon: '📈', color: '#17a2b8' };
    if (filename.includes('threat_summary')) return { type: 'Threat Summary', icon: '🚨', color: '#dc3545' };
    if (filename.includes('user_activity') || filename.includes('activity')) return { type: 'Activity Report', icon: '👥', color: '#ffc107' };
    if (filename.includes('system')) return { type: 'System Report', icon: '🖥️', color: '#6c757d' };
    return { type: 'Report', icon: '📄', color: '#6c757d' };
  };

  if (loading) {
    return <Loading message="Loading reports..." fullScreen={true} />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />
      <div className="admin-main">
        <div className="admin-header">
          <div>
            <h1 className="admin-title">Reports</h1>
            <p className="admin-subtitle">Generate and download security reports</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ color: '#a8d0ff', fontSize: '13px' }}>Date Range:</label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#1a252f',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '13px'
                }}
              >
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>
          </div>
        </div>

        {/* Report Generation Cards */}
        <div className="admin-card" style={{ marginBottom: '24px' }}>
          <h3 className="card-title">Generate New Report</h3>
          <div className="reports-grid">
            <div className="report-card">
              <div className="report-icon">📊</div>
              <div className="report-title">Comprehensive Report</div>
              <div className="report-desc">
                Full threat analysis with user risk scores and system recommendations
              </div>
              <button
                className="btn-admin btn-primary"
                onClick={() => generateReport('comprehensive', 'Comprehensive Report')}
                disabled={generating.comprehensive}
              >
                {generating.comprehensive ? 'Generating...' : 'Generate PDF'}
              </button>
            </div>

            <div className="report-card">
              <div className="report-icon">👥</div>
              <div className="report-title">User Activity Report</div>
              <div className="report-desc">
                Detailed user activity logs and behavioral patterns analysis
              </div>
              <button
                className="btn-admin btn-primary"
                onClick={() => generateReport('user_activity', 'User Activity Report')}
                disabled={generating.user_activity}
              >
                {generating.user_activity ? 'Generating...' : 'Generate PDF'}
              </button>
            </div>

            <div className="report-card">
              <div className="report-icon">🚨</div>
              <div className="report-title">Threat Summary</div>
              <div className="report-desc">
                Summary of all detected threats, severity levels, and actions taken
              </div>
              <button
                className="btn-admin btn-primary"
                onClick={() => generateReport('threat_summary', 'Threat Summary')}
                disabled={generating.threat_summary}
              >
                {generating.threat_summary ? 'Generating...' : 'Generate PDF'}
              </button>
            </div>

            <div className="report-card">
              <div className="report-icon">📈</div>
              <div className="report-title">ML Performance</div>
              <div className="report-desc">
                Machine learning model accuracy, detection rates, and performance metrics
              </div>
              <button
                className="btn-admin btn-primary"
                onClick={() => generateReport('ml_performance', 'ML Performance Report')}
                disabled={generating.ml_performance}
              >
                {generating.ml_performance ? 'Generating...' : 'Generate PDF'}
              </button>
            </div>

            {/* High-Risk User Reports - Full Width Professional Card */}
            <div className="report-card" style={{ gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '16px' }}>
                <div className="report-icon" style={{ color: '#dc3545', fontSize: '32px' }}>&#9888;</div>
                <div style={{ flex: 1 }}>
                  <div className="report-title" style={{ marginBottom: '8px' }}>High-Risk User Reports</div>
                  <div className="report-desc" style={{ marginBottom: '0' }}>
                    Generate comprehensive security reports for users with risk score &ge; 60.
                    These reports are suitable for HR review, legal documentation, and security audits.
                  </div>
                </div>
                <div style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  backgroundColor: highRiskUsers.length > 0 ? 'rgba(220, 53, 69, 0.2)' : 'rgba(40, 167, 69, 0.2)',
                  border: `1px solid ${highRiskUsers.length > 0 ? 'rgba(220, 53, 69, 0.4)' : 'rgba(40, 167, 69, 0.4)'}`,
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: highRiskUsers.length > 0 ? '#dc3545' : '#28a745' }}>
                    {highRiskUsers.length}
                  </div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.7)' }}>
                    {highRiskUsers.length === 1 ? 'User' : 'Users'}
                  </div>
                </div>
              </div>

              {/* High-Risk Users List */}
              {highRiskUsers.length > 0 ? (
                <div style={{
                  backgroundColor: 'rgba(0,0,0,0.2)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{ fontSize: '12px', color: '#a8d0ff', marginBottom: '10px', fontWeight: 'bold' }}>
                    Detected High-Risk Users:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {highRiskUsers.map((user, idx) => {
                      const riskScore = user.current_risk_score || 0;
                      const riskInfo = getRiskLevel(riskScore);
                      return (
                        <div key={user.user_id || idx} style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 12px',
                          backgroundColor: 'rgba(255,255,255,0.03)',
                          borderRadius: '6px',
                          borderLeft: `3px solid ${riskInfo.color}`
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{
                              width: '36px',
                              height: '36px',
                              borderRadius: '50%',
                              backgroundColor: `${riskInfo.color}30`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: riskInfo.color,
                              fontWeight: 'bold',
                              fontSize: '14px'
                            }}>
                              {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div style={{ fontWeight: 'bold', color: '#fff', fontSize: '14px' }}>
                                {user.full_name || user.username}
                              </div>
                              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                                {user.department || 'N/A'} &bull; {user.role || 'N/A'}
                              </div>
                            </div>
                          </div>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px'
                          }}>
                            <div style={{
                              padding: '4px 10px',
                              borderRadius: '4px',
                              backgroundColor: riskInfo.bg,
                              border: `1px solid ${riskInfo.color}`,
                              color: riskInfo.color,
                              fontWeight: 'bold',
                              fontSize: '12px'
                            }}>
                              {riskInfo.level}
                            </div>
                            <div style={{
                              fontWeight: 'bold',
                              fontSize: '16px',
                              color: riskInfo.color,
                              minWidth: '50px',
                              textAlign: 'right'
                            }}>
                              {riskScore.toFixed(0)}/100
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div style={{
                  backgroundColor: 'rgba(40, 167, 69, 0.1)',
                  borderRadius: '8px',
                  padding: '20px',
                  marginBottom: '16px',
                  textAlign: 'center',
                  border: '1px solid rgba(40, 167, 69, 0.3)'
                }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>&#10003;</div>
                  <div style={{ color: '#28a745', fontWeight: 'bold', marginBottom: '4px' }}>
                    No High-Risk Users Detected
                  </div>
                  <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
                    All users are currently within acceptable risk thresholds
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  className="btn-admin btn-primary"
                  onClick={generateHighRiskReports}
                  disabled={highRiskUsers.length === 0 || generatingBulk}
                  style={{
                    flex: 1,
                    padding: '12px',
                    backgroundColor: highRiskUsers.length > 0 ? '#dc3545' : 'rgba(255,255,255,0.1)',
                    opacity: highRiskUsers.length === 0 ? 0.5 : 1
                  }}
                >
                  {generatingBulk
                    ? 'Generating Reports...'
                    : highRiskUsers.length === 0
                      ? 'No Reports to Generate'
                      : `Generate All Reports (${highRiskUsers.length})`
                  }
                </button>
                {highRiskUsers.length > 0 && (
                  <select
                    className="admin-select"
                    onChange={(e) => {
                      if (e.target.value) {
                        setSelectedUserId(e.target.value);
                        setShowConfirmDialog(true);
                      }
                    }}
                    value=""
                    style={{
                      flex: 1,
                      padding: '12px',
                      backgroundColor: '#1a252f',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">Select Individual User...</option>
                    {highRiskUsers.map(user => (
                      <option key={user.user_id} value={user.user_id}>
                        {user.full_name || user.username} (Risk: {(user.current_risk_score || 0).toFixed(0)})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Enhanced Individual User Report Card */}
            <div className="report-card" style={{ gridColumn: 'span 2' }}>
              <div className="report-icon">👤</div>
              <div className="report-title">Individual User Report</div>
              <div className="report-desc">
                Comprehensive 8-section security report including threat analysis, behavioral patterns,
                ML predictions, and executive summary. Suitable for legal/HR/audit purposes.
              </div>

              {/* Search Input */}
              <div style={{ marginTop: '16px' }}>
                <input
                  type="text"
                  placeholder="Search users by name, username, email, or department..."
                  value={userSearchQuery}
                  onChange={(e) => setUserSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '14px',
                    marginBottom: '12px'
                  }}
                />

                {/* User Dropdown */}
                <select
                  className="admin-select"
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#1a252f',
                    border: '1px solid rgba(102, 126, 234, 0.4)',
                    borderRadius: '8px',
                    color: '#ffffff',
                    fontSize: '14px',
                    cursor: 'pointer',
                    appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23a8d0ff' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center'
                  }}
                >
                  <option value="" style={{ backgroundColor: '#1a252f', color: '#a8d0ff' }}>
                    -- Select User ({filteredUsers.length} users) --
                  </option>
                  {filteredUsers.map(user => {
                    const riskScore = user.current_risk_score || 0;
                    const risk = getRiskLevel(riskScore);
                    return (
                      <option
                        key={user.user_id}
                        value={user.user_id}
                        style={{
                          backgroundColor: '#1a252f',
                          color: risk.color,
                          padding: '8px'
                        }}
                      >
                        {user.full_name || user.username} | {user.department || 'N/A'} | Risk: {riskScore} ({risk.level})
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* User Preview Card */}
              {selectedUser && (() => {
                const riskScore = selectedUser.current_risk_score || 0;
                const riskInfo = getRiskLevel(riskScore);
                return (
                <div style={{
                  marginTop: '16px',
                  padding: '16px',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: '8px',
                  border: `1px solid ${riskInfo.color}40`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginBottom: '4px' }}>
                        {selectedUser.full_name || selectedUser.username}
                      </div>
                      <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>
                        {selectedUser.email || 'No email'} | {selectedUser.department || 'No department'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                        Role: {selectedUser.role || 'N/A'} | Status: {selectedUser.status || 'Active'}
                      </div>
                    </div>
                    <div style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      backgroundColor: riskInfo.bg,
                      border: `1px solid ${riskInfo.color}`,
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: riskInfo.color }}>
                        {riskScore}
                      </div>
                      <div style={{ fontSize: '11px', color: riskInfo.color, fontWeight: 'bold' }}>
                        {riskInfo.level} RISK
                      </div>
                    </div>
                  </div>
                </div>
              );})()}

              {/* Generate Button */}
              <div style={{ marginTop: '16px' }}>
                <button
                  className="btn-admin btn-primary"
                  onClick={handleGenerateUserReport}
                  disabled={!selectedUserId || generating.user_report}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {generating.user_report ? (
                    <>
                      <span className="spinner" style={{
                        width: '18px',
                        height: '18px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTop: '2px solid #fff',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }}></span>
                      Generating Comprehensive Report...
                    </>
                  ) : (
                    <>
                      📋 Generate Individual User Report
                    </>
                  )}
                </button>
              </div>

              {/* Report Contents Info */}
              <div style={{
                marginTop: '12px',
                padding: '12px',
                backgroundColor: 'rgba(30, 60, 114, 0.2)',
                borderRadius: '6px',
                fontSize: '12px',
                color: 'rgba(255,255,255,0.6)'
              }}>
                <strong style={{ color: 'rgba(255,255,255,0.8)' }}>Report Contents:</strong>
                <div style={{ marginTop: '6px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                  <span>1. User Profile</span>
                  <span>5. ML Model Predictions</span>
                  <span>2. Activity History</span>
                  <span>6. Actions Taken</span>
                  <span>3. Threat Analysis</span>
                  <span>7. Recommendations</span>
                  <span>4. Behavioral Analysis</span>
                  <span>8. Executive Summary</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Previous Reports */}
        <div className="admin-card">
          <h3 className="card-title">Previous Reports ({reports.length})</h3>
          {reports.length === 0 ? (
            <div className="empty-state">
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
              <div style={{ fontSize: '16px', marginBottom: '8px' }}>No reports generated yet</div>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)' }}>
                Generate a report above to see it here
              </div>
            </div>
          ) : (
            <div className="users-table-container">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((report, index) => {
                    const reportInfo = getReportType(report.filename);
                    return (
                      <tr key={index}>
                        <td>
                          <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            backgroundColor: `${reportInfo.color}20`,
                            border: `1px solid ${reportInfo.color}40`
                          }}>
                            <span>{reportInfo.icon}</span>
                            <span style={{ color: reportInfo.color, fontSize: '12px', fontWeight: 'bold' }}>
                              {reportInfo.type}
                            </span>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '20px' }}>📄</span>
                            <span style={{ fontSize: '13px' }}>{report.filename}</span>
                          </div>
                        </td>
                        <td>{formatFileSize(report.size_bytes)}</td>
                        <td>{new Date(report.created_at).toLocaleString()}</td>
                        <td>
                          <button
                            className="btn-admin btn-primary"
                            style={{ padding: '6px 12px', fontSize: '13px' }}
                            onClick={() => downloadReport(report.filename)}
                          >
                            Download
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && selectedUser && (() => {
        const dialogRiskScore = selectedUser.current_risk_score || 0;
        const dialogRiskInfo = getRiskLevel(dialogRiskScore);
        return (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '500px',
            width: '90%',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h3 style={{ color: '#fff', marginBottom: '16px', fontSize: '20px' }}>
              Confirm Report Generation
            </h3>
            <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '20px' }}>
              Generate a comprehensive security report for:
            </p>

            <div style={{
              backgroundColor: 'rgba(255,255,255,0.05)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '20px'
            }}>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginBottom: '4px' }}>
                {selectedUser.full_name || selectedUser.username}
              </div>
              <div style={{ fontSize: '14px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>
                {selectedUser.department || 'No department'} | {selectedUser.role || 'No role'}
              </div>
              <div style={{
                display: 'inline-block',
                padding: '4px 12px',
                borderRadius: '4px',
                backgroundColor: dialogRiskInfo.bg,
                color: dialogRiskInfo.color,
                fontWeight: 'bold',
                fontSize: '13px'
              }}>
                Risk Score: {dialogRiskScore} ({dialogRiskInfo.level})
              </div>
            </div>

            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', marginBottom: '20px' }}>
              This will generate an 8-section PDF report suitable for legal, HR, and audit purposes.
              The report will be automatically downloaded when complete.
            </p>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                className="btn-admin"
                onClick={() => setShowConfirmDialog(false)}
                style={{
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  color: '#fff',
                  padding: '10px 20px'
                }}
              >
                Cancel
              </button>
              <button
                className="btn-admin btn-primary"
                onClick={confirmGenerateUserReport}
                style={{ padding: '10px 20px' }}
              >
                Generate Report
              </button>
            </div>
          </div>
        </div>
      );})()}

      {/* Report Generation Progress Overlay */}
      {generationProgress.active && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '400px',
            width: '90%',
            textAlign: 'center',
            border: '1px solid rgba(102, 126, 234, 0.3)'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              border: '4px solid rgba(102, 126, 234, 0.2)',
              borderTop: '4px solid #667eea',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>

            <h3 style={{ color: '#fff', marginBottom: '8px', fontSize: '18px' }}>
              Generating Report...
            </h3>

            <div style={{
              color: '#667eea',
              fontSize: '14px',
              marginBottom: '16px'
            }}>
              {generationProgress.current + 1}/{generationProgress.total} sections complete
            </div>

            <div style={{
              height: '8px',
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '12px'
            }}>
              <div style={{
                height: '100%',
                width: `${((generationProgress.current + 1) / generationProgress.total) * 100}%`,
                backgroundColor: '#667eea',
                transition: 'width 0.3s ease',
                borderRadius: '4px'
              }}></div>
            </div>

            <div style={{
              color: 'rgba(255,255,255,0.6)',
              fontSize: '13px'
            }}>
              Processing: {generationProgress.section}
            </div>
          </div>
        </div>
      )}

      {/* CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Reports;
