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
9. [Report Generation](#report-generation)
10. [System Settings](#system-settings)
11. [Network Monitor (Employee Laptops)](#network-monitor-employee-laptops)
12. [Best Practices](#best-practices)
13. [FAQ](#faq)

---

## Introduction

**IGNISYL** is an AI-powered insider threat detection and adaptive firewall system designed to protect organizations from internal security threats. This manual will guide you through using the system effectively.

### Key Features
- ✅ Real-time threat detection using ML
- ✅ Automated firewall responses
- ✅ Professional PDF report generation
- ✅ Live activity monitoring dashboard
- ✅ Role-based access control
- ✅ Network activity tracking on employee devices

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
- ✅ Override ANY firewall action (all 5 levels)
- ✅ Manage ML models
- ✅ Remote shutdown capability

### 2. Security Analyst
**Permissions:**
- ✅ View dashboard and all activities
- ✅ Monitor real-time threats
- ✅ **REMOTE THREAT CONTROL:**
  - ✅ Make decisions on RESTRICT level threats (50-69 risk)
  - ✅ Apply custom firewall restrictions
  - ✅ Contact users directly
  - ✅ Escalate to manager/admin
  - ✅ Override auto-restrictions with justification
- ✅ Generate user-specific reports
- ✅ Acknowledge and resolve alerts
- ❌ Cannot create/delete users
- ❌ Cannot modify global system settings
- ⚠️ Limited to Level 3-4 actions (cannot force shutdown)

## Analyst Remote Control Capabilities

### Real-Time Threat Response Dashboard

When a HIGH-risk threat is detected (risk score 50-69), the system **does not automatically block**. Instead, it sends the threat to the **Analyst Decision Queue**.

### Analyst Decision Workflow

1. **Threat Notification**
   - Alert appears in "Pending Decisions" section
   - Desktop notification (if enabled)
   - Email alert for URGENT threats

2. **Threat Analysis**
   - View complete activity context
   - See user's recent behavior history
   - Review ML model reasoning
   - Check if user is on-site or remote

3. **Available Actions**

#### Option 1: ALLOW (False Positive)
```
Use Case: Legitimate unusual activity
Example: CFO accessing payroll data at night for audit
Action: Clear alert, add to user baseline
```

#### Option 2: RESTRICT (Limit Access)
```
Use Case: Suspicious but not critical
Example: Employee accessing confidential files outside normal hours
Custom Restrictions:
  ☐ Block external internet only
  ☐ Block file transfers (FTP, SMB, SSH)
  ☐ Rate limit to 1 Mbps
  ☐ Disable USB devices
  ☐ Force logout after 10 minutes
  ☐ Send warning notification to user
Duration: 30 min / 1 hr / 4 hrs / Until review
```

#### Option 3: ISOLATE (Network Quarantine)
```
Use Case: High-confidence threat
Example: Large data exfiltration attempt
Restrictions:
  ✓ Block all external network
  ✓ Allow internal corporate network only
  ✓ Disconnect VPN
  ✓ Disable USB ports
  ✓ Log all local file operations
Duration: Until analyst manually releases
```

#### Option 4: ESCALATE
```
Use Case: Need admin/management decision
Action: Forward to admin with notes
Notification: Immediate alert to admin
```

#### Option 5: CONTACT USER
```
Use Case: Need user explanation
Action: Send message to user's device
Message: "We've detected unusual activity on your account.
         Please call Security at ext. 1234 immediately."
```

### Custom Restriction Examples

**Scenario 1: Finance employee accessing HR files**
```
Risk Score: 62 (HIGH)
Analyst Decision: RESTRICT
Custom Actions:
  ✓ Block external internet
  ✓ Send warning notification
  ✗ Allow internal network (for legitimate work)
Duration: 30 minutes
Reason: "Verify legitimate business need with manager"
```

**Scenario 2: Developer with sudden large data transfer**
```
Risk Score: 71 (CRITICAL - auto-isolated)
Analyst Review: ISOLATE → ALLOW
Custom Actions:
  ✓ Contact user first
  ✓ User confirmed: "Uploading product release to cloud"
  ✓ Release isolation
  ✓ Add to baseline: "Weekly release uploads"
Reason: "Legitimate release process, updated user profile"
```

**Scenario 3: Honeypot access detected**
```
Risk Score: 95 (CRITICAL - auto-blocked)
Analyst Review: Confirm block
Actions:
  ✓ Keep blocked
  ✓ Contact user's manager
  ✓ Initiate incident investigation
  ✓ Preserve forensic evidence
Reason: "Confirmed insider threat - investigating"
```

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
- 🟢 **GREEN** - LOW risk (0-29)
- 🟡 **YELLOW** - MEDIUM risk (30-49)
- 🟠 **ORANGE** - HIGH risk (50-69)
- 🔴 **RED** - CRITICAL risk (70-100)

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
- **LOW** - Risk Score < 30
- **MEDIUM** - Risk Score 30-49
- **HIGH** - Risk Score 50-69
- **CRITICAL** - Risk Score ≥ 70

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
## Analyst Remote Threat Control

### Overview

When a HIGH-risk threat is detected (risk score 50-69), the system **does not automatically block**. Instead, it sends the threat to the **Analyst Decision Queue** for human review.

This graduated approach prevents false positives while ensuring real threats are addressed.

### Accessing Pending Decisions

1. Navigate to **Dashboard** → **Pending Decisions**
2. Or click the **notification badge** when new threats appear
3. You'll see threats sorted by risk score (highest first)

### Threat Analysis Screen

Each pending threat shows:
- **User Information:** Name, department, role
- **Activity Details:** What they did, when, where
- **Risk Breakdown:**
  - ML model scores (Isolation Forest, Autoencoder, XGBoost)
  - Triggered risk factors (e.g., "outside_business_hours", "large_file_transfer")
  - Contextual modifiers applied
- **Recommended Action:** System suggestion
- **Recent History:** User's last 10 activities

### Available Actions

#### Option 1: ALLOW (False Positive)
**Use When:** Activity is legitimate despite high risk score

**Example Scenario:**
- CFO accessing payroll data at 11 PM for board meeting next morning
- Developer downloading large codebase for urgent hotfix

**Steps:**
1. Click **ALLOW** button
2. Enter reason: "Legitimate business need - board meeting preparation"
3. Optionally: Add to user's baseline behavior
4. Click **Confirm**

**Result:** Alert cleared, no restrictions applied

---

#### Option 2: RESTRICT (Limit Access)
**Use When:** Suspicious activity that needs investigation

**Example Scenario:**
- Employee accessing HR files outside their department
- Large data transfer to personal cloud storage

**Custom Restrictions:**
```
☐ Block external internet only
☐ Block file transfers (FTP, SMB, SSH)
☐ Rate limit to 1 Mbps
☐ Disable USB devices
☐ Force logout after 10 minutes
☐ Send warning notification to user
```

**Duration Options:**
- 30 minutes
- 1 hour (default)
- 4 hours
- 8 hours
- Until analyst review

**Steps:**
1. Click **RESTRICT** button
2. Select custom restrictions (checkboxes)
3. Choose duration
4. Enter reason: "Accessing confidential files outside normal hours - verifying with manager"
5. Optional: Send notification to user
6. Click **Apply Restrictions**

**Result:** User can access internal resources but limited external access

---

#### Option 3: ISOLATE (Network Quarantine)
**Use When:** High confidence of malicious activity

**Example Scenario:**
- Multiple honeypot file accesses
- Attempting privilege escalation
- Large data exfiltration in progress

**Restrictions Applied:**
```
✓ Block all external network
✓ Allow internal corporate network only
✓ Disconnect VPN
✓ Disable USB ports
✓ Log all local file operations
✓ Require admin unlock
```

**Steps:**
1. Click **ISOLATE** button
2. Confirm action (this is severe)
3. Enter detailed reason
4. Click **Quarantine User**

**Result:** User completely isolated, investigation begins immediately

---

#### Option 4: CONTACT USER
**Use When:** Need user explanation before taking action

**Steps:**
1. Click **Contact User** button
2. Select method:
   - Desktop notification (instant)
   - Email (within 5 min)
   - SMS (if configured)
3. Enter message:
```
   We've detected unusual activity on your account.
   Please call Security at ext. 1234 immediately.
```
4. Click **Send Message**

**Result:** User receives notification, analyst waits for response

---

#### Option 5: ESCALATE
**Use When:** Decision requires higher authority

**Escalation Targets:**
- **Admin:** For policy decisions
- **Manager:** For department-specific context
- **Incident Team:** For serious threats

**Steps:**
1. Click **Escalate** button
2. Select escalation target
3. Enter notes:
```
   User accessing multiple honeypot files.
   Need executive decision on whether to involve HR.
   Possible insider threat investigation required.
```
4. Click **Escalate**

**Result:** Notification sent to target, they take over decision

---

### Real-World Examples

#### Example 1: Finance Employee Accessing HR Files

**Alert:**
```
User: jane_smith
Risk Score: 62 (HIGH)
Activity: Accessed employee_salaries.xlsx
Time: 2:47 AM
Location: Home IP
```

**Analyst Analysis:**
- Finance employee, but HR files are outside scope
- Very unusual time (2:47 AM)
- Working from home (not corporate network)
- No recent approval for HR data access

**Decision: RESTRICT**
```
Custom Actions:
  ✓ Block external internet
  ✓ Send warning notification
  ✗ Allow internal network (for legitimate work)
Duration: 1 hour
Reason: "Verifying legitimate business need with HR director"
```

**Follow-up:**
- Contacted user via notification
- User responded: "Working on merger analysis, need salary data"
- Contacted HR director: Confirmed approval exists
- Released restriction after 30 minutes
- Updated user profile: "Authorized for HR data access"

---

#### Example 2: Developer with Large Data Transfer

**Alert:**
```
User: bob_developer
Risk Score: 71 (CRITICAL - auto-isolated)
Activity: Uploading 5GB to external cloud
Time: 6:15 PM
Location: Office
```

**Analyst Analysis:**
- System auto-isolated (risk > 70)
- Developer transferring large amount of data
- To personal Dropbox account
- No business justification visible

**Decision: Review Isolation → ALLOW**
```
Actions Taken:
  1. Contacted user immediately
  2. User explained: "Uploading product release to cloud for distribution"
  3. Verified: Weekly release schedule, this is normal
  4. Released isolation
  5. Updated baseline: "Weekly 5GB uploads on Friday evenings"
  
Reason: "Legitimate release process, updated user profile"
```

**Lesson:** Auto-isolation for CRITICAL threats, but analyst can override with justification

---

#### Example 3: Honeypot Access (Confirmed Threat)

**Alert:**
```
User: john_contractor
Risk Score: 95 (CRITICAL - auto-blocked)
Activity: Accessed admin_passwords.txt (honeypot)
Time: 11:32 PM
Location: Unknown IP
```

**Analyst Analysis:**
- Honeypot file (decoy trap)
- Any access is malicious
- Unknown IP (not corporate network)
- Late night activity
- Contractor, not full employee

**Decision: Keep BLOCK + Escalate to Incident Team**
```
Actions Taken:
  1. Keep full network block (already applied)
  2. Contacted user's manager
  3. Escalated to Incident Response Team
  4. Started forensic investigation
  5. Notified HR for contract review
  
Reason: "Confirmed insider threat - honeypot access indicates malicious intent"
```

**Result:** Full investigation launched, contractor's access revoked

---

### Best Practices for Analysts

#### 1. Always Investigate Context
- Check user's normal behavior patterns
- Review recent activities (last 24 hours)
- Consider business context (month-end, audits, releases)
- Contact user's manager if unsure

#### 2. Document Everything
- Always provide detailed reasons
- Note any contact made with user/manager
- Document follow-up actions
- Update user baselines when patterns change

#### 3. Response Time Targets
- **CRITICAL (90-100):** Already auto-handled, review within 30 min
- **HIGH (70-89):** Review within 1 hour
- **MEDIUM-HIGH (50-69):** Review within 4 hours

#### 4. Communication
- Use **Contact User** for quick clarification
- Use **Escalate** when you need more authority
- Always notify users when applying restrictions
- Follow up after restrictions expire

#### 5. False Positive Handling
- If ALLOW, update user's baseline behavior
- Document why it was flagged (for model improvement)
- Add notes for future analysts

---

### Audit Trail

All analyst actions are logged for compliance:
- What action was taken
- Who took it
- When it was taken
- Why (justification required)
- Result of action

**View Your Actions:**
1. Navigate to **Profile** → **My Actions**
2. See complete history of your decisions
3. Export for compliance reporting
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

## System Settings

*(Admin Only)*

### ML Model Configuration

1. Navigate to **Settings** → **ML Models**
2. Configure:
   - **Enable ML Training** (On/Off)
   - **Auto-Retraining Threshold** (accuracy < 85%)
   - **Model Persistence Path**

### Risk Scoring Configuration

1. Navigate to **Settings** → **Risk Scoring**
2. Adjust thresholds:
   - **LOW Risk:** 0-29
   - **MEDIUM Risk:** 30-49
   - **HIGH Risk:** 50-69
   - **CRITICAL Risk:** 70-100

### Firewall Configuration

1. Navigate to **Settings** → **Firewall**
2. Configure:
   - **Auto-Block Threshold** (default: 70)
   - **Default Block Duration** (default: 60 minutes)
   - **Restriction Types:**
     - Block External (no internet)
     - Rate Limit (1 Mbps)
     - Block File Transfer (ports 21, 22, 445)

### Logging Configuration

1. Navigate to **Settings** → **Logging**
2. Set:
   - **Log Level** (DEBUG, INFO, WARNING, ERROR)
   - **Log to File** (On/Off)
   - **Log Retention** (default: 90 days)

---

## Network Monitor (Employee Laptops)

### Deployment

The **Network Monitor** runs on each employee's laptop to track network activity.

#### Step 1: Install on Employee Laptop
```bash
# Copy network_monitor.py to employee laptop
# Navigate to directory
cd C:\Ignisyl

# Install dependencies
pip install psutil requests
```

#### Step 2: Configure User

Create `user_config.json`:
```json
{
  "user_id": "john_doe",
  "username": "john_doe",
  "full_name": "John Doe",
  "department": "Finance",
  "role": "analyst",
  "api_url": "http://central-server:8000/api/v1"
}
```

#### Step 3: Run Monitor
```bash
# Start network monitor
python network_monitor.py

# You should see:
# Starting network monitoring for user: john_doe
# Monitoring every 30 seconds...
# Press Ctrl+C to stop
```

#### Step 4: Set as Startup Service

**Windows:**

1. Create batch file `start_monitor.bat`:
```batch
@echo off
cd C:\Ignisyl
python network_monitor.py
```

2. Press `Win + R`, type `shell:startup`
3. Copy `start_monitor.bat` to Startup folder

### Monitoring Behavior

The network monitor:
- ✅ Checks network usage every 30 seconds
- ✅ Detects large transfers (> 50 MB in 30 seconds)
- ✅ Monitors high transfer rates (> 50 MB/s)
- ✅ Sends data to central API
- ✅ Receives firewall commands

### Employee Notifications

When suspicious activity is detected:
1. Network monitor sends data to server
2. Server analyzes with ML models
3. If HIGH/CRITICAL risk:
   - Alert appears on security dashboard
   - Firewall restriction applied
   - Employee receives notification (if configured)

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
A: Depending on risk level, the system can:
- ALLOW (log only)
- MONITOR (flag for review)
- RESTRICT (limit network/file access)
- BLOCK (complete network isolation)

### Technical Questions

**Q: How often is data analyzed?**
A: Real-time. Every activity is analyzed immediately using ML models.

**Q: Can I customize risk thresholds?**
A: Yes (Admin only). Go to Settings → Risk Scoring to adjust thresholds.

**Q: How long is data retained?**
A: Default: 90 days for logs, indefinite for activities. Configurable in Settings.

**Q: Can the system detect USB data exfiltration?**
A: Yes. The comprehensive monitor tracks USB device usage and flags suspicious transfers.

**Q: What is a honeypot file?**
A: A decoy file that shouldn't be accessed. Any access triggers CRITICAL alert.

### Troubleshooting

**Q: Dashboard not updating in real-time?**
A: Check WebSocket connection. Refresh browser and ensure backend is running.

**Q: Reports not generating?**
A: Verify ReportLab is installed and `data/reports/` directory exists with write permissions.

**Q: User can't login?**
A: Verify credentials. Check if account is active. Admin can reset password in User Management.

**Q: Network monitor not sending data?**
A: Check `user_config.json` has correct API URL and user is not blocked by firewall.

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
| 0-29 | LOW | Normal behavior | ALLOW |
| 30-49 | MEDIUM | Slightly suspicious | MONITOR |
| 50-69 | HIGH | Concerning behavior | RESTRICT |
| 70-100 | CRITICAL | Immediate threat | BLOCK |

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

**Last Updated:** January 2025  
**Version:** 1.0  
**Document:** User Manual
<<<END User_Manual.md>>>



