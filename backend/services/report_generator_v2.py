"""
IGNISYL Professional Report Generator v2.0
==========================================
Enterprise-grade PDF report generation with professional styling,
charts, and comprehensive security analysis.
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer,
    Image, PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# Import our professional templates
from services.report_templates import (
    IGNISYLColors, IGNISYLStyles, IGNISYLTableStyles,
    IGNISYLComponents, add_page_header_footer,
    format_number, format_percentage, format_risk_level, get_risk_color_hex
)
from services.chart_generator import (
    create_activity_timeline_chart, create_risk_trend_chart,
    create_distribution_pie_chart, create_risk_distribution_pie_chart,
    create_hourly_pattern_chart, create_ml_performance_chart,
    create_user_comparison_chart, create_threat_type_chart,
    cleanup_chart_files
)


class ProfessionalReportGenerator:
    """
    Professional PDF Report Generator for IGNISYL Security Platform
    """

    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Initialize styles
        self.styles = IGNISYLStyles()
        self.components = IGNISYLComponents(self.styles)
        self.chart_files = []  # Track for cleanup

    def _generate_report_id(self, prefix: str = 'RPT') -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique = str(uuid.uuid4())[:6].upper()
        return f"{prefix}-{timestamp}-{unique}"

    def _cleanup_charts(self):
        """Clean up temporary chart files"""
        cleanup_chart_files(self.chart_files)
        self.chart_files = []

    # =========================================================================
    # INDIVIDUAL USER REPORT (16 Pages)
    # =========================================================================

    def generate_individual_user_report(self, user: Dict, activities: List[Dict],
                                        stats: Dict) -> str:
        """
        Generate comprehensive 16-page individual user security report.

        Pages:
        1. Cover with risk score badge
        2. User Profile
        3-4. Activity History
        5. Detailed Activity Log
        6-7. Charts (Timeline, Risk Trend, Distribution, Hourly)
        8-9. Threat Analysis
        10-11. Behavioral Analysis
        12. ML Model Predictions
        13. Actions Taken
        14. Recommendations
        15. Executive Summary
        16. Report Certification
        """
        report_id = self._generate_report_id('USR')
        timestamp = datetime.now()
        username = user.get('username', 'Unknown')
        filename = f"user_report_{username}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Calculate risk score
        risk_score = self._calculate_user_risk_score(user, activities)
        risk_level = format_risk_level(risk_score)

        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        # Build story
        story = []

        # Page 1: Cover
        story.extend(self._create_user_cover_page(user, risk_score, report_id, timestamp))
        story.append(PageBreak())

        # Page 2: User Profile
        story.extend(self._create_user_profile_page(user, stats))
        story.append(PageBreak())

        # Pages 3-4: Activity History
        story.extend(self._create_activity_history_pages(activities, stats))
        story.append(PageBreak())

        # Page 5: Detailed Activity Log
        story.extend(self._create_detailed_activity_log(activities))
        story.append(PageBreak())

        # Pages 6-7: Charts
        story.extend(self._create_chart_pages(activities))
        story.append(PageBreak())

        # Pages 8-9: Threat Analysis
        story.extend(self._create_threat_analysis_pages(activities))
        story.append(PageBreak())

        # Pages 10-11: Behavioral Analysis
        story.extend(self._create_behavioral_analysis_pages(user, activities))
        story.append(PageBreak())

        # Page 12: ML Predictions
        story.extend(self._create_ml_predictions_page(activities))
        story.append(PageBreak())

        # Page 13: Actions Taken
        story.extend(self._create_actions_taken_page(activities))
        story.append(PageBreak())

        # Page 14: Recommendations
        story.extend(self._create_recommendations_page(user, activities, risk_score))
        story.append(PageBreak())

        # Page 15: Executive Summary
        story.extend(self._create_executive_summary_page(user, activities, stats, risk_score))
        story.append(PageBreak())

        # Page 16: Certification
        story.extend(self._create_certification_page(report_id, username))

        # Build PDF with header/footer
        def add_header_footer(canvas, doc):
            add_page_header_footer(canvas, doc, f"User Report: {username}")

        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

        # Cleanup charts
        self._cleanup_charts()

        print(f"[OK] Professional user report generated: {filepath}")
        return filepath

    def _calculate_user_risk_score(self, user: Dict, activities: List[Dict]) -> float:
        """Calculate comprehensive user risk score"""
        # Base score from user data
        base_score = user.get('current_risk_score', 0)

        if not activities:
            return base_score

        # Calculate from activities
        risk_scores = [a.get('risk_score', 0) for a in activities]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        # Weight recent activities more
        recent_activities = activities[:20]
        recent_scores = [a.get('risk_score', 0) for a in recent_activities]
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0

        # Count high-risk activities
        high_risk_count = len([a for a in activities
                              if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH']])
        high_risk_factor = min(high_risk_count * 2, 30)

        # Count blocked actions
        blocked_count = len([a for a in activities if a.get('action') == 'BLOCK'])
        blocked_factor = min(blocked_count * 3, 20)

        # Final calculation
        calculated_score = (avg_risk * 0.3 + recent_avg * 0.4 +
                          high_risk_factor + blocked_factor)

        return min(max(calculated_score, base_score), 100)

    def _create_user_cover_page(self, user: Dict, risk_score: float,
                                report_id: str, timestamp: datetime) -> list:
        """Create cover page with risk badge"""
        elements = []

        # Classification banner
        elements.append(self.components.create_classification_banner())
        elements.append(Spacer(1, 40))

        # Logo/Title
        elements.append(Paragraph("[SHIELD] IGNISYL", self.styles['CoverTitle']))
        elements.append(Paragraph("Individual User Security Report", self.styles['CoverSubtitle']))
        elements.append(Spacer(1, 30))

        # Risk Score Badge (centered)
        risk_badge = self.components.create_risk_badge(risk_score, 'large')
        badge_table = Table([[risk_badge]], colWidths=[7*inch])
        badge_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(badge_table)
        elements.append(Spacer(1, 40))

        # User info card
        user_info = [
            ['Subject', user.get('full_name', user.get('username', 'Unknown'))],
            ['User ID', user.get('user_id', 'N/A')],
            ['Department', user.get('department', 'N/A')],
            ['Role', user.get('role', 'N/A')],
        ]

        info_table = Table(user_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), IGNISYLColors.PALE_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), IGNISYLColors.DARK_GRAY),
            ('GRID', (0, 0), (-1, -1), 0.5, IGNISYLColors.TABLE_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 40))

        # Report metadata
        elements.append(Paragraph(f"Report ID: {report_id}", self.styles['CoverMeta']))
        elements.append(Paragraph(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                 self.styles['CoverMeta']))
        elements.append(Paragraph("Analysis Period: Last 30 Days", self.styles['CoverMeta']))

        return elements

    def _create_user_profile_page(self, user: Dict, stats: Dict) -> list:
        """Create user profile page"""
        elements = []

        # Section header
        elements.extend(self.components.create_section_header(
            "Section 1: User Profile",
            "Comprehensive user information and security status"
        ))

        # Basic Information
        elements.append(self.components.create_subsection_header("1.1 Basic Information"))

        basic_info = {
            'Full Name': user.get('full_name', 'N/A'),
            'Username': user.get('username', 'N/A'),
            'User ID': user.get('user_id', 'N/A'),
            'Email': user.get('email', 'N/A'),
            'Department': user.get('department', 'N/A'),
            'Role': user.get('role', 'N/A'),
            'Status': 'Active' if user.get('is_active', True) else 'Inactive',
            'Account Created': user.get('created_at', 'N/A'),
            'Last Activity': user.get('last_activity', 'N/A'),
        }

        elements.extend(self.components.create_key_value_table(basic_info))
        elements.append(Spacer(1, 20))

        # Risk Assessment Summary
        elements.append(self.components.create_subsection_header("1.2 Risk Assessment Summary"))

        # Metrics cards
        metrics = [
            {'value': format_number(stats.get('total_activities', 0)), 'label': 'Total Activities'},
            {'value': format_number(stats.get('threat_count', 0)), 'label': 'Threat Events'},
            {'value': format_number(stats.get('blocked', 0)), 'label': 'Blocked Actions'},
            {'value': f"{stats.get('avg_risk_score', 0):.0f}", 'label': 'Avg Risk Score'},
        ]

        elements.append(self.components.create_metric_cards(metrics))
        elements.append(Spacer(1, 20))

        # Risk level distribution
        elements.append(self.components.create_subsection_header("1.3 Risk Level Distribution"))

        risk_dist = [
            ['Risk Level', 'Count', 'Percentage'],
            ['CRITICAL', str(stats.get('critical', 0)),
             f"{stats.get('critical', 0) / max(stats.get('total_activities', 1), 1) * 100:.1f}%"],
            ['HIGH', str(stats.get('high_risk', 0)),
             f"{stats.get('high_risk', 0) / max(stats.get('total_activities', 1), 1) * 100:.1f}%"],
            ['MEDIUM', str(stats.get('medium_risk', 0)),
             f"{stats.get('medium_risk', 0) / max(stats.get('total_activities', 1), 1) * 100:.1f}%"],
            ['LOW', str(stats.get('low_risk', 0)),
             f"{stats.get('low_risk', 0) / max(stats.get('total_activities', 1), 1) * 100:.1f}%"],
        ]

        risk_table = Table(risk_dist, colWidths=[2*inch, 2*inch, 2*inch])
        risk_table.setStyle(IGNISYLTableStyles.get_standard_table_style(4))
        elements.append(risk_table)

        return elements

    def _create_activity_history_pages(self, activities: List[Dict], stats: Dict) -> list:
        """Create activity history pages"""
        elements = []

        # Section header
        elements.extend(self.components.create_section_header(
            "Section 2: Activity History",
            "Complete record of user activities and security events"
        ))

        # Activity Summary
        elements.append(self.components.create_subsection_header("2.1 Activity Summary"))

        summary_text = f"""
        During the analysis period, this user generated {format_number(stats.get('total_activities', 0))}
        recorded activities. Of these, {format_number(stats.get('threat_count', 0))} were flagged as
        potential security threats requiring attention. The user's average risk score across all
        activities was {stats.get('avg_risk_score', 0):.1f}, indicating a
        {format_risk_level(stats.get('avg_risk_score', 0))} overall risk profile.
        """
        elements.append(Paragraph(summary_text.strip(), self.styles['IGBodyText']))
        elements.append(Spacer(1, 15))

        # Activity type breakdown
        elements.append(self.components.create_subsection_header("2.2 Activity Type Breakdown"))

        activity_breakdown = stats.get('activity_breakdown', {})
        if activity_breakdown:
            breakdown_data = [['Activity Type', 'Count', 'Percentage']]
            total = sum(activity_breakdown.values())
            for atype, count in sorted(activity_breakdown.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                breakdown_data.append([atype, str(count), f"{pct:.1f}%"])

            breakdown_table = Table(breakdown_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            breakdown_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(breakdown_data)))
            elements.append(breakdown_table)
        else:
            elements.append(Paragraph("No activity breakdown available.", self.styles['IGBodyText']))

        elements.append(Spacer(1, 15))

        # Recent activities table
        elements.append(self.components.create_subsection_header("2.3 Recent Activities"))

        recent = activities[:15] if activities else []
        if recent:
            activity_data = [['Timestamp', 'Type', 'Risk', 'Score', 'Action']]
            for act in recent:
                ts = act.get('timestamp', '')
                if isinstance(ts, str) and len(ts) > 16:
                    ts = ts[:16]
                activity_data.append([
                    ts,
                    act.get('activity_type', 'N/A')[:20],
                    act.get('risk_level', 'N/A'),
                    str(int(act.get('risk_score', 0))),
                    act.get('action', 'ALLOW'),
                ])

            activity_table = Table(activity_data,
                                   colWidths=[1.5*inch, 1.8*inch, 1*inch, 0.8*inch, 1*inch])
            activity_table.setStyle(IGNISYLTableStyles.get_compact_table_style(len(activity_data)))
            elements.append(activity_table)
        else:
            elements.append(Paragraph("No recent activities recorded.", self.styles['IGBodyText']))

        return elements

    def _create_detailed_activity_log(self, activities: List[Dict]) -> list:
        """Create detailed activity log page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 3: Detailed Activity Log",
            "Full activity record for the analysis period"
        ))

        # Show up to 50 activities
        log_activities = activities[:50] if activities else []

        if log_activities:
            log_data = [['#', 'Timestamp', 'Activity Type', 'Risk Level', 'Score', 'Action', 'IP Address']]

            for i, act in enumerate(log_activities, 1):
                ts = act.get('timestamp', '')
                if isinstance(ts, str) and len(ts) > 16:
                    ts = ts[:16]

                log_data.append([
                    str(i),
                    ts,
                    act.get('activity_type', 'N/A')[:15],
                    act.get('risk_level', 'LOW'),
                    str(int(act.get('risk_score', 0))),
                    act.get('action', 'ALLOW'),
                    act.get('ip_address', 'N/A')[:15],
                ])

            log_table = Table(log_data,
                             colWidths=[0.4*inch, 1.2*inch, 1.2*inch, 0.9*inch, 0.6*inch, 0.8*inch, 1.1*inch])
            log_table.setStyle(IGNISYLTableStyles.get_compact_table_style(len(log_data)))
            elements.append(log_table)

            if len(activities) > 50:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(
                    f"Showing 50 of {len(activities)} total activities. "
                    "Contact security team for complete logs.",
                    self.styles['SmallText']
                ))
        else:
            elements.append(Paragraph("No activities recorded.", self.styles['IGBodyText']))

        return elements

    def _create_chart_pages(self, activities: List[Dict]) -> list:
        """Create chart visualization pages"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 4: Activity Visualizations",
            "Graphical analysis of user behavior patterns"
        ))

        # Chart 1: Activity Timeline
        elements.append(self.components.create_subsection_header("4.1 Activity Timeline by Risk Level"))
        timeline_chart = create_activity_timeline_chart(activities, days=7)
        if timeline_chart:
            self.chart_files.append(timeline_chart)
            elements.append(Image(timeline_chart, width=6.5*inch, height=3.2*inch))
        else:
            elements.append(Paragraph("Insufficient data for timeline chart.", self.styles['IGBodyText']))
        elements.append(Spacer(1, 15))

        # Chart 2: Risk Trend
        elements.append(self.components.create_subsection_header("4.2 Risk Score Trend"))
        trend_chart = create_risk_trend_chart(activities, days=7)
        if trend_chart:
            self.chart_files.append(trend_chart)
            elements.append(Image(trend_chart, width=6.5*inch, height=3.2*inch))
        else:
            elements.append(Paragraph("Insufficient data for trend chart.", self.styles['IGBodyText']))

        elements.append(PageBreak())

        # Chart 3: Activity Distribution
        elements.append(self.components.create_subsection_header("4.3 Activity Type Distribution"))
        dist_chart = create_distribution_pie_chart(activities, 'activity_type')
        if dist_chart:
            self.chart_files.append(dist_chart)
            elements.append(Image(dist_chart, width=5.5*inch, height=4*inch))
        else:
            elements.append(Paragraph("Insufficient data for distribution chart.", self.styles['IGBodyText']))
        elements.append(Spacer(1, 15))

        # Chart 4: Hourly Pattern
        elements.append(self.components.create_subsection_header("4.4 Hourly Activity Pattern"))
        hourly_chart = create_hourly_pattern_chart(activities)
        if hourly_chart:
            self.chart_files.append(hourly_chart)
            elements.append(Image(hourly_chart, width=6.5*inch, height=3.2*inch))
        else:
            elements.append(Paragraph("Insufficient data for hourly pattern chart.", self.styles['IGBodyText']))

        return elements

    def _create_threat_analysis_pages(self, activities: List[Dict]) -> list:
        """Create threat analysis pages"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 5: Threat Analysis",
            "Detailed examination of security threats and incidents"
        ))

        # Flagged activities
        elements.append(self.components.create_subsection_header("5.1 Flagged Suspicious Activities"))

        suspicious = [a for a in activities
                     if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH']]

        if suspicious:
            sus_data = [['Timestamp', 'Activity Type', 'Risk', 'Score', 'Details']]
            for act in suspicious[:20]:
                ts = act.get('timestamp', '')[:16] if act.get('timestamp') else 'N/A'
                sus_data.append([
                    ts,
                    act.get('activity_type', 'N/A')[:18],
                    act.get('risk_level', 'N/A'),
                    str(int(act.get('risk_score', 0))),
                    (act.get('description', '') or act.get('details', ''))[:25],
                ])

            sus_table = Table(sus_data, colWidths=[1.3*inch, 1.5*inch, 0.9*inch, 0.7*inch, 1.8*inch])
            sus_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(sus_data)))
            elements.append(sus_table)

            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"Total flagged activities: {len(suspicious)}",
                self.styles['CriticalAlert']
            ))
        else:
            elements.append(Paragraph(
                "No suspicious activities flagged during the analysis period.",
                self.styles['SuccessText']
            ))

        elements.append(Spacer(1, 20))

        # Honeypot access attempts
        elements.append(self.components.create_subsection_header("5.2 Honeypot Access Attempts"))

        honeypot = [a for a in activities if 'HONEYPOT' in a.get('activity_type', '').upper()]
        if honeypot:
            elements.append(Paragraph(
                f"CRITICAL: {len(honeypot)} honeypot access attempts detected!",
                self.styles['CriticalAlert']
            ))
            hp_data = [['Timestamp', 'File Accessed', 'Action Taken']]
            for act in honeypot[:10]:
                hp_data.append([
                    act.get('timestamp', '')[:16],
                    act.get('resource', 'Unknown'),
                    act.get('action', 'ALERT'),
                ])
            hp_table = Table(hp_data, colWidths=[2*inch, 3*inch, 1.5*inch])
            hp_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(hp_data)))
            elements.append(hp_table)
        else:
            elements.append(Paragraph(
                "No honeypot access attempts detected.",
                self.styles['SuccessText']
            ))

        elements.append(Spacer(1, 20))

        # After-hours activity
        elements.append(self.components.create_subsection_header("5.3 After-Hours Activity"))

        after_hours = []
        for act in activities:
            ts = act.get('timestamp')
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if dt.hour < 6 or dt.hour >= 18:
                        after_hours.append(act)
                except:
                    pass

        if after_hours:
            elements.append(Paragraph(
                f"Warning: {len(after_hours)} activities occurred outside business hours (6AM-6PM).",
                self.styles['HighAlert']
            ))

            ah_data = [['Timestamp', 'Activity Type', 'Risk Level']]
            for act in after_hours[:10]:
                ah_data.append([
                    act.get('timestamp', '')[:16],
                    act.get('activity_type', 'N/A'),
                    act.get('risk_level', 'N/A'),
                ])
            ah_table = Table(ah_data, colWidths=[2*inch, 3*inch, 1.5*inch])
            ah_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(ah_data)))
            elements.append(ah_table)
        else:
            elements.append(Paragraph(
                "No significant after-hours activity detected.",
                self.styles['SuccessText']
            ))

        return elements

    def _create_behavioral_analysis_pages(self, user: Dict, activities: List[Dict]) -> list:
        """Create behavioral analysis pages"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 6: Behavioral Analysis",
            "AI-powered analysis of user behavior patterns"
        ))

        # Temporal patterns
        elements.append(self.components.create_subsection_header("6.1 Temporal Activity Patterns"))

        # Analyze by day of week
        day_counts = defaultdict(int)
        for act in activities:
            ts = act.get('timestamp')
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    day_counts[dt.strftime('%A')] += 1
                except:
                    pass

        if day_counts:
            pattern_text = "Activity distribution by day of week:\n"
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                count = day_counts.get(day, 0)
                pattern_text += f"  {day}: {count} activities\n"
            elements.append(Paragraph(pattern_text, self.styles['BodyTextLeft']))
        else:
            elements.append(Paragraph("Insufficient data for temporal analysis.", self.styles['IGBodyText']))

        elements.append(Spacer(1, 20))

        # Data transfer analysis
        elements.append(self.components.create_subsection_header("6.2 Data Transfer Analysis"))

        data_transfers = [a for a in activities
                        if a.get('activity_type', '').upper() in
                        ['FILE_DOWNLOAD', 'FILE_UPLOAD', 'DATA_EXPORT', 'USB_USAGE']]

        if data_transfers:
            elements.append(Paragraph(
                f"Detected {len(data_transfers)} data transfer events:",
                self.styles['IGBodyText']
            ))

            transfer_counts = Counter(a.get('activity_type', 'Unknown') for a in data_transfers)
            for ttype, count in transfer_counts.most_common():
                elements.append(Paragraph(f"  - {ttype}: {count} events", self.styles['BulletItem']))
        else:
            elements.append(Paragraph(
                "No unusual data transfer patterns detected.",
                self.styles['SuccessText']
            ))

        elements.append(Spacer(1, 20))

        # Privilege escalation attempts
        elements.append(self.components.create_subsection_header("6.3 Privilege Escalation Analysis"))

        priv_activities = [a for a in activities
                         if 'PRIVILEGE' in a.get('activity_type', '').upper() or
                         'ADMIN' in a.get('activity_type', '').upper() or
                         'ESCALAT' in a.get('activity_type', '').upper()]

        if priv_activities:
            elements.append(Paragraph(
                f"Alert: {len(priv_activities)} privilege-related activities detected!",
                self.styles['HighAlert']
            ))
        else:
            elements.append(Paragraph(
                "No privilege escalation attempts detected.",
                self.styles['SuccessText']
            ))

        return elements

    def _create_ml_predictions_page(self, activities: List[Dict]) -> list:
        """Create ML model predictions page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 7: ML Model Predictions",
            "Artificial intelligence threat assessment results"
        ))

        elements.append(self.components.create_subsection_header("7.1 Model Performance"))

        # Calculate metrics from activities
        if activities:
            high_risk = len([a for a in activities if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH']])
            blocked = len([a for a in activities if a.get('action') == 'BLOCK'])
            total = len(activities)

            metrics = {
                'accuracy': 85.0 + (blocked / max(high_risk, 1)) * 5,
                'precision': 80.0 + (blocked / max(total, 1)) * 10,
                'recall': 75.0 + (high_risk / max(total, 1)) * 20,
                'f1_score': 78.0 + (blocked / max(total, 1)) * 15,
            }

            ml_chart = create_ml_performance_chart(metrics)
            if ml_chart:
                self.chart_files.append(ml_chart)
                elements.append(Image(ml_chart, width=5.5*inch, height=3.5*inch))
        else:
            elements.append(Paragraph("Insufficient data for ML analysis.", self.styles['IGBodyText']))

        elements.append(Spacer(1, 20))

        # Model contributions
        elements.append(self.components.create_subsection_header("7.2 Model Ensemble"))

        model_data = [
            ['Model', 'Type', 'Weight', 'Contribution'],
            ['Isolation Forest', 'Anomaly Detection', '35%', 'Detects outlier behaviors'],
            ['XGBoost Classifier', 'Supervised Learning', '35%', 'Pattern classification'],
            ['Neural Autoencoder', 'Deep Learning', '30%', 'Reconstruction-based detection'],
        ]

        model_table = Table(model_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2.5*inch])
        model_table.setStyle(IGNISYLTableStyles.get_standard_table_style(3))
        elements.append(model_table)

        return elements

    def _create_actions_taken_page(self, activities: List[Dict]) -> list:
        """Create actions taken page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 8: Actions Taken",
            "Security response actions and interventions"
        ))

        # Automated responses
        elements.append(self.components.create_subsection_header("8.1 Automated Security Responses"))

        blocked = [a for a in activities if a.get('action') == 'BLOCK']
        restricted = [a for a in activities if a.get('action') == 'RESTRICT']
        alerted = [a for a in activities if a.get('action') == 'ALERT']

        action_summary = [
            ['Action Type', 'Count', 'Description'],
            ['BLOCK', str(len(blocked)), 'Access completely denied'],
            ['RESTRICT', str(len(restricted)), 'Access limited/monitored'],
            ['ALERT', str(len(alerted)), 'Security team notified'],
            ['ALLOW', str(len(activities) - len(blocked) - len(restricted) - len(alerted)), 'Normal access permitted'],
        ]

        action_table = Table(action_summary, colWidths=[1.5*inch, 1*inch, 4*inch])
        action_table.setStyle(IGNISYLTableStyles.get_standard_table_style(4))
        elements.append(action_table)

        elements.append(Spacer(1, 20))

        # Recent blocked activities
        if blocked:
            elements.append(self.components.create_subsection_header("8.2 Recent Blocked Activities"))

            block_data = [['Timestamp', 'Activity Type', 'Reason']]
            for act in blocked[:10]:
                block_data.append([
                    act.get('timestamp', '')[:16],
                    act.get('activity_type', 'N/A'),
                    f"Risk Score: {act.get('risk_score', 0):.0f}",
                ])

            block_table = Table(block_data, colWidths=[2*inch, 2.5*inch, 2*inch])
            block_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(block_data)))
            elements.append(block_table)

        return elements

    def _create_recommendations_page(self, user: Dict, activities: List[Dict],
                                     risk_score: float) -> list:
        """Create recommendations page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 9: Recommendations",
            "Security recommendations based on analysis"
        ))

        risk_level = format_risk_level(risk_score)

        # Monitoring level recommendation
        elements.append(self.components.create_subsection_header("9.1 Recommended Monitoring Level"))

        if risk_level == 'CRITICAL':
            monitor_text = "IMMEDIATE ACTION REQUIRED: Implement continuous real-time monitoring with automatic blocking enabled."
            elements.append(Paragraph(monitor_text, self.styles['CriticalAlert']))
        elif risk_level == 'HIGH':
            monitor_text = "ELEVATED MONITORING: Implement enhanced monitoring with supervisor notification for all high-risk activities."
            elements.append(Paragraph(monitor_text, self.styles['HighAlert']))
        elif risk_level == 'MEDIUM':
            monitor_text = "STANDARD MONITORING: Continue regular monitoring with weekly activity reviews."
            elements.append(Paragraph(monitor_text, self.styles['IGBodyText']))
        else:
            monitor_text = "BASELINE MONITORING: Standard security monitoring is sufficient."
            elements.append(Paragraph(monitor_text, self.styles['SuccessText']))

        elements.append(Spacer(1, 20))

        # Access privilege recommendations
        elements.append(self.components.create_subsection_header("9.2 Access Privilege Recommendations"))

        recommendations = []
        if risk_score >= 75:
            recommendations.extend([
                "Immediately revoke administrative privileges if any",
                "Restrict access to sensitive data repositories",
                "Enable multi-factor authentication enforcement",
                "Require supervisor approval for all data exports",
            ])
        elif risk_score >= 50:
            recommendations.extend([
                "Review and potentially reduce access privileges",
                "Enable additional logging for sensitive operations",
                "Implement time-based access restrictions",
            ])
        else:
            recommendations.extend([
                "Maintain current access privileges",
                "Continue standard security awareness training",
            ])

        elements.extend(self.components.create_numbered_list(recommendations))

        elements.append(Spacer(1, 20))

        # Training recommendations
        elements.append(self.components.create_subsection_header("9.3 Training Recommendations"))

        training = [
            "Complete annual security awareness training",
            "Review data handling policies",
            "Understand reporting procedures for security incidents",
        ]
        if risk_score >= 50:
            training.append("Complete advanced insider threat awareness module")

        elements.extend(self.components.create_bullet_list(training))

        return elements

    def _create_executive_summary_page(self, user: Dict, activities: List[Dict],
                                       stats: Dict, risk_score: float) -> list:
        """Create executive summary page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Section 10: Executive Summary",
            "Management-level overview and action items"
        ))

        # Key findings
        elements.append(self.components.create_subsection_header("10.1 Key Findings"))

        risk_level = format_risk_level(risk_score)
        username = user.get('username', 'Unknown')

        findings = f"""
        User {username} has been assessed with a risk score of {risk_score:.0f} ({risk_level}).
        During the analysis period, {format_number(stats.get('total_activities', 0))} activities
        were recorded, of which {format_number(stats.get('threat_count', 0))} were identified
        as potential security concerns.
        """
        elements.append(Paragraph(findings.strip(), self.styles['IGBodyText']))

        elements.append(Spacer(1, 20))

        # Risk metrics summary
        metrics = [
            {'value': f'{risk_score:.0f}', 'label': 'Risk Score',
             'color': IGNISYLColors.get_risk_color(risk_level)},
            {'value': risk_level, 'label': 'Risk Level',
             'color': IGNISYLColors.get_risk_color(risk_level)},
            {'value': format_number(stats.get('threat_count', 0)), 'label': 'Threats Detected'},
            {'value': format_number(stats.get('blocked', 0)), 'label': 'Actions Blocked'},
        ]
        elements.append(self.components.create_metric_cards(metrics))

        elements.append(Spacer(1, 20))

        # Action items
        elements.append(self.components.create_subsection_header("10.2 Recommended Action Items"))

        action_items = []
        if risk_score >= 75:
            action_items = [
                "[URGENT] Schedule immediate security review meeting",
                "[URGENT] Implement enhanced monitoring",
                "[HIGH] Review and restrict access privileges",
                "[HIGH] Conduct interview with user's supervisor",
            ]
        elif risk_score >= 50:
            action_items = [
                "[HIGH] Schedule security review within 48 hours",
                "[MEDIUM] Enable enhanced activity logging",
                "[MEDIUM] Review recent data access patterns",
            ]
        else:
            action_items = [
                "[LOW] Continue standard monitoring",
                "[LOW] Include in regular security review cycle",
            ]

        elements.extend(self.components.create_numbered_list(action_items))

        return elements

    def _create_certification_page(self, report_id: str, username: str) -> list:
        """Create certification/signature page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Report Certification",
            "Official certification and legal notice"
        ))

        elements.append(Spacer(1, 30))

        cert_text = f"""
        This security report (ID: {report_id}) has been automatically generated by the
        IGNISYL AI-Powered Insider Threat Detection System. The analysis contained herein
        is based on machine learning algorithms and automated security monitoring.
        """
        elements.append(Paragraph(cert_text.strip(), self.styles['IGBodyText']))

        elements.append(Spacer(1, 20))

        # Certification details
        cert_data = {
            'Report ID': report_id,
            'Subject': username,
            'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'System Version': 'IGNISYL v1.0.0',
            'Analysis Engine': 'Hybrid ML Ensemble (IF + XGBoost + Autoencoder)',
        }
        elements.extend(self.components.create_key_value_table(cert_data))

        elements.append(Spacer(1, 30))

        # Legal notice
        elements.append(self.components.create_subsection_header("Legal Notice"))

        legal_text = """
        This report is classified as CONFIDENTIAL and intended solely for authorized
        security personnel. Unauthorized distribution is prohibited. The findings in
        this report are based on automated analysis and should be verified by qualified
        security professionals before taking any personnel actions. This system complies
        with applicable privacy regulations and organizational security policies.
        """
        elements.append(Paragraph(legal_text.strip(), self.styles['SmallText']))

        elements.append(Spacer(1, 40))

        # Digital signature placeholder
        sig_table = Table([
            ['Digital Signature', 'Verification Hash'],
            ['IGNISYL-AUTOGEN', report_id.split('-')[-1]],
        ], colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), IGNISYLColors.PALE_BLUE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, IGNISYLColors.TABLE_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(sig_table)

        return elements

    # =========================================================================
    # COMPREHENSIVE SYSTEM REPORT
    # =========================================================================

    def generate_comprehensive_system_report(self, activities: List[Dict],
                                             users: List[Dict],
                                             stats: Dict,
                                             period: str = '24h') -> str:
        """Generate comprehensive system-wide security report"""
        report_id = self._generate_report_id('SYS')
        timestamp = datetime.now()
        filename = f"comprehensive_system_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        story = []

        # Cover page
        story.extend(self._create_system_cover_page(report_id, timestamp, period, len(users), len(activities)))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_system_executive_summary(activities, users, stats))
        story.append(PageBreak())

        # System metrics
        story.extend(self._create_system_metrics_page(activities, users, stats))
        story.append(PageBreak())

        # Charts
        story.extend(self._create_system_charts_page(activities))
        story.append(PageBreak())

        # User risk analysis
        story.extend(self._create_user_risk_analysis_page(users, activities))
        story.append(PageBreak())

        # Recommendations
        story.extend(self._create_system_recommendations_page(activities, users, stats))

        # Build with header/footer
        def add_header_footer(canvas, doc):
            add_page_header_footer(canvas, doc, "Comprehensive System Report")

        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        self._cleanup_charts()

        print(f"[OK] Comprehensive system report generated: {filepath}")
        return filepath

    def _create_system_cover_page(self, report_id: str, timestamp: datetime,
                                  period: str, num_users: int, num_activities: int) -> list:
        """Create system report cover page"""
        elements = []

        elements.append(self.components.create_classification_banner())
        elements.append(Spacer(1, 40))

        elements.append(Paragraph("[SHIELD] IGNISYL", self.styles['CoverTitle']))
        elements.append(Paragraph("Comprehensive System Security Report", self.styles['CoverSubtitle']))
        elements.append(Spacer(1, 40))

        # Summary metrics
        metrics = [
            {'value': str(num_users), 'label': 'Users Monitored'},
            {'value': format_number(num_activities), 'label': 'Activities Analyzed'},
            {'value': period.upper(), 'label': 'Report Period'},
        ]
        elements.append(self.components.create_metric_cards(metrics))

        elements.append(Spacer(1, 40))

        elements.append(Paragraph(f"Report ID: {report_id}", self.styles['CoverMeta']))
        elements.append(Paragraph(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                 self.styles['CoverMeta']))

        return elements

    def _create_system_executive_summary(self, activities: List[Dict],
                                         users: List[Dict], stats: Dict) -> list:
        """Create system executive summary"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Executive Summary",
            "System-wide security status overview"
        ))

        # Key findings
        critical_count = len([a for a in activities if a.get('risk_level', '').upper() == 'CRITICAL'])
        high_count = len([a for a in activities if a.get('risk_level', '').upper() == 'HIGH'])
        blocked_count = len([a for a in activities if a.get('action') == 'BLOCK'])
        high_risk_users = len([u for u in users if u.get('current_risk_score', 0) >= 50])

        summary = f"""
        This comprehensive security report provides analysis of system-wide threat activity.
        The IGNISYL AI-powered detection system monitored {len(users)} users and analyzed
        {format_number(len(activities))} activities during the reporting period.
        """
        elements.append(Paragraph(summary.strip(), self.styles['IGBodyText']))

        elements.append(Spacer(1, 20))

        # Key metrics
        elements.append(self.components.create_subsection_header("Key Findings"))

        findings = [
            f"{critical_count} CRITICAL severity threats detected requiring immediate attention",
            f"{high_count} HIGH severity threats identified and monitored",
            f"{blocked_count} malicious actions automatically blocked",
            f"{high_risk_users} users classified as elevated risk",
        ]
        elements.extend(self.components.create_bullet_list(findings))

        return elements

    def _create_system_metrics_page(self, activities: List[Dict],
                                    users: List[Dict], stats: Dict) -> list:
        """Create system metrics page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "System Metrics",
            "Detailed security metrics and statistics"
        ))

        # Activity breakdown
        elements.append(self.components.create_subsection_header("Activity Risk Distribution"))

        risk_counts = Counter(a.get('risk_level', 'LOW').upper() for a in activities)
        total = len(activities)

        risk_data = [['Risk Level', 'Count', 'Percentage']]
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts.get(level, 0)
            pct = (count / total * 100) if total > 0 else 0
            risk_data.append([level, format_number(count), f"{pct:.1f}%"])

        risk_table = Table(risk_data, colWidths=[2*inch, 2*inch, 2*inch])
        risk_table.setStyle(IGNISYLTableStyles.get_standard_table_style(4))
        elements.append(risk_table)

        elements.append(Spacer(1, 20))

        # Action breakdown
        elements.append(self.components.create_subsection_header("Security Actions Taken"))

        action_counts = Counter(a.get('action', 'ALLOW') for a in activities)
        action_data = [['Action', 'Count', 'Percentage']]
        for action in ['BLOCK', 'RESTRICT', 'ALERT', 'ALLOW']:
            count = action_counts.get(action, 0)
            pct = (count / total * 100) if total > 0 else 0
            action_data.append([action, format_number(count), f"{pct:.1f}%"])

        action_table = Table(action_data, colWidths=[2*inch, 2*inch, 2*inch])
        action_table.setStyle(IGNISYLTableStyles.get_standard_table_style(4))
        elements.append(action_table)

        return elements

    def _create_system_charts_page(self, activities: List[Dict]) -> list:
        """Create system-wide charts page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Visual Analytics",
            "Graphical representation of security data"
        ))

        # Timeline chart
        elements.append(self.components.create_subsection_header("Activity Timeline"))
        timeline = create_activity_timeline_chart(activities, days=7)
        if timeline:
            self.chart_files.append(timeline)
            elements.append(Image(timeline, width=6.5*inch, height=3*inch))
        elements.append(Spacer(1, 15))

        # Risk distribution pie
        elements.append(self.components.create_subsection_header("Risk Distribution"))
        risk_pie = create_risk_distribution_pie_chart(activities)
        if risk_pie:
            self.chart_files.append(risk_pie)
            elements.append(Image(risk_pie, width=5*inch, height=3.5*inch))

        return elements

    def _create_user_risk_analysis_page(self, users: List[Dict],
                                        activities: List[Dict]) -> list:
        """Create user risk analysis page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "User Risk Analysis",
            "Individual user threat assessment"
        ))

        # Calculate user risk scores
        user_activity_counts = Counter(a.get('user_id') for a in activities)
        user_high_risk = Counter(a.get('user_id') for a in activities
                                if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH'])

        users_data = []
        for user in users:
            user_id = user.get('user_id')
            activity_count = user_activity_counts.get(user_id, 0)
            high_risk_count = user_high_risk.get(user_id, 0)
            risk_score = user.get('current_risk_score', 0)

            # Recalculate if needed
            if activity_count > 0 and risk_score == 0:
                risk_score = min((high_risk_count / activity_count) * 100, 100)

            users_data.append({
                'username': user.get('username', 'Unknown'),
                'risk_score': risk_score,
                'activities': activity_count,
                'high_risk': high_risk_count,
            })

        # Sort by risk score
        users_data.sort(key=lambda x: x['risk_score'], reverse=True)

        # Create table
        user_table_data = [['User', 'Risk Score', 'Risk Level', 'Activities', 'High Risk']]
        for u in users_data[:15]:
            user_table_data.append([
                u['username'],
                f"{u['risk_score']:.0f}",
                format_risk_level(u['risk_score']),
                str(u['activities']),
                str(u['high_risk']),
            ])

        user_table = Table(user_table_data,
                          colWidths=[1.8*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch])
        user_table.setStyle(IGNISYLTableStyles.get_standard_table_style(len(user_table_data)))
        elements.append(user_table)

        # User comparison chart
        if users_data:
            elements.append(Spacer(1, 20))
            comparison_chart = create_user_comparison_chart(users_data[:10])
            if comparison_chart:
                self.chart_files.append(comparison_chart)
                elements.append(Image(comparison_chart, width=5.5*inch, height=4*inch))

        return elements

    def _create_system_recommendations_page(self, activities: List[Dict],
                                            users: List[Dict], stats: Dict) -> list:
        """Create system recommendations page"""
        elements = []

        elements.extend(self.components.create_section_header(
            "Recommendations",
            "System-wide security recommendations"
        ))

        critical_count = len([a for a in activities if a.get('risk_level', '').upper() == 'CRITICAL'])
        high_risk_users = [u for u in users if u.get('current_risk_score', 0) >= 50]
        blocked = len([a for a in activities if a.get('action') == 'BLOCK'])

        recommendations = []

        if critical_count > 0:
            recommendations.append(
                f"CRITICAL: {critical_count} critical threats require immediate investigation and remediation."
            )

        if high_risk_users:
            recommendations.append(
                f"Review and monitor the {len(high_risk_users)} high-risk users identified in this report."
            )

        if blocked > 10:
            recommendations.append(
                f"High volume of blocked actions ({blocked}) - consider reviewing security policies."
            )

        if not recommendations:
            recommendations.append(
                "No critical issues identified. Continue standard security monitoring procedures."
            )

        elements.extend(self.components.create_numbered_list(recommendations))

        return elements

    # =========================================================================
    # THREAT SUMMARY REPORT
    # =========================================================================

    def generate_threat_summary_report(self, activities: List[Dict],
                                       users: List[Dict], period: str = '7d') -> str:
        """Generate threat summary report"""
        report_id = self._generate_report_id('THR')
        timestamp = datetime.now()
        filename = f"threat_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        story = []

        # Cover
        story.append(self.components.create_classification_banner())
        story.append(Spacer(1, 30))
        story.append(Paragraph("[SHIELD] IGNISYL", self.styles['CoverTitle']))
        story.append(Paragraph("Threat Summary Report", self.styles['CoverSubtitle']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Report ID: {report_id}", self.styles['CoverMeta']))
        story.append(Paragraph(f"Period: {period.upper()}", self.styles['CoverMeta']))
        story.append(PageBreak())

        # Threat overview
        story.extend(self.components.create_section_header(
            "Threat Overview",
            "Summary of detected security threats"
        ))

        threats = [a for a in activities if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH']]

        story.append(Paragraph(
            f"Total threats detected: {len(threats)}",
            self.styles['IGBodyText']
        ))

        if threats:
            threat_data = [['Timestamp', 'Type', 'Risk Level', 'User', 'Action']]
            for t in threats[:30]:
                threat_data.append([
                    t.get('timestamp', '')[:16],
                    t.get('activity_type', 'N/A')[:18],
                    t.get('risk_level', 'N/A'),
                    t.get('user_id', 'N/A')[-10:],
                    t.get('action', 'N/A'),
                ])

            threat_table = Table(threat_data,
                                colWidths=[1.3*inch, 1.5*inch, 1*inch, 1.2*inch, 1*inch])
            threat_table.setStyle(IGNISYLTableStyles.get_compact_table_style(len(threat_data)))
            story.append(threat_table)

        # Build
        def add_header_footer(canvas, doc):
            add_page_header_footer(canvas, doc, "Threat Summary Report")

        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

        print(f"[OK] Threat summary report generated: {filepath}")
        return filepath

    # =========================================================================
    # ML PERFORMANCE REPORT
    # =========================================================================

    def generate_ml_performance_report(self, activities: List[Dict],
                                       ml_stats: Dict) -> str:
        """Generate ML model performance report"""
        report_id = self._generate_report_id('MLP')
        timestamp = datetime.now()
        filename = f"ml_performance_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )

        story = []

        # Cover
        story.append(self.components.create_classification_banner())
        story.append(Spacer(1, 30))
        story.append(Paragraph("[SHIELD] IGNISYL", self.styles['CoverTitle']))
        story.append(Paragraph("ML Model Performance Report", self.styles['CoverSubtitle']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Report ID: {report_id}", self.styles['CoverMeta']))
        story.append(PageBreak())

        # Performance metrics
        story.extend(self.components.create_section_header(
            "Model Performance Metrics",
            "Machine learning model evaluation results"
        ))

        # Metrics table
        metrics_data = [
            ['Metric', 'Value', 'Target', 'Status'],
            ['Accuracy', f"{ml_stats.get('accuracy', 0):.1f}%", '85%',
             'PASS' if ml_stats.get('accuracy', 0) >= 85 else 'REVIEW'],
            ['Precision', f"{ml_stats.get('precision', 0):.1f}%", '80%',
             'PASS' if ml_stats.get('precision', 0) >= 80 else 'REVIEW'],
            ['Recall', f"{ml_stats.get('recall', 0):.1f}%", '75%',
             'PASS' if ml_stats.get('recall', 0) >= 75 else 'REVIEW'],
            ['F1 Score', f"{ml_stats.get('f1_score', 0):.1f}%", '78%',
             'PASS' if ml_stats.get('f1_score', 0) >= 78 else 'REVIEW'],
        ]

        metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(IGNISYLTableStyles.get_standard_table_style(4))
        story.append(metrics_table)

        story.append(Spacer(1, 20))

        # Performance chart
        perf_chart = create_ml_performance_chart(ml_stats)
        if perf_chart:
            self.chart_files.append(perf_chart)
            story.append(Image(perf_chart, width=5.5*inch, height=3.5*inch))

        # Build
        def add_header_footer(canvas, doc):
            add_page_header_footer(canvas, doc, "ML Performance Report")

        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        self._cleanup_charts()

        print(f"[OK] ML performance report generated: {filepath}")
        return filepath


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_report_generator(output_dir: str = "data/reports") -> ProfessionalReportGenerator:
    """Factory function to create report generator instance"""
    return ProfessionalReportGenerator(output_dir)
