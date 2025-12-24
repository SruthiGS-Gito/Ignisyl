"""
PDF Report Generator for IGNISYL
Generates professional threat detection reports
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import Dict, List
import os

class ReportGenerator:
    """Generates PDF reports for threat analysis"""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3c72'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2a5298'),
            spaceAfter=12,
            spaceBefore=12
        )
    
    def generate_threat_report(self, user_data: Dict, activities: List[Dict], 
                               summary_stats: Dict) -> str:
        """
        Generate comprehensive threat report for a user
        
        Args:
            user_data: User information
            activities: List of threat activities
            summary_stats: Summary statistics
            
        Returns:
            Path to generated PDF file
        """
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"threat_report_{user_data.get('username', 'user')}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph("[SHIELD] IGNISYL - Threat Detection Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Report metadata
        metadata = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Report Type:', 'User Threat Analysis'],
            ['Classification:', 'CONFIDENTIAL']
        ]
        
        t = Table(metadata, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * inch))
        
        # User Information Section
        story.append(Paragraph("User Information", self.heading_style))
        
        user_info = [
            ['Field', 'Value'],
            ['User ID', user_data.get('user_id', 'N/A')],
            ['Full Name', user_data.get('full_name', 'N/A')],
            ['Username', user_data.get('username', 'N/A')],
            ['Department', user_data.get('department', 'N/A')],
            ['Role', user_data.get('role', 'N/A')],
            ['Current Risk Score', f"{user_data.get('current_risk_score', 0):.1f}"],
            ['Total Threats', str(user_data.get('total_threats', 0))]
        ]
        
        t = Table(user_info, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", self.heading_style))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Activities Analyzed', str(summary_stats.get('total_activities', 0))],
            ['High Risk Activities', str(summary_stats.get('high_risk', 0))],
            ['Medium Risk Activities', str(summary_stats.get('medium_risk', 0))],
            ['Low Risk Activities', str(summary_stats.get('low_risk', 0))],
            ['Actions Blocked', str(summary_stats.get('blocked', 0))],
            ['Actions Restricted', str(summary_stats.get('restricted', 0))]
        ]
        
        t = Table(summary_data, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))
        
        # Threat Activities Table
        if activities:
            story.append(Paragraph("Detailed Threat Activities", self.heading_style))
            
            # Prepare activity data
            activity_data = [['Timestamp', 'Activity', 'Risk Score', 'Level', 'Action']]
            
            for activity in activities[:20]:  # Limit to 20 most recent
                activity_data.append([
                    datetime.fromisoformat(activity['timestamp']).strftime('%Y-%m-%d %H:%M'),
                    activity['activity_type'].replace('_', ' ').title()[:20],
                    f"{activity['risk_score']:.1f}",
                    activity['risk_level'],
                    activity['action']
                ])
            
            t = Table(activity_data, colWidths=[1.5*inch, 1.8*inch, 1*inch, 0.8*inch, 0.9*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            # Color code risk levels
            for i, activity in enumerate(activities[:20], start=1):
                if activity['risk_level'] == 'HIGH':
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (3, i), (3, i), colors.red),
                        ('TEXTCOLOR', (3, i), (3, i), colors.whitesmoke)
                    ]))
                elif activity['risk_level'] == 'MEDIUM':
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (3, i), (3, i), colors.orange)
                    ]))
                else:
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (3, i), (3, i), colors.lightgreen)
                    ]))
            
            story.append(t)
        else:
            story.append(Paragraph("No threat activities recorded for this user.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.heading_style))
        
        recommendations = self._generate_recommendations(user_data, summary_stats)
        for rec in recommendations:
            bullet = Paragraph(f"• {rec}", self.styles['Normal'])
            story.append(bullet)
            story.append(Spacer(1, 0.1 * inch))
        
        # Footer
        story.append(Spacer(1, 0.5 * inch))
        footer_text = f"<para align=center><font size=8>Generated by IGNISYL - AI-Powered Insider Threat Detection System<br/>" \
                     f"Report ID: {timestamp}<br/>" \
                     f"© 2025 IGNISYL Project - Confidential</font></para>"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        print(f"[OK] Report generated: {filepath}")
        return filepath
    
    def _generate_recommendations(self, user_data: Dict, summary_stats: Dict) -> List[str]:
        """Generate recommendations based on user risk profile"""
        recommendations = []
        
        risk_score = user_data.get('current_risk_score', 0)
        total_threats = user_data.get('total_threats', 0)
        high_risk = summary_stats.get('high_risk', 0)
        
        if risk_score >= 70:
            recommendations.append("IMMEDIATE ACTION REQUIRED: User poses HIGH security risk. Consider temporary access suspension pending investigation.")
            recommendations.append("Conduct thorough security interview with user and their manager.")
            recommendations.append("Review all recent file access and data transfers.")
        
        if high_risk > 5:
            recommendations.append(f"User has {high_risk} high-risk activities. Implement enhanced monitoring.")
            recommendations.append("Restrict access to sensitive data and systems.")
        
        if total_threats > 10:
            recommendations.append("Schedule mandatory security awareness training.")
            recommendations.append("Review user's access privileges and apply principle of least privilege.")
        
        if risk_score >= 30 and risk_score < 70:
            recommendations.append("Implement weekly check-ins with user's supervisor.")
            recommendations.append("Monitor for pattern changes in behavior.")
        
        if risk_score < 30 and total_threats == 0:
            recommendations.append("User demonstrates good security practices. No action required.")
            recommendations.append("Continue standard monitoring.")
        
        if not recommendations:
            recommendations.append("Maintain current monitoring level.")
            recommendations.append("Review user activity on a monthly basis.")
        
        return recommendations
    
    def generate_system_report(self, all_activities: List[Dict], 
                               system_stats: Dict, time_period: str = "24h") -> str:
        """
        Generate system-wide threat report
        
        Args:
            all_activities: All threat activities
            system_stats: System statistics
            time_period: Time period for report
            
        Returns:
            Path to generated PDF file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"system_report_{time_period}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(f"[SHIELD] IGNISYL - System Threat Report ({time_period})", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.5 * inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        
        summary_text = f"""
        This report provides a comprehensive overview of security threats detected by the IGNISYL 
        system over the past {time_period}. The analysis includes threat patterns, user risk profiles, 
        and recommended actions for maintaining organizational security.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # System-wide statistics
        story.append(Paragraph("System Statistics", self.heading_style))
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Threats Detected', str(system_stats.get('total_threats', 0))],
            ['High Risk Threats', str(system_stats.get('high_risk_threats', 0))],
            ['Medium Risk Threats', str(system_stats.get('medium_risk_threats', 0))],
            ['Low Risk Threats', str(system_stats.get('low_risk_threats', 0))],
            ['Actions Blocked', str(system_stats.get('blocked_actions', 0))],
            ['Users Monitored', str(system_stats.get('total_users', 0))],
            ['High Risk Users', str(system_stats.get('high_risk_users', 0))]
        ]
        
        t = Table(stats_data, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * inch))
        
        # Top threats
        if all_activities:
            story.append(Paragraph("Top 10 Threat Activities", self.heading_style))
            
            # Sort by risk score
            sorted_activities = sorted(all_activities, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]
            
            threat_data = [['User', 'Activity', 'Risk', 'Timestamp']]
            for activity in sorted_activities:
                threat_data.append([
                    activity.get('full_name', 'Unknown')[:15],
                    activity.get('activity_type', 'Unknown').replace('_', ' ')[:20],
                    f"{activity.get('risk_score', 0):.1f}",
                    datetime.fromisoformat(activity['timestamp']).strftime('%m-%d %H:%M')
                ])
            
            t = Table(threat_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(t)
        
        # Build PDF
        doc.build(story)
        
        print(f"[OK] System report generated: {filepath}")
        return filepath

# Global instance
report_generator = ReportGenerator()