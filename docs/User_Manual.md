<<<START User_Manual.md>>>
# IGNISYL - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Roles](#user-roles)
4. [Login & Authentication](#login--authentication)
5. [Dashboard Overview](#dashboard-overview)
6. [User Management](#user-management)
7. [Activity Monitoring](#activity-monitoring)
8. [Alert Management](#alert-management)
9. [Analyst Control Panel](#analyst-control-panel)
10. [Report Generation](#report-generation)
11. [System Status](#system-status)
12. [Best Practices](#best-practices)
13. [FAQ](#faq)

---

## Introduction

**IGNISYL** is an AI-powered insider threat detection and adaptive firewall system designed to protect organizations from internal security threats. This manual will guide you through using the system effectively.

### Key Features
- ✅ Real-time threat detection using ML ensemble
- ✅ 4-tier graduated response framework (ALLOW/MONITOR/RESTRICT/BLOCK)
- ✅ Professional PDF report generation (4 report types)
- ✅ Live activity monitoring dashboard with WebSocket updates
- ✅ Role-based access control
- ✅ Analyst decision queue for HIGH-risk threats

---

## Getting Started

### System Access

**URL:** http://localhost:3000 (or your organization's deployed URL)

**Default Credentials:**
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Analyst | sruthi_g_s | analyst123 |

⚠️ **Security Notice:** Change default passwords immediately after first login!

---

## User Roles

### 1. Admin
**Permissions:**
- ✅ Full system access
- ✅ User management (create, edit, delete users)
- ✅ View all activities and alerts
- ✅ Generate all types of reports
- ✅ Configure system settings
- ✅ Override any firewall action (all 4 tiers)
- ❌ Cannot manage ML models directly (backend only)

### 2. Security Analyst
**Permissions:**
- ✅ View dashboard and all activities
- ✅ Monitor real-time threats
- ✅ Generate user-specific reports
- ✅ Acknowledge and resolve alerts
- ❌ Cannot create/delete users
- ❌ Cannot modify global system settings

**What Analysts CAN Do:**
- ✅ View pending threats (risk 51-75)
- ✅ Apply actions: ALLOW, RESTRICT (with reason), BLOCK
- ✅ Contact users (notification logging)
- ✅ Escalate to admin/manager (notification logging)
- ✅ View audit trail of their actions

**What Analysts CANNOT Do:**
- ❌ Custom firewall restrictions (block external only, rate limits, etc.) - *Future Feature*
- ❌ Real-time network enforcement - *Requires agent deployment*
- ❌ USB device control - *Requires endpoint agent*

---

## Login & Authentication

### Step 1: Access Login Page

Navigate to http://localhost:3000

You'll see the **IGNISYL Login Page** with:
- Username field
- Password field
- "Remember Me" checkbox
- Login button

### Step 2: Enter Credentials

Username: admin
Password: admin123

### Step 3: First-Time Setup

**Change Your Password:**

1. After login, click **Profile** (top-right corner)
2. Select **Change Password**
3. Enter:
   - Current Password
   - New Password (min 8 characters)
   - Confirm New Password
4. Click **Update Password**

### Step 4: Session Management

- **Session Duration:** 30 minutes of inactivity
- **Auto-Logout:** Yes, after session expires
- **Remember Me:** Keeps you logged in for 7 days

---

## Dashboard Overview

### Main Dashboard

After login, you'll see the main dashboard with:

#### 1. Statistics Cards (Top Row)
- **Total Users** - Number of monitored users
- **High-Risk Activities** - Count of high-risk events today
- **Active Alerts** - Unresolved alerts
- **Blocked Users** - Users currently blocked by firewall

#### 2. Real-Time Threat Feed (Center)
Live updates of detected threats with:
- User ID
- Activity Type
- Risk Score (0-100)
- Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
- Timestamp
- Action Taken

**Color Coding:**
- 🟢 **GREEN** - LOW risk (0-30) → ALLOW
- 🟡 **YELLOW** - MEDIUM risk (31-50) → MONITOR
- 🟠 **ORANGE** - HIGH risk (51-75) → RESTRICT (Analyst Decision)
- 🔴 **RED** - CRITICAL risk (76-100) → BLOCK (Auto)

#### 3. Risk Score Chart (Right)
Line chart showing risk scores over time for quick trend analysis.

#### 4. Recent Activities Table (Bottom)
Latest user activities with:
- User
- Activity Type
- Timestamp
- Risk Level
- Action button (View Details)

---

## User Management

*(Admin Only)*

### View All Users

1. Click **Users** in the navigation menu
2. You'll see a table with all users:
   - User ID
   - Username
   - Full Name
   - Department
   - Role
   - Email
   - Actions (Edit, Delete)

### Add New User

1. Click **+ Add User** button
2. Fill in the form:
   - **Username** (required, 3-50 characters)
   - **Password** (required, min 8 characters)
   - **Full Name** (required)
   - **Email** (required, valid email format)
   - **Department** (e.g., Finance, IT, HR)
   - **Role** (Admin or Analyst)
3. Click **Create User**

**Example:**

Username: john_doe
Password: SecurePass123!
Full Name: John Doe
Email: john.doe@ignisyl.demo
Department: Finance
Role: Analyst

### Edit User

1. Click **Edit** button next to user
2. Modify fields (except username)
3. Click **Update User**

### Delete User

1. Click **Delete** button next to user
2. Confirm deletion in popup
3. User and all their activities will be removed

---

## Activity Monitoring

### View All Activities

1. Click **Activities** in navigation menu
2. You'll see all logged activities with:
   - Timestamp
   - User
   - Activity Type
   - Risk Score
   - Risk Level
   - Source IP
   - Details

### Filter Activities

**By User:**
1. Select user from dropdown
2. Click **Filter**

**By Risk Level:**
1. Select risk level (LOW, MEDIUM, HIGH, CRITICAL)
2. Click **Apply**

**By Date Range:**
1. Select start date
2. Select end date
3. Click **Filter**

### Activity Types

The system monitors:
- **file_access** - File operations
- **network_access** - Network connections
- **login** - Authentication attempts
- **data_transfer** - Large data movements
- **privilege_escalation** - Permission changes
- **usb_device** - USB device usage
- **honeypot_access** - Decoy file access (CRITICAL)

### View Activity Details

1. Click on any activity row
2. Modal popup shows:
   - Complete activity information
   - ML model scores (Isolation Forest, Autoencoder, XGBoost)
   - Risk factors triggered
   - Contextual modifiers applied
   - Recommended action
   - Actual action taken

---

## Alert Management

### View Alerts

1. Click **Alerts** in navigation menu
2. You'll see all alerts with:
   - Alert ID
   - User
   - Risk Score
   - Priority (LOW, MEDIUM, HIGH, CRITICAL)
   - Status (Active, Acknowledged, Resolved)
   - Created At
   - Actions

### Alert Priorities

Automatically assigned based on risk score:
- **LOW** - Risk Score 0-30 → ALLOW
- **MEDIUM** - Risk Score 31-50 → MONITOR
- **HIGH** - Risk Score 51-75 → RESTRICT (Analyst Decision Required)
- **CRITICAL** - Risk Score 76-100 → BLOCK (Auto)

### Alert Workflow

#### 1. Acknowledge Alert
1. Click **Acknowledge** button
2. Alert status changes to "Acknowledged"
3. Your username and timestamp are recorded

#### 2. Add Actions Taken
1. Click **Add Action** button
2. Enter action description:

Contacted user to verify activity.
Confirmed legitimate business need.

3. Click **Save**

#### 3. Resolve Alert
1. Click **Resolve** button
2. Add resolution notes:

False positive - User was working on month-end reports.
Updated baseline behavior model.

3. Click **Resolve Alert**

### Alert Statistics

View system-wide alert statistics:
- Total Alerts
- Active Alerts
- Resolved Alerts
- Priority Breakdown (graph)

---
## Analyst Control Panel

### Overview

When a HIGH-risk threat is detected (risk score 51-75), the system sends the threat to the **Analyst Decision Queue** for human review. This graduated approach prevents false positives while ensuring real threats are addressed.

### Accessing Pending Decisions

1. Navigate to **Dashboard** → **Active Threats** tab
2. Or click the **notification badge** when new threats appear
3. Threats are sorted by risk score (highest first)

### Available Actions

| Action | Use Case | Result |
|--------|----------|--------|
| **ALLOW** | False positive, legitimate activity | Alert cleared, logged |
| **RESTRICT** | Suspicious, needs investigation | Limited access, analyst notified |
| **BLOCK** | Confirmed threat | Complete block, incident logged |
| **Contact User** | Need explanation | Notification sent (logged) |
| **Escalate** | Need higher authority | Forwarded to admin/manager |

### Action Requirements

All actions require:
- **Reason:** Text explanation (mandatory)
- **Timestamp:** Automatically recorded
- **Analyst ID:** Automatically recorded

### Audit Trail

All analyst actions are logged for compliance:
- What action was taken
- Who took it
- When it was taken
- Why (justification required)
- Result of action

**View Action History:**
1. Navigate to **Activity Log** page
2. Filter by "Analyst Actions"
3. See complete history of decisions

---

## Report Generation

### Generate User Threat Report

1. Click **Reports** in navigation menu
2. Select **User Threat Report**
3. Fill in:
   - **User ID** (dropdown)
   - **Time Period** (24 hours, 7 days, 30 days, custom)
4. Click **Generate Report**

**Report Contents:**
- User information
- Activities summary (last 20 activities)
- Risk score statistics
- Triggered risk factors
- Recommendations
- Action taken breakdown

**Report Format:** PDF
**File Location:** `data/reports/threat_report_<user>_<timestamp>.pdf`

### Generate System Report

*(Admin Only)*

1. Select **System Report**
2. Choose time period
3. Click **Generate Report**

**Report Contents:**
- System overview
- Top 10 high-risk users
- All users summary
- System statistics
- Executive summary
- Overall recommendations

### Download Reports

1. After generation, click **Download** button
2. Report opens in browser for preview
3. Use browser's save/print function

### View Past Reports

1. Click **Report History** tab
2. See all previously generated reports
3. Click filename to download

---

## System Status

### Current Implementation

The system operates in **Simulation Mode** for academic demonstration:

| Component | Status | Notes |
|-----------|--------|-------|
| Dashboard | ✅ Active | Real-time metrics via WebSocket |
| ML Models | ✅ Active | Running on backend only |
| Detection | ✅ Active | Based on activity logs |
| Firewall Commands | ⚠️ Simulation | Generated but NOT executed |
| Network Enforcement | ❌ Not Active | Requires endpoint agent |

### What IS Working

- ✅ **Dashboard:** Shows real-time metrics and threat feed
- ✅ **ML Detection:** Ensemble model analyzes all activities
- ✅ **Risk Scoring:** 27 factors + 13 business modifiers
- ✅ **Graduated Response:** 4-tier automated classification
- ✅ **Analyst Actions:** Logged and displayed in UI
- ✅ **PDF Reports:** All 4 report types generate correctly
- ✅ **Audit Trail:** Complete action history

### What is SIMULATED

- ⚠️ **Firewall Commands:** System generates OS-specific commands but does NOT execute them
- ⚠️ **Network Blocking:** Commands are logged, not enforced
- ⚠️ **USB Control:** Not implemented (requires endpoint agent)

### For Production Deployment

To enable actual network enforcement:
1. Deploy endpoint agents on user workstations
2. Configure agent-to-server communication
3. Enable firewall command execution in config
4. Test thoroughly in isolated environment first

---

## Best Practices

### For Security Administrators

1. **Daily Dashboard Review**
   - Check dashboard every morning
   - Review overnight alerts
   - Identify trends in risk scores

2. **Weekly Report Generation**
   - Generate system reports weekly
   - Share with management
   - Track improvement metrics

3. **Regular Model Retraining**
   - Retrain ML models monthly
   - Review model accuracy
   - Update with new attack patterns

4. **Alert Response Time**
   - Acknowledge CRITICAL alerts within 1 hour
   - Resolve HIGH alerts within 24 hours
   - Weekly review of MEDIUM/LOW alerts

5. **User Communication**
   - Inform users about monitoring
   - Explain legitimate vs suspicious behavior
   - Provide feedback on false positives

### For Analysts

1. **Activity Monitoring**
   - Review assigned users daily
   - Flag unusual patterns
   - Document legitimate exceptions

2. **Alert Investigation**
   - Investigate before resolving
   - Contact users for verification
   - Document findings thoroughly

3. **Baseline Understanding**
   - Learn normal user behavior
   - Recognize department-specific patterns
   - Update contextual modifiers

---

## FAQ

### General Questions

**Q: What is IGNISYL?**
A: IGNISYL is an AI-powered insider threat detection system that monitors employee activities and automatically responds to security threats.

**Q: How does the ML detection work?**
A: The system uses a 3-model ensemble (Isolation Forest, Autoencoder, XGBoost) to analyze user behavior and assign risk scores.

**Q: Will employees know they're being monitored?**
A: Yes, transparency is recommended. Inform employees about monitoring for security purposes.

**Q: What happens when a threat is detected?**
A: Depending on risk level, the system responds:
- ALLOW (0-30): Log only, normal operations
- MONITOR (31-50): Enhanced logging, analyst awareness
- RESTRICT (51-75): Analyst decision required
- BLOCK (76-100): Auto-block, incident response

**Note:** In current simulation mode, firewall commands are generated but not executed.

### Technical Questions

**Q: How often is data analyzed?**
A: Real-time. Every activity is analyzed immediately using ML models.

**Q: Can I customize risk thresholds?**
A: Yes (Admin only). Go to Settings → Risk Scoring to adjust thresholds.

**Q: How long is data retained?**
A: Default: 90 days for logs, indefinite for activities. Configurable in Settings.

**Q: Can the system detect USB data exfiltration?**
A: The current implementation detects USB-related activities in activity logs, but real-time USB device control requires endpoint agent deployment (future feature).

**Q: What is a honeypot file?**
A: A decoy file that shouldn't be accessed. Any access triggers CRITICAL alert.

### Troubleshooting

**Q: Dashboard not updating in real-time?**
A: Check WebSocket connection. Refresh browser and ensure backend is running.

**Q: Reports not generating?**
A: Verify ReportLab is installed and `data/reports/` directory exists with write permissions.

**Q: User can't login?**
A: Verify credentials. Check if account is active. Admin can reset password in User Management.

**Q: Why aren't firewall actions being enforced?**
A: The system runs in simulation mode by default. Firewall commands are generated and logged but not executed. This is intentional for academic demonstration safety.

---

## Support & Contact

### Technical Support
- **Email:** support@ignisyl.demo
- **Phone:** +1-XXX-XXX-XXXX
- **Hours:** Monday-Friday, 9 AM - 5 PM

### Documentation
- **API Documentation:** http://localhost:8000/docs
- **Architecture Guide:** `docs/Architecture.md`
- **Installation Guide:** `docs/Installation_Guide.md`

### Report Issues
- **GitHub Issues:** https://github.com/SruthiGS-Gito/Ignisyl/issues
- **Email:** bugs@ignisyl.demo

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + /` | Open search |
| `Ctrl + D` | Go to dashboard |
| `Ctrl + U` | Go to users |
| `Ctrl + A` | Go to activities |
| `Ctrl + R` | Go to reports |
| `Esc` | Close modal |

### Risk Score Interpretation

| Score | Level | Meaning | Typical Action |
|-------|-------|---------|----------------|
| 0-30 | LOW | Normal behavior | ALLOW |
| 31-50 | MEDIUM | Slightly suspicious | MONITOR |
| 51-75 | HIGH | Concerning behavior | RESTRICT (Analyst Decision) |
| 76-100 | CRITICAL | Immediate threat | BLOCK (Auto)

### Activity Type Definitions

| Type | Description | Example |
|------|-------------|---------|
| file_access | File operations | Opening confidential_salary_data.xlsx |
| network_access | Network connections | Large external data transfer |
| login | Authentication | Failed login attempts |
| data_transfer | Data movement | Moving 5GB to USB drive |
| privilege_escalation | Permission changes | Requesting admin rights |
| usb_device | USB usage | Connecting external drive |
| honeypot_access | Decoy file access | Opening admin_passwords.txt |

---

**Last Updated:** January 2026
**Version:** 2.0
**Document:** User Manual
**Note:** This documentation reflects the current simulation mode implementation.
<<<END User_Manual.md>>>



