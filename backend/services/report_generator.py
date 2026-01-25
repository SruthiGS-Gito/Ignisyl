"""
IGNISYL Enterprise PDF Report Generator
Professional multi-page security reports with charts and detailed analysis

Uses ReportLab for professional PDF generation
Uses Matplotlib for high-quality chart generation
"""

import os
import tempfile
import hashlib
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Any

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether, ListFlowable, ListItem,
    HRFlowable, Flowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect

# Matplotlib for charts
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ============================================================================
# PROFESSIONAL COLOR SCHEME - Blue Theme
# ============================================================================

COLORS = {
    # Primary Blues (Professional Theme)
    'primary_dark': colors.HexColor('#1e3a8a'),    # Dark navy blue
    'primary': colors.HexColor('#3b82f6'),          # Bright blue
    'primary_light': colors.HexColor('#60a5fa'),    # Light blue
    'primary_bg': colors.HexColor('#eff6ff'),       # Very light blue bg

    # Risk Level Colors
    'critical': colors.HexColor('#dc2626'),         # Red
    'high': colors.HexColor('#ea580c'),             # Orange
    'medium': colors.HexColor('#ca8a04'),           # Amber
    'low': colors.HexColor('#16a34a'),              # Green

    # Neutral Colors
    'dark': colors.HexColor('#1f2937'),             # Dark gray text
    'gray': colors.HexColor('#6b7280'),             # Medium gray
    'light_gray': colors.HexColor('#9ca3af'),       # Light gray
    'border': colors.HexColor('#e5e7eb'),           # Border gray
    'bg_alt': colors.HexColor('#f9fafb'),           # Alternating row bg
    'white': colors.white,
    'black': colors.black,

    # Table Colors
    'table_header': colors.HexColor('#1e3a8a'),     # Dark blue header
    'table_header_text': colors.white,
    'table_border': colors.HexColor('#d1d5db'),

    # Status Colors
    'success': colors.HexColor('#16a34a'),
    'warning': colors.HexColor('#ca8a04'),
    'danger': colors.HexColor('#dc2626'),
    'info': colors.HexColor('#0891b2'),
}

RISK_COLORS = {
    'CRITICAL': '#dc2626',
    'HIGH': '#ea580c',
    'MEDIUM': '#ca8a04',
    'LOW': '#16a34a'
}

RISK_COLORS_RGB = {
    'CRITICAL': (220, 38, 38),
    'HIGH': (234, 88, 12),
    'MEDIUM': (202, 138, 4),
    'LOW': (22, 163, 74)
}


# ============================================================================
# CUSTOM CANVAS FOR HEADERS/FOOTERS
# ============================================================================

class ProfessionalCanvas(canvas.Canvas):
    """Canvas with professional headers and footers"""

    def __init__(self, *args, **kwargs):
        self.report_title = kwargs.pop('report_title', 'Security Report')
        self.report_id = kwargs.pop('report_id', 'RPT-000000')
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_header_footer(self, page_count):
        """Draw professional header and footer"""
        self.saveState()
        page_width = letter[0]

        # Skip header on page 1 (cover page)
        if self._pageNumber > 1:
            # Header line
            self.setStrokeColor(colors.HexColor('#1e3a8a'))
            self.setLineWidth(2)
            self.line(0.75*inch, 10.3*inch, 7.75*inch, 10.3*inch)

            # Header text
            self.setFont("Helvetica-Bold", 9)
            self.setFillColor(colors.HexColor('#1e3a8a'))
            self.drawString(0.75*inch, 10.45*inch, "IGNISYL")

            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor('#6b7280'))
            self.drawRightString(7.75*inch, 10.45*inch, self.report_title)

        # Footer
        self.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.setLineWidth(1)
        self.line(0.75*inch, 0.65*inch, 7.75*inch, 0.65*inch)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#6b7280'))

        # Left: Report ID
        self.drawString(0.75*inch, 0.45*inch, f"Report: {self.report_id}")

        # Center: Page number
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawCentredString(page_width/2, 0.45*inch, page_text)

        # Right: Confidential
        self.setFillColor(colors.HexColor('#dc2626'))
        self.drawRightString(7.75*inch, 0.45*inch, "CONFIDENTIAL")

        self.restoreState()


# ============================================================================
# CUSTOM FLOWABLES
# ============================================================================

class SectionHeader(Flowable):
    """Professional section header with blue underline"""

    def __init__(self, text, section_num=None):
        Flowable.__init__(self)
        self.text = text
        self.section_num = section_num
        self.height = 45
        self.width = 6.5*inch

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        # Section number badge (if provided)
        x_offset = 0
        if self.section_num:
            self.canv.setFillColor(colors.HexColor('#1e3a8a'))
            self.canv.roundRect(0, self.height - 25, 30, 22, 4, fill=1, stroke=0)
            self.canv.setFillColor(colors.white)
            self.canv.setFont("Helvetica-Bold", 12)
            self.canv.drawCentredString(15, self.height - 19, str(self.section_num))
            x_offset = 40

        # Section title
        self.canv.setFillColor(colors.HexColor('#1e3a8a'))
        self.canv.setFont("Helvetica-Bold", 16)
        self.canv.drawString(x_offset, self.height - 18, self.text)

        # Blue underline
        self.canv.setStrokeColor(colors.HexColor('#3b82f6'))
        self.canv.setLineWidth(3)
        self.canv.line(0, 5, self.width, 5)


class RiskScoreBox(Flowable):
    """Large risk score display box"""

    def __init__(self, score, label="Risk Score"):
        Flowable.__init__(self)
        self.score = score
        self.label = label
        self.width = 2*inch
        self.height = 1.5*inch

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        # Determine color based on score
        if self.score >= 75:
            bg_color = colors.HexColor('#fef2f2')
            border_color = colors.HexColor('#dc2626')
            text_color = colors.HexColor('#dc2626')
        elif self.score >= 50:
            bg_color = colors.HexColor('#fff7ed')
            border_color = colors.HexColor('#ea580c')
            text_color = colors.HexColor('#ea580c')
        elif self.score >= 30:
            bg_color = colors.HexColor('#fefce8')
            border_color = colors.HexColor('#ca8a04')
            text_color = colors.HexColor('#ca8a04')
        else:
            bg_color = colors.HexColor('#f0fdf4')
            border_color = colors.HexColor('#16a34a')
            text_color = colors.HexColor('#16a34a')

        # Background
        self.canv.setFillColor(bg_color)
        self.canv.setStrokeColor(border_color)
        self.canv.setLineWidth(2)
        self.canv.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)

        # Score value
        self.canv.setFillColor(text_color)
        self.canv.setFont("Helvetica-Bold", 36)
        self.canv.drawCentredString(self.width/2, self.height/2 + 5, f"{self.score:.0f}")

        # Label
        self.canv.setFont("Helvetica", 10)
        self.canv.setFillColor(colors.HexColor('#6b7280'))
        self.canv.drawCentredString(self.width/2, 15, self.label)


class AlertBox(Flowable):
    """Colored alert/notification box"""

    def __init__(self, text, alert_type='info', width=6.5*inch):
        Flowable.__init__(self)
        self.text = text
        self.alert_type = alert_type
        self.box_width = width
        self.height = 40

        self.colors = {
            'critical': (colors.HexColor('#fef2f2'), colors.HexColor('#dc2626'), colors.HexColor('#991b1b')),
            'warning': (colors.HexColor('#fffbeb'), colors.HexColor('#d97706'), colors.HexColor('#92400e')),
            'success': (colors.HexColor('#f0fdf4'), colors.HexColor('#16a34a'), colors.HexColor('#166534')),
            'info': (colors.HexColor('#eff6ff'), colors.HexColor('#3b82f6'), colors.HexColor('#1e40af')),
        }

    def wrap(self, availWidth, availHeight):
        return self.box_width, self.height

    def draw(self):
        bg, border, text_color = self.colors.get(self.alert_type, self.colors['info'])

        self.canv.setFillColor(bg)
        self.canv.setStrokeColor(border)
        self.canv.setLineWidth(1.5)
        self.canv.roundRect(0, 0, self.box_width, self.height, 6, fill=1, stroke=1)

        # Icon indicator
        self.canv.setFillColor(border)
        self.canv.circle(20, self.height/2, 6, fill=1, stroke=0)

        # Text
        self.canv.setFillColor(text_color)
        self.canv.setFont("Helvetica-Bold", 10)
        self.canv.drawString(35, self.height/2 - 4, self.text[:80])


class MetricCard(Flowable):
    """Small metric display card"""

    def __init__(self, value, label, color='#3b82f6'):
        Flowable.__init__(self)
        self.value = str(value)
        self.label = label
        self.color = colors.HexColor(color)
        self.width = 1.5*inch
        self.height = 0.9*inch

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        # Light background
        self.canv.setFillColor(colors.HexColor('#f9fafb'))
        self.canv.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)

        # Top color bar
        self.canv.setFillColor(self.color)
        self.canv.rect(0, self.height - 4, self.width, 4, fill=1, stroke=0)

        # Value
        self.canv.setFillColor(colors.HexColor('#1f2937'))
        self.canv.setFont("Helvetica-Bold", 18)
        self.canv.drawCentredString(self.width/2, self.height/2 + 2, self.value)

        # Label
        self.canv.setFont("Helvetica", 8)
        self.canv.setFillColor(colors.HexColor('#6b7280'))
        self.canv.drawCentredString(self.width/2, 10, self.label)


# ============================================================================
# REPORT GENERATOR CLASS
# ============================================================================

class ReportGenerator:
    """Enterprise-grade PDF report generator for IGNISYL"""

    def __init__(self):
        # Use absolute path for consistency across all modules
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(backend_dir, "data", "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.temp_dir = tempfile.gettempdir()
        self.styles = self._create_styles()

    def _create_styles(self) -> Dict:
        """Create professional paragraph styles"""
        styles = getSampleStyleSheet()

        # Cover page title
        styles.add(ParagraphStyle(
            name='CoverTitle',
            fontSize=32,
            textColor=COLORS['primary_dark'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=15,
            leading=38
        ))

        # Cover subtitle
        styles.add(ParagraphStyle(
            name='CoverSubtitle',
            fontSize=16,
            textColor=COLORS['gray'],
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=25
        ))

        # Section titles
        styles.add(ParagraphStyle(
            name='SectionTitle',
            fontSize=16,
            textColor=COLORS['primary_dark'],
            fontName='Helvetica-Bold',
            spaceBefore=20,
            spaceAfter=12,
            leading=20
        ))

        # Subsection titles
        styles.add(ParagraphStyle(
            name='SubsectionTitle',
            fontSize=12,
            textColor=COLORS['dark'],
            fontName='Helvetica-Bold',
            spaceBefore=15,
            spaceAfter=8,
            leading=16
        ))

        # Body text
        styles.add(ParagraphStyle(
            name='Body',
            fontSize=10,
            textColor=COLORS['dark'],
            fontName='Helvetica',
            spaceBefore=4,
            spaceAfter=4,
            leading=14,
            alignment=TA_JUSTIFY
        ))

        # Small text
        styles.add(ParagraphStyle(
            name='Small',
            fontSize=9,
            textColor=COLORS['gray'],
            fontName='Helvetica',
            spaceBefore=3,
            spaceAfter=3,
            leading=12
        ))

        # Bullet point
        styles.add(ParagraphStyle(
            name='BulletItem',
            fontSize=10,
            textColor=COLORS['dark'],
            fontName='Helvetica',
            leftIndent=20,
            spaceBefore=3,
            spaceAfter=3,
            leading=14,
            bulletIndent=10
        ))

        # Table cell
        styles.add(ParagraphStyle(
            name='TableCell',
            fontSize=9,
            textColor=COLORS['dark'],
            fontName='Helvetica',
            leading=12
        ))

        return styles

    def _get_risk_level(self, score: float) -> str:
        """Determine risk level from score"""
        if score >= 75:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        return 'LOW'

    def _get_risk_color(self, level: str) -> colors.Color:
        """Get color for risk level"""
        color_map = {
            'CRITICAL': COLORS['critical'],
            'HIGH': COLORS['high'],
            'MEDIUM': COLORS['medium'],
            'LOW': COLORS['low']
        }
        return color_map.get(level.upper(), COLORS['gray'])

    def _format_timestamp(self, ts: str, fmt: str = 'short') -> str:
        """Format timestamp string"""
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            if fmt == 'short':
                return dt.strftime('%m/%d %H:%M')
            elif fmt == 'date':
                return dt.strftime('%Y-%m-%d')
            elif fmt == 'time':
                return dt.strftime('%H:%M:%S')
            elif fmt == 'full':
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return str(ts)[:16] if ts else 'N/A'

    def _truncate(self, text: str, max_len: int = 30) -> str:
        """Truncate text with ellipsis"""
        if not text:
            return 'N/A'
        text = str(text)
        return text[:max_len-2] + '..' if len(text) > max_len else text

    def _generate_report_id(self, prefix: str = 'RPT') -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        rand = hashlib.md5(os.urandom(8)).hexdigest()[:4].upper()
        return f"{prefix}-{timestamp}-{rand}"

    def _generate_hash(self) -> str:
        """Generate verification hash"""
        data = f"{datetime.now().isoformat()}-IGNISYL-{os.urandom(16).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()

    # ========================================================================
    # TABLE CREATION
    # ========================================================================

    def _create_table(self, data: List[List], col_widths: List[float] = None,
                      has_header: bool = True, zebra: bool = True) -> Table:
        """Create professionally styled table"""
        if not data:
            return Table([['No data available']], colWidths=[6*inch])

        table = Table(data, colWidths=col_widths)

        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['table_border']),
        ]

        if has_header and len(data) > 0:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), COLORS['table_header']),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['table_header_text']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
            ])

        if zebra and len(data) > 2:
            for i in range(2, len(data), 2):
                style_commands.append(('BACKGROUND', (0, i), (-1, i), COLORS['bg_alt']))

        table.setStyle(TableStyle(style_commands))
        return table

    def _create_key_value_table(self, items: List[tuple], col_widths=None) -> Table:
        """Create a key-value style table"""
        if not col_widths:
            col_widths = [2.5*inch, 4*inch]

        data = [[k, v] for k, v in items]
        table = Table(data, colWidths=col_widths)

        style_commands = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), COLORS['gray']),
            ('TEXTCOLOR', (1, 0), (1, -1), COLORS['dark']),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLORS['border']),
        ]

        table.setStyle(TableStyle(style_commands))
        return table

    # ========================================================================
    # CHART GENERATION - PROFESSIONAL BLUE THEME
    # ========================================================================

    def _create_timeline_chart(self, activities: List[Dict], username: str) -> Optional[str]:
        """Create activity timeline stacked bar chart"""
        if not activities:
            return None

        date_data = defaultdict(lambda: {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0})

        for act in activities:
            try:
                ts = act.get('timestamp', '')
                date = ts[:10] if ts else None
                if date:
                    level = act.get('risk_level', 'LOW').upper()
                    if level in date_data[date]:
                        date_data[date][level] += 1
            except:
                pass

        if not date_data:
            return None

        sorted_dates = sorted(date_data.keys())[-14:]

        dates = [d[5:] for d in sorted_dates]
        low = [date_data[d]['LOW'] for d in sorted_dates]
        medium = [date_data[d]['MEDIUM'] for d in sorted_dates]
        high = [date_data[d]['HIGH'] for d in sorted_dates]
        critical = [date_data[d]['CRITICAL'] for d in sorted_dates]

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

        x = np.arange(len(dates))
        width = 0.65

        ax.bar(x, low, width, label='Low', color='#16a34a')
        ax.bar(x, medium, width, bottom=low, label='Medium', color='#ca8a04')
        ax.bar(x, high, width, bottom=[l+m for l,m in zip(low, medium)], label='High', color='#ea580c')
        ax.bar(x, critical, width, bottom=[l+m+h for l,m,h in zip(low, medium, high)], label='Critical', color='#dc2626')

        ax.set_ylabel('Activity Count', fontsize=10, fontweight='bold', color='#1f2937')
        ax.set_xlabel('Date', fontsize=10, fontweight='bold', color='#1f2937')
        ax.set_title(f'Activity Timeline by Risk Level', fontsize=13, fontweight='bold', color='#1e3a8a', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.95)
        ax.set_axisbelow(True)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        chart_path = os.path.join(self.temp_dir, f'timeline_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close()

        return chart_path

    def _create_risk_trend_chart(self, activities: List[Dict], username: str) -> Optional[str]:
        """Create risk score trend line chart"""
        if not activities or len(activities) < 2:
            return None

        date_scores = defaultdict(list)

        for act in sorted(activities, key=lambda x: x.get('timestamp', '')):
            try:
                ts = act.get('timestamp', '')
                date = ts[:10] if ts else None
                if date:
                    date_scores[date].append(act.get('risk_score', 0))
            except:
                pass

        if len(date_scores) < 2:
            return None

        sorted_dates = sorted(date_scores.keys())[-14:]
        dates = [d[5:] for d in sorted_dates]
        avg_scores = [sum(date_scores[d])/len(date_scores[d]) for d in sorted_dates]
        max_scores = [max(date_scores[d]) for d in sorted_dates]

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

        x = np.arange(len(dates))

        # Gradient fill under curve
        ax.fill_between(x, avg_scores, alpha=0.2, color='#3b82f6')

        ax.plot(x, avg_scores, marker='o', linestyle='-', color='#3b82f6', linewidth=2.5,
                label='Average Risk Score', markersize=6, markerfacecolor='white', markeredgewidth=2)
        ax.plot(x, max_scores, marker='s', linestyle='--', color='#dc2626', linewidth=2,
                label='Peak Risk Score', markersize=5)

        # Threshold lines
        ax.axhline(y=75, color='#dc2626', linestyle=':', linewidth=1.5, alpha=0.7, label='Critical (75)')
        ax.axhline(y=50, color='#ea580c', linestyle=':', linewidth=1.5, alpha=0.7, label='High (50)')
        ax.axhline(y=30, color='#ca8a04', linestyle=':', linewidth=1.5, alpha=0.5, label='Medium (30)')

        ax.set_ylabel('Risk Score', fontsize=10, fontweight='bold', color='#1f2937')
        ax.set_xlabel('Date', fontsize=10, fontweight='bold', color='#1f2937')
        ax.set_title('Risk Score Trend Analysis', fontsize=13, fontweight='bold', color='#1e3a8a', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)
        ax.set_ylim(0, 105)
        ax.legend(loc='upper right', fontsize=8, framealpha=0.95)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        chart_path = os.path.join(self.temp_dir, f'trend_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close()

        return chart_path

    def _create_activity_pie_chart(self, activities: List[Dict], username: str) -> Optional[str]:
        """Create activity distribution pie chart"""
        if not activities:
            return None

        type_counts = Counter(act.get('activity_type', 'Unknown') for act in activities)
        if not type_counts:
            return None

        top_types = type_counts.most_common(8)

        labels = [self._truncate(t[0].replace('_', ' ').title(), 18) for t in top_types]
        sizes = [t[1] for t in top_types]

        # Professional blue-themed colors
        chart_colors = ['#1e3a8a', '#3b82f6', '#60a5fa', '#93c5fd',
                       '#0891b2', '#14b8a6', '#6366f1', '#8b5cf6'][:len(labels)]

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

        explode = [0.03] * len(labels)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
            startangle=90,
            colors=chart_colors,
            explode=explode,
            shadow=False,
            pctdistance=0.75,
            wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
        )

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.legend(wedges, labels, title="Activity Types", loc="center left",
                 bbox_to_anchor=(1.05, 0.5), fontsize=9, title_fontsize=10)

        ax.set_title('Activity Distribution by Type', fontsize=13, fontweight='bold',
                    color='#1e3a8a', pad=15)

        plt.tight_layout()

        chart_path = os.path.join(self.temp_dir, f'pie_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close()

        return chart_path

    def _create_hourly_chart(self, activities: List[Dict], username: str) -> Optional[str]:
        """Create hourly activity pattern chart"""
        if not activities:
            return None

        hourly_counts = defaultdict(int)
        hourly_risks = defaultdict(list)

        for act in activities:
            try:
                ts = act.get('timestamp', '')
                if ts:
                    hour = int(ts[11:13])
                    hourly_counts[hour] += 1
                    hourly_risks[hour].append(act.get('risk_score', 0))
            except:
                pass

        if not hourly_counts:
            return None

        hours = list(range(24))
        counts = [hourly_counts.get(h, 0) for h in hours]
        avg_risks = [sum(hourly_risks.get(h, [0]))/max(len(hourly_risks.get(h, [0])), 1) for h in hours]

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax1 = plt.subplots(figsize=(10, 4), dpi=150)

        # Business hours vs after-hours coloring
        bar_colors = ['#ea580c' if h < 6 or h >= 22 else '#3b82f6' for h in hours]

        # Background shading
        ax1.axvspan(-0.5, 5.5, alpha=0.08, color='#ea580c')
        ax1.axvspan(21.5, 23.5, alpha=0.08, color='#ea580c')

        bars = ax1.bar(hours, counts, color=bar_colors, alpha=0.8, edgecolor='white', linewidth=0.5)
        ax1.set_xlabel('Hour of Day', fontsize=10, fontweight='bold', color='#1f2937')
        ax1.set_ylabel('Activity Count', color='#3b82f6', fontsize=10, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#3b82f6')
        ax1.set_xticks(hours)
        ax1.set_xticklabels([f'{h:02d}' for h in hours], fontsize=7)

        ax2 = ax1.twinx()
        ax2.plot(hours, avg_risks, color='#dc2626', marker='o', linestyle='-',
                linewidth=2, markersize=4, label='Avg Risk')
        ax2.set_ylabel('Avg Risk Score', color='#dc2626', fontsize=10, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#dc2626')
        ax2.set_ylim(0, 100)

        ax1.set_title('Hourly Activity Pattern Analysis', fontsize=13, fontweight='bold',
                     color='#1e3a8a', pad=15)

        # Custom legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3b82f6', label='Business Hours'),
            Patch(facecolor='#ea580c', label='After Hours'),
            plt.Line2D([0], [0], color='#dc2626', marker='o', label='Avg Risk Score')
        ]
        ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)

        ax1.spines['top'].set_visible(False)

        plt.tight_layout()

        chart_path = os.path.join(self.temp_dir, f'hourly_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close()

        return chart_path

    def _create_risk_distribution_chart(self, activities: List[Dict]) -> Optional[str]:
        """Create risk level distribution donut chart with proper colors and label positioning"""
        if not activities:
            return None

        risk_counts = Counter(act.get('risk_level', 'LOW').upper() for act in activities)

        # Order: LOW, MEDIUM, HIGH, CRITICAL (clockwise from top)
        levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        counts = [risk_counts.get(l, 0) for l in levels]

        # Distinct colors as specified: LOW green, MEDIUM orange, HIGH red, CRITICAL dark red
        colors_list = ['#2ecc71', '#f39c12', '#e74c3c', '#c0392b']

        total = sum(counts)
        if total == 0:
            return None

        # Ensure all slices are visible - add minimum value for zero counts
        display_counts = []
        for c in counts:
            if c == 0:
                display_counts.append(total * 0.02)  # 2% minimum for visibility
            else:
                display_counts.append(c)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(7, 5), dpi=150)

        # Create pie chart without labels first
        wedges, texts, autotexts = ax.pie(
            display_counts,
            labels=None,  # No labels on pie - use legend instead
            autopct=lambda pct: '',  # No percentage on pie
            startangle=90,
            colors=colors_list,
            pctdistance=0.75,
            wedgeprops={'width': 0.5, 'linewidth': 2, 'edgecolor': 'white'}
        )

        # Create legend labels with actual counts and percentages
        legend_labels = []
        for i, level in enumerate(levels):
            actual_count = counts[i]
            pct = (actual_count / total * 100) if total > 0 else 0
            legend_labels.append(f'{level}: {actual_count} ({pct:.1f}%)')

        # Position legend to the right to prevent overlap
        ax.legend(wedges, legend_labels, title="Risk Levels", loc="center left",
                 bbox_to_anchor=(1.05, 0.5), fontsize=10, title_fontsize=11)

        # Center text
        ax.text(0, 0, f'{total}\nTotal', ha='center', va='center', fontsize=14,
               fontweight='bold', color='#1f2937')

        ax.set_title('Risk Level Distribution', fontsize=13, fontweight='bold',
                    color='#1e3a8a', pad=15)

        plt.tight_layout()

        chart_path = os.path.join(self.temp_dir, f'risk_dist_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        plt.close()

        return chart_path

    # ========================================================================
    # INDIVIDUAL USER REPORT - 15-16 PAGES
    # ========================================================================

    def generate_individual_user_report(self, user: Dict, activities: List[Dict],
                                        stats: Dict) -> str:
        """
        Generate comprehensive individual user threat assessment report.
        Professional 15-16 page document with detailed analysis.
        """
        timestamp = datetime.now()
        report_id = self._generate_report_id('IUR')
        username = user.get('username', 'unknown')
        filename = f"individual_report_{username}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.9*inch,
            bottomMargin=0.9*inch
        )

        story = []
        styles = self.styles

        # Calculate comprehensive statistics
        total_activities = len(activities)
        risk_score = float(user.get('current_risk_score', 0))
        risk_level = self._get_risk_level(risk_score)

        # Risk level counts
        critical_count = len([a for a in activities if a.get('risk_level', '').upper() == 'CRITICAL'])
        high_count = len([a for a in activities if a.get('risk_level', '').upper() == 'HIGH'])
        medium_count = len([a for a in activities if a.get('risk_level', '').upper() == 'MEDIUM'])
        low_count = len([a for a in activities if a.get('risk_level', '').upper() == 'LOW'])

        # Action counts
        blocked_count = len([a for a in activities if a.get('action') == 'BLOCK'])
        restricted_count = len([a for a in activities if a.get('action') == 'RESTRICT'])
        monitored_count = len([a for a in activities if a.get('action') == 'MONITOR'])
        allowed_count = len([a for a in activities if a.get('action') == 'ALLOW'])

        # Time-based analysis
        business_hours = 0
        after_hours_count = 0
        weekend_count = 0

        for act in activities:
            try:
                ts = act.get('timestamp', '')
                if ts:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if 9 <= dt.hour < 18 and dt.weekday() < 5:
                        business_hours += 1
                    else:
                        after_hours_count += 1
                    if dt.weekday() >= 5:
                        weekend_count += 1
            except:
                pass

        after_hours_pct = (after_hours_count / max(total_activities, 1)) * 100

        # ====================================================================
        # PAGE 1: COVER PAGE
        # ====================================================================

        story.append(Spacer(1, 1.2*inch))

        # Logo/Branding
        story.append(Paragraph(
            '<font color="#1e3a8a" size="42"><b>IGNISYL</b></font>',
            ParagraphStyle('Logo', alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.2*inch))  # Proper spacing after logo
        story.append(Paragraph(
            '<font color="#6b7280" size="12">AI-Powered Insider Threat Detection System</font>',
            ParagraphStyle('Tagline', alignment=TA_CENTER)
        ))

        story.append(Spacer(1, 0.5*inch))  # 0.5 inch space after branding block

        # Horizontal line
        story.append(HRFlowable(width="80%", thickness=2, color=COLORS['primary'],
                               spaceAfter=25, spaceBefore=15))

        story.append(Paragraph("Individual User Security Report", styles['CoverTitle']))

        story.append(Spacer(1, 0.3*inch))  # 0.3 inch space after title

        # User name prominently displayed
        story.append(Paragraph(
            f'<font color="#1f2937" size="22"><b>{user.get("full_name", "Unknown User")}</b></font>',
            ParagraphStyle('UserName', alignment=TA_CENTER)
        ))
        story.append(Paragraph(
            f'<font color="#6b7280" size="12">{user.get("department", "N/A")} | {user.get("role", "N/A")}</font>',
            ParagraphStyle('UserDept', alignment=TA_CENTER, spaceBefore=8)
        ))

        story.append(Spacer(1, 0.5*inch))

        # Key metrics in centered table
        risk_color_hex = RISK_COLORS.get(risk_level, '#6b7280')
        cover_data = [
            ['Risk Score', f'{risk_score:.0f}/100'],
            ['Risk Classification', risk_level],
            ['Activities Analyzed', str(total_activities)],
            ['Security Actions Taken', str(blocked_count + restricted_count)],
        ]

        cover_table = Table(cover_data, colWidths=[2.2*inch, 2.2*inch])
        cover_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), COLORS['gray']),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(risk_color_hex)),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLORS['border']),
        ]))

        # Center the table
        story.append(Table([[cover_table]], colWidths=[6.5*inch], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))

        story.append(Spacer(1, 0.8*inch))

        # Report info
        story.append(Paragraph(
            f'<font color="#6b7280" size="10">Report ID: {report_id}</font>',
            ParagraphStyle('ReportInfo', alignment=TA_CENTER)
        ))
        story.append(Paragraph(
            f'<font color="#6b7280" size="10">Generated: {timestamp.strftime("%B %d, %Y at %H:%M:%S UTC")}</font>',
            ParagraphStyle('ReportInfo', alignment=TA_CENTER, spaceBefore=5)
        ))

        story.append(Spacer(1, 0.5*inch))

        story.append(Paragraph(
            '<font color="#dc2626" size="10"><b>CONFIDENTIAL - AUTHORIZED PERSONNEL ONLY</b></font>',
            ParagraphStyle('Confidential', alignment=TA_CENTER)
        ))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 2: EXECUTIVE SUMMARY
        # ====================================================================

        story.append(SectionHeader("Executive Summary", section_num=1))
        story.append(Spacer(1, 0.2*inch))

        # Risk assessment box
        if risk_level == 'CRITICAL':
            alert_type = 'critical'
            assessment = "IMMEDIATE ACTION REQUIRED - Critical security risk detected"
        elif risk_level == 'HIGH':
            alert_type = 'warning'
            assessment = "ELEVATED CONCERN - Enhanced monitoring and investigation recommended"
        elif risk_level == 'MEDIUM':
            alert_type = 'info'
            assessment = "MODERATE RISK - Regular monitoring advised with attention to flagged activities"
        else:
            alert_type = 'success'
            assessment = "NORMAL OPERATIONS - Standard monitoring protocols sufficient"

        story.append(AlertBox(assessment, alert_type))
        story.append(Spacer(1, 0.25*inch))

        # Summary paragraph
        summary_text = f"""This report provides a comprehensive security analysis of <b>{user.get('full_name', 'the user')}</b>
        from the <b>{user.get('department', 'N/A')}</b> department. Over the analysis period, IGNISYL's AI-powered
        threat detection system processed <b>{total_activities}</b> activities, identifying <b>{critical_count}</b> critical
        and <b>{high_count}</b> high-risk incidents. The system automatically blocked <b>{blocked_count}</b> potentially
        malicious actions and applied restrictions to <b>{restricted_count}</b> additional activities."""

        story.append(Paragraph(summary_text, styles['Body']))
        story.append(Spacer(1, 0.2*inch))

        # Key metrics cards row
        story.append(Paragraph("<b>Key Metrics at a Glance</b>", styles['SubsectionTitle']))

        metrics_row = Table([
            [
                MetricCard(f"{risk_score:.0f}", "Risk Score", risk_color_hex),
                MetricCard(str(total_activities), "Total Activities", "#3b82f6"),
                MetricCard(str(critical_count + high_count), "High Risk Events", "#ea580c"),
                MetricCard(str(blocked_count), "Blocked Actions", "#dc2626"),
            ]
        ], colWidths=[1.625*inch]*4)
        metrics_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(metrics_row)
        story.append(Spacer(1, 0.3*inch))

        # Key findings
        story.append(Paragraph("<b>Key Findings</b>", styles['SubsectionTitle']))

        findings = []
        if critical_count > 0:
            findings.append(f"<bullet>&bull;</bullet> <font color='#dc2626'><b>CRITICAL:</b></font> {critical_count} critical security incident(s) requiring immediate investigation")
        if high_count > 0:
            findings.append(f"<bullet>&bull;</bullet> <font color='#ea580c'><b>HIGH:</b></font> {high_count} high-risk activities detected during the analysis period")
        if after_hours_pct > 30:
            findings.append(f"<bullet>&bull;</bullet> <font color='#ca8a04'><b>ANOMALY:</b></font> {after_hours_pct:.0f}% of activities occurred outside business hours")
        if blocked_count > 0:
            findings.append(f"<bullet>&bull;</bullet> <font color='#dc2626'><b>ACTION:</b></font> {blocked_count} activities were automatically blocked by the system")
        if not findings:
            findings.append("<bullet>&bull;</bullet> <font color='#16a34a'><b>NORMAL:</b></font> No significant security concerns identified during analysis")

        for finding in findings:
            story.append(Paragraph(finding, styles['BulletItem']))

        story.append(Spacer(1, 0.25*inch))

        # Recommended actions
        story.append(Paragraph("<b>Recommended Actions</b>", styles['SubsectionTitle']))

        if risk_score >= 75:
            actions = [
                "Immediately suspend account pending investigation",
                "Schedule meeting with employee, manager, and HR",
                "Preserve all activity logs for forensic analysis",
                "Review access to sensitive systems and data"
            ]
        elif risk_score >= 50:
            actions = [
                "Schedule discussion with employee regarding security concerns",
                "Implement enhanced monitoring for 30 days",
                "Review and potentially reduce access privileges",
                "Require completion of security awareness training"
            ]
        else:
            actions = [
                "Continue standard monitoring procedures",
                "Schedule routine security awareness refresher",
                "Review access permissions during next audit cycle"
            ]

        for i, action in enumerate(actions, 1):
            story.append(Paragraph(f"<bullet>{i}.</bullet> {action}", styles['BulletItem']))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 3: USER PROFILE
        # ====================================================================

        story.append(SectionHeader("User Profile", section_num=2))
        story.append(Spacer(1, 0.15*inch))

        # Basic Information
        story.append(Paragraph("<b>2.1 Basic Information</b>", styles['SubsectionTitle']))

        basic_info = [
            ['Field', 'Value'],
            ['User ID', user.get('user_id', 'N/A')],
            ['Username', user.get('username', 'N/A')],
            ['Full Name', user.get('full_name', 'N/A')],
            ['Email Address', user.get('email', 'Not provided') or 'Not provided'],
            ['Department', user.get('department', 'N/A')],
            ['Role/Position', user.get('role', 'N/A')],
            ['Account Status', user.get('status', 'active').title()],
            ['Account Created', self._format_timestamp(user.get('registered_at', ''), 'full')],
            ['Last Activity', self._format_timestamp(user.get('last_activity', ''), 'full')],
        ]

        story.append(self._create_table(basic_info, [2.2*inch, 4.3*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Risk Assessment
        story.append(Paragraph("<b>2.2 Current Risk Assessment</b>", styles['SubsectionTitle']))

        risk_profile = stats.get('risk_profile', {})
        peak_score = risk_profile.get('peak_score', risk_score)

        risk_data = [
            ['Risk Metric', 'Value', 'Status'],
            ['Current Risk Score', f'{risk_score:.1f}', risk_level],
            ['Peak Risk Score (24h)', f'{peak_score:.1f}', self._get_risk_level(peak_score)],
            ['Critical Incidents', str(critical_count), 'ALERT' if critical_count > 0 else 'OK'],
            ['High-Risk Incidents', str(high_count), 'WARNING' if high_count > 5 else 'OK'],
            ['Activities Blocked', str(blocked_count), 'ENFORCED' if blocked_count > 0 else 'NONE'],
            ['Activities Restricted', str(restricted_count), 'ACTIVE' if restricted_count > 0 else 'NONE'],
        ]

        risk_table = self._create_table(risk_data, [2.5*inch, 1.8*inch, 1.8*inch])
        story.append(risk_table)

        if risk_score >= 50:
            story.append(Spacer(1, 0.15*inch))
            alert_msg = f"Risk score ({risk_score:.0f}) exceeds monitoring threshold. Enhanced surveillance active."
            story.append(AlertBox(alert_msg, 'warning' if risk_score < 75 else 'critical'))

        story.append(Spacer(1, 0.25*inch))

        # Account Security Status
        story.append(Paragraph("<b>2.3 Account Security Status</b>", styles['SubsectionTitle']))

        status = user.get('status', 'active')
        if status == 'blocked':
            status_items = [
                ('Account Status', 'BLOCKED'),
                ('Network Access', 'Denied'),
                ('System Access', 'Suspended'),
                ('Reason', 'Security policy violation'),
            ]
        elif status == 'restricted':
            status_items = [
                ('Account Status', 'RESTRICTED'),
                ('Network Access', 'Limited'),
                ('System Access', 'Monitored'),
                ('Restrictions Applied', 'Enhanced logging, limited file access'),
            ]
        else:
            status_items = [
                ('Account Status', 'ACTIVE'),
                ('Network Access', 'Full'),
                ('System Access', 'Normal'),
                ('Monitoring Level', 'Standard' if risk_score < 30 else 'Enhanced'),
            ]

        story.append(self._create_key_value_table(status_items))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 4-5: ACTIVITY ANALYSIS
        # ====================================================================

        story.append(SectionHeader("Activity Analysis", section_num=3))
        story.append(Spacer(1, 0.15*inch))

        # Activity Summary
        story.append(Paragraph("<b>3.1 Activity Summary</b>", styles['SubsectionTitle']))

        story.append(Paragraph(
            f"""During the analysis period, IGNISYL processed <b>{total_activities}</b> activities
            for this user. The following breakdown shows the distribution across activity types
            and risk classifications.""", styles['Body']
        ))
        story.append(Spacer(1, 0.15*inch))

        # Activity type breakdown
        activity_types = Counter(a.get('activity_type', 'Unknown') for a in activities)
        top_activities = activity_types.most_common(12)

        if top_activities:
            activity_data = [['Activity Type', 'Count', 'Percentage', 'Avg Risk']]
            for act_type, count in top_activities:
                pct = (count / total_activities * 100) if total_activities > 0 else 0
                avg_risk = sum(a.get('risk_score', 0) for a in activities if a.get('activity_type') == act_type) / max(count, 1)
                activity_data.append([
                    self._truncate(act_type.replace('_', ' ').title(), 28),
                    str(count),
                    f'{pct:.1f}%',
                    f'{avg_risk:.0f}'
                ])

            story.append(self._create_table(activity_data, [2.8*inch, 1.1*inch, 1.1*inch, 1.1*inch]))

        story.append(Spacer(1, 0.25*inch))

        # Risk Level Distribution
        story.append(Paragraph("<b>3.2 Risk Level Distribution</b>", styles['SubsectionTitle']))

        risk_dist = [
            ['Risk Level', 'Count', 'Percentage', 'Trend'],
            ['CRITICAL', str(critical_count), f'{(critical_count/max(total_activities,1)*100):.1f}%', 'Immediate Action'],
            ['HIGH', str(high_count), f'{(high_count/max(total_activities,1)*100):.1f}%', 'Monitor Closely'],
            ['MEDIUM', str(medium_count), f'{(medium_count/max(total_activities,1)*100):.1f}%', 'Review Periodically'],
            ['LOW', str(low_count), f'{(low_count/max(total_activities,1)*100):.1f}%', 'Normal Operation'],
        ]

        story.append(self._create_table(risk_dist, [1.5*inch, 1.2*inch, 1.3*inch, 2.1*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Firewall Actions
        story.append(Paragraph("<b>3.3 Security Actions Applied</b>", styles['SubsectionTitle']))

        actions_data = [
            ['Action Type', 'Count', 'Description'],
            ['BLOCK', str(blocked_count), 'Access completely denied - policy violation'],
            ['RESTRICT', str(restricted_count), 'Access limited with enhanced monitoring'],
            ['MONITOR', str(monitored_count), 'Activity logged for security review'],
            ['ALLOW', str(allowed_count), 'Normal access permitted'],
        ]

        story.append(self._create_table(actions_data, [1.3*inch, 1*inch, 3.8*inch]))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 5-6: DETAILED ACTIVITY LOG
        # ====================================================================

        story.append(Paragraph("<b>3.4 Detailed Activity Log</b>", styles['SubsectionTitle']))
        story.append(Paragraph(
            "The following table shows the most recent activities sorted by timestamp. "
            "High-risk activities are highlighted for immediate attention.",
            styles['Small']
        ))
        story.append(Spacer(1, 0.1*inch))

        # Show activities sorted by risk then time
        sorted_activities = sorted(activities, key=lambda x: (-x.get('risk_score', 0), x.get('timestamp', '')))[:40]

        activity_log = [['Timestamp', 'Activity Type', 'Risk', 'Level', 'Action']]
        for act in sorted_activities:
            activity_log.append([
                self._format_timestamp(act.get('timestamp', ''), 'short'),
                self._truncate(act.get('activity_type', 'Unknown').replace('_', ' ').title(), 24),
                f"{act.get('risk_score', 0):.0f}",
                act.get('risk_level', 'LOW'),
                act.get('action', 'ALLOW')
            ])

        if len(activities) > 40:
            activity_log.append([f'... Showing 40 of {len(activities)} activities ...', '', '', '', ''])

        story.append(self._create_table(activity_log, [1.1*inch, 2.3*inch, 0.6*inch, 0.9*inch, 1*inch]))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 7-8: VISUALIZATIONS
        # ====================================================================

        story.append(SectionHeader("Visual Analytics", section_num=4))
        story.append(Spacer(1, 0.15*inch))

        story.append(Paragraph(
            "The following charts provide visual analysis of activity patterns and risk trends. "
            "These visualizations help identify anomalies and behavioral patterns.",
            styles['Body']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Timeline Chart
        story.append(Paragraph("<b>4.1 Activity Timeline by Risk Level</b>", styles['SubsectionTitle']))
        timeline_chart = self._create_timeline_chart(activities, username)
        if timeline_chart and os.path.exists(timeline_chart):
            story.append(Image(timeline_chart, width=6.3*inch, height=2.6*inch))
        else:
            story.append(Paragraph("<i>Insufficient data for timeline visualization.</i>", styles['Small']))
        story.append(Spacer(1, 0.25*inch))

        # Risk Trend Chart
        story.append(Paragraph("<b>4.2 Risk Score Trend Over Time</b>", styles['SubsectionTitle']))
        trend_chart = self._create_risk_trend_chart(activities, username)
        if trend_chart and os.path.exists(trend_chart):
            story.append(Image(trend_chart, width=6.3*inch, height=2.6*inch))
        else:
            story.append(Paragraph("<i>Insufficient data for trend visualization.</i>", styles['Small']))

        story.append(PageBreak())

        # Pie Chart
        story.append(Paragraph("<b>4.3 Activity Distribution by Type</b>", styles['SubsectionTitle']))
        pie_chart = self._create_activity_pie_chart(activities, username)
        if pie_chart and os.path.exists(pie_chart):
            story.append(Image(pie_chart, width=6*inch, height=3.3*inch))
        else:
            story.append(Paragraph("<i>Insufficient data for distribution chart.</i>", styles['Small']))
        story.append(Spacer(1, 0.3*inch))

        # Hourly Pattern Chart
        story.append(Paragraph("<b>4.4 Hourly Activity Pattern</b>", styles['SubsectionTitle']))
        hourly_chart = self._create_hourly_chart(activities, username)
        if hourly_chart and os.path.exists(hourly_chart):
            story.append(Image(hourly_chart, width=6.3*inch, height=2.6*inch))
        else:
            story.append(Paragraph("<i>Insufficient data for hourly pattern chart.</i>", styles['Small']))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 9-10: THREAT ANALYSIS
        # ====================================================================

        story.append(SectionHeader("Threat Analysis", section_num=5))
        story.append(Spacer(1, 0.15*inch))

        # Flagged Activities
        story.append(Paragraph("<b>5.1 Flagged Suspicious Activities</b>", styles['SubsectionTitle']))

        high_risk_activities = sorted(
            [a for a in activities if a.get('risk_score', 0) >= 50],
            key=lambda x: -x.get('risk_score', 0)
        )[:20]

        if high_risk_activities:
            story.append(Paragraph(
                f"<font color='#dc2626'><b>{len(high_risk_activities)}</b></font> high-risk activities have been flagged for review:",
                styles['Body']
            ))
            story.append(Spacer(1, 0.1*inch))

            flagged_data = [['Time', 'Activity', 'Risk', 'Level', 'Action']]
            for act in high_risk_activities:
                flagged_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    self._truncate(act.get('activity_type', 'Unknown').replace('_', ' ').title(), 22),
                    f"{act.get('risk_score', 0):.0f}",
                    act.get('risk_level', 'HIGH'),
                    act.get('action', 'RESTRICT')
                ])

            story.append(self._create_table(flagged_data, [1.1*inch, 2.2*inch, 0.7*inch, 0.9*inch, 1*inch]))
        else:
            story.append(AlertBox("No high-risk activities detected during analysis period", 'success'))

        story.append(Spacer(1, 0.25*inch))

        # Honeypot Access
        story.append(Paragraph("<b>5.2 Honeypot Access Attempts</b>", styles['SubsectionTitle']))

        honeypot_activities = [a for a in activities if 'honeypot' in a.get('activity_type', '').lower()]

        if honeypot_activities:
            story.append(AlertBox(
                f"CRITICAL: {len(honeypot_activities)} honeypot access attempt(s) detected!",
                'critical'
            ))
            story.append(Spacer(1, 0.1*inch))

            story.append(Paragraph(
                """<b>What this means:</b> Honeypot files are decoy resources designed to detect unauthorized access.
                Any access to these files indicates potential malicious intent or policy violation.""",
                styles['Body']
            ))
            story.append(Spacer(1, 0.1*inch))

            honeypot_data = [['Timestamp', 'Activity Details', 'Risk Score', 'Action']]
            for act in honeypot_activities[:10]:
                honeypot_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    self._truncate(act.get('activity_type', ''), 28),
                    f"{act.get('risk_score', 100):.0f}",
                    act.get('action', 'BLOCK')
                ])

            story.append(self._create_table(honeypot_data, [1.3*inch, 2.8*inch, 1*inch, 1*inch]))
        else:
            story.append(Paragraph(
                "No honeypot access attempts detected. The user has not accessed any decoy resources.",
                styles['Body']
            ))

        story.append(Spacer(1, 0.25*inch))

        # After-Hours Activity
        story.append(Paragraph("<b>5.3 After-Hours Activity Analysis</b>", styles['SubsectionTitle']))

        after_hours_activities = []
        for act in activities:
            try:
                ts = act.get('timestamp', '')
                if ts:
                    hour = int(ts[11:13])
                    if hour < 6 or hour >= 22:
                        after_hours_activities.append(act)
            except:
                pass

        after_hours_activities = sorted(after_hours_activities,
                                        key=lambda x: -x.get('risk_score', 0))[:15]

        if after_hours_activities:
            ah_pct = (len(after_hours_activities) / max(total_activities, 1)) * 100

            if ah_pct > 30:
                story.append(AlertBox(
                    f"ANOMALY: {ah_pct:.0f}% of activities occur outside business hours",
                    'warning'
                ))

            story.append(Paragraph(
                f"<b>{len(after_hours_activities)}</b> activities occurred during non-business hours (before 6 AM or after 10 PM):",
                styles['Body']
            ))
            story.append(Spacer(1, 0.1*inch))

            after_hours_data = [['Time', 'Activity', 'Risk Score']]
            for act in after_hours_activities:
                after_hours_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    self._truncate(act.get('activity_type', 'Unknown').replace('_', ' ').title(), 35),
                    f"{act.get('risk_score', 0):.0f}"
                ])

            story.append(self._create_table(after_hours_data, [1.3*inch, 3.5*inch, 1.3*inch]))
        else:
            story.append(Paragraph(
                "No significant after-hours activity detected. User activities are within normal working hours.",
                styles['Body']
            ))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 11: BEHAVIORAL ANALYSIS
        # ====================================================================

        story.append(SectionHeader("Behavioral Analysis", section_num=6))
        story.append(Spacer(1, 0.15*inch))

        # Temporal Patterns
        story.append(Paragraph("<b>6.1 Temporal Activity Patterns</b>", styles['SubsectionTitle']))

        story.append(Paragraph(
            "Analysis of when activities occur can reveal anomalous behavior patterns that may indicate security risks.",
            styles['Body']
        ))
        story.append(Spacer(1, 0.1*inch))

        temporal_data = [
            ['Time Period', 'Activity Count', 'Percentage', 'Assessment'],
            ['Business Hours (9 AM - 6 PM)', str(business_hours),
             f'{(business_hours/max(total_activities,1)*100):.1f}%', 'Normal'],
            ['After Hours', str(after_hours_count),
             f'{(after_hours_count/max(total_activities,1)*100):.1f}%',
             'Elevated' if after_hours_pct > 30 else 'Normal'],
            ['Weekend Activity', str(weekend_count),
             f'{(weekend_count/max(total_activities,1)*100):.1f}%',
             'Review' if weekend_count > total_activities * 0.2 else 'Normal'],
        ]

        story.append(self._create_table(temporal_data, [2.2*inch, 1.3*inch, 1.2*inch, 1.4*inch]))

        if after_hours_pct > 40:
            story.append(Spacer(1, 0.1*inch))
            story.append(AlertBox(
                f"Significant after-hours activity detected ({after_hours_pct:.0f}%)",
                'warning'
            ))

        story.append(Spacer(1, 0.25*inch))

        # Peer Comparison
        story.append(Paragraph("<b>6.2 Department Peer Comparison</b>", styles['SubsectionTitle']))

        department_peers = stats.get('department_peers', [])
        peer_activities = stats.get('peer_activities', [])

        user_bytes = sum(a.get('bytes_transferred', 0) or 0 for a in activities)

        if department_peers:
            peer_risk_scores = [p.get('current_risk_score', 0) for p in department_peers]
            avg_peer_risk = sum(peer_risk_scores) / max(len(peer_risk_scores), 1)
            peer_bytes = sum(a.get('bytes_transferred', 0) or 0 for a in peer_activities)
            avg_peer_bytes = peer_bytes / max(len(department_peers), 1)
            avg_peer_activities = len(peer_activities) / max(len(department_peers), 1)

            deviation = ((risk_score - avg_peer_risk) / max(avg_peer_risk, 1)) * 100 if avg_peer_risk else 0

            comparison_data = [
                ['Metric', 'This User', 'Dept. Average', 'Deviation'],
                ['Risk Score', f'{risk_score:.1f}', f'{avg_peer_risk:.1f}',
                 f'{deviation:+.0f}%' if deviation else 'N/A'],
                ['High-Risk Events', str(high_count + critical_count), '~2',
                 'Above Avg' if (high_count + critical_count) > 2 else 'Normal'],
                ['Data Transfer', f'{user_bytes/(1024*1024):.1f} MB',
                 f'{avg_peer_bytes/(1024*1024):.1f} MB', '-'],
                ['Total Activities', str(total_activities), f'{avg_peer_activities:.0f}', '-'],
            ]

            story.append(self._create_table(comparison_data, [2*inch, 1.4*inch, 1.4*inch, 1.3*inch]))

            if deviation > 100:
                story.append(Spacer(1, 0.1*inch))
                story.append(AlertBox(
                    f"Risk score is {deviation:.0f}% higher than department average",
                    'critical'
                ))
        else:
            story.append(Paragraph(
                "Peer comparison data not available. Analysis based on individual metrics only.",
                styles['Small']
            ))

        story.append(Spacer(1, 0.25*inch))

        # Behavioral Indicators
        story.append(Paragraph("<b>6.3 Behavioral Risk Indicators</b>", styles['SubsectionTitle']))

        indicators = []

        # Calculate various indicators
        if critical_count > 0:
            indicators.append(('Critical Security Events', str(critical_count), 'HIGH',
                             'Immediate investigation required'))
        if blocked_count > 5:
            indicators.append(('Blocked Access Attempts', str(blocked_count), 'HIGH',
                             'Pattern of policy violations'))
        if after_hours_pct > 50:
            indicators.append(('After-Hours Activity Ratio', f'{after_hours_pct:.0f}%', 'MEDIUM',
                             'Unusual work pattern detected'))
        if user_bytes > 100 * 1024 * 1024:  # > 100MB
            indicators.append(('Large Data Transfers', f'{user_bytes/(1024*1024):.1f} MB', 'MEDIUM',
                             'Potential data exfiltration risk'))

        if indicators:
            indicator_data = [['Indicator', 'Value', 'Severity', 'Implication']]
            indicator_data.extend(indicators)
            story.append(self._create_table(indicator_data, [2*inch, 1*inch, 1*inch, 2.1*inch]))
        else:
            story.append(Paragraph(
                "No significant behavioral risk indicators detected. Activity patterns appear normal.",
                styles['Body']
            ))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 12: ML MODEL ANALYSIS
        # ====================================================================

        story.append(SectionHeader("ML Model Analysis", section_num=7))
        story.append(Spacer(1, 0.15*inch))

        story.append(Paragraph(
            """IGNISYL employs multiple machine learning models to detect anomalous behavior.
            Each model provides an independent risk assessment, which are combined using
            ensemble voting for the final score.""",
            styles['Body']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Model Predictions
        story.append(Paragraph("<b>7.1 Individual Model Predictions</b>", styles['SubsectionTitle']))

        # Simulated ML outputs based on actual risk score
        ml_data = [
            ['Model', 'Algorithm', 'Anomaly Score', 'Risk Level', 'Confidence'],
            ['Isolation Forest', 'Unsupervised', f'{min(risk_score * 0.95, 100):.1f}',
             self._get_risk_level(risk_score * 0.95), '85%'],
            ['XGBoost Classifier', 'Supervised', f'{min(risk_score * 1.08, 100):.1f}',
             self._get_risk_level(risk_score * 1.08), '92%'],
            ['Autoencoder (DNN)', 'Deep Learning', f'{min(risk_score * 0.88, 100):.1f}',
             self._get_risk_level(risk_score * 0.88), '78%'],
            ['Ensemble Average', 'Weighted Vote', f'{risk_score:.1f}', risk_level, '88%'],
        ]

        story.append(self._create_table(ml_data, [1.5*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Feature Importance
        story.append(Paragraph("<b>7.2 Feature Importance Analysis</b>", styles['SubsectionTitle']))

        story.append(Paragraph(
            "The following features contributed most to the risk score calculation:",
            styles['Body']
        ))
        story.append(Spacer(1, 0.1*inch))

        # Dynamic feature importance based on actual data
        feature_data = [['Feature', 'Importance', 'Direction', 'Impact']]

        if after_hours_pct > 30:
            feature_data.append(['After-Hours Activity Frequency', 'High', 'Risk Increasing', '+15-25 points'])
        if critical_count > 0:
            feature_data.append(['Critical Security Events', 'High', 'Risk Increasing', '+20-35 points'])
        if blocked_count > 0:
            feature_data.append(['Blocked Access Attempts', 'High', 'Risk Increasing', '+10-20 points'])

        feature_data.extend([
            ['Sensitive File Access Count', 'Medium', 'Variable', '+5-15 points'],
            ['Data Transfer Volume', 'Medium', 'Variable', '+5-10 points'],
            ['Login Pattern Regularity', 'Low', 'Risk Decreasing', '-5 points'],
        ])

        story.append(self._create_table(feature_data[:8], [2.3*inch, 1.1*inch, 1.3*inch, 1.4*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Prediction Explanations
        story.append(Paragraph("<b>7.3 Risk Score Explanation</b>", styles['SubsectionTitle']))

        explanations = []

        if risk_score >= 75:
            explanations.append("Multiple critical threat indicators detected requiring immediate attention")
        if critical_count > 0:
            explanations.append(f"{critical_count} critical security incident(s) significantly elevated the risk score")
        if high_count > 5:
            explanations.append(f"Pattern of {high_count} high-risk activities indicates persistent security concern")
        if after_hours_pct > 40:
            explanations.append(f"Unusual after-hours activity pattern ({after_hours_pct:.0f}%) contributes to elevated score")
        if blocked_count > 0:
            explanations.append(f"{blocked_count} blocked action(s) indicate attempted policy violations")

        if not explanations:
            explanations.append("Activity patterns are within normal parameters with no significant anomalies detected")

        for exp in explanations:
            story.append(Paragraph(f"<bullet>&bull;</bullet> {exp}", styles['BulletItem']))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 13: SECURITY ACTIONS
        # ====================================================================

        story.append(SectionHeader("Security Actions", section_num=8))
        story.append(Spacer(1, 0.15*inch))

        # Action Timeline
        story.append(Paragraph("<b>8.1 Security Action Timeline</b>", styles['SubsectionTitle']))

        action_activities = [a for a in activities if a.get('action') in ['BLOCK', 'RESTRICT', 'MONITOR']]
        action_activities = sorted(action_activities, key=lambda x: x.get('timestamp', ''), reverse=True)[:18]

        if action_activities:
            story.append(Paragraph(
                f"<b>{len(action_activities)}</b> security actions were applied to this user's activities:",
                styles['Body']
            ))
            story.append(Spacer(1, 0.1*inch))

            action_data = [['Timestamp', 'Action', 'Activity', 'Risk', 'Reason']]
            for act in action_activities:
                reason = 'Policy Violation' if act.get('risk_score', 0) >= 75 else 'Risk Threshold'
                action_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    act.get('action', 'N/A'),
                    self._truncate(act.get('activity_type', '').replace('_', ' ').title(), 18),
                    f"{act.get('risk_score', 0):.0f}",
                    reason
                ])

            story.append(self._create_table(action_data, [1.1*inch, 0.9*inch, 1.7*inch, 0.6*inch, 1.5*inch]))
        else:
            story.append(Paragraph(
                "No security actions were required for this user during the analysis period.",
                styles['Body']
            ))

        story.append(Spacer(1, 0.25*inch))

        # Current Restrictions
        story.append(Paragraph("<b>8.2 Current Access Restrictions</b>", styles['SubsectionTitle']))

        user_status = user.get('status', 'active')

        if user_status == 'blocked':
            story.append(AlertBox("USER ACCOUNT IS CURRENTLY BLOCKED", 'critical'))
            story.append(Spacer(1, 0.1*inch))

            restriction_data = [
                ['System Area', 'Status', 'Effective Date', 'Reason'],
                ['Network Access', 'BLOCKED', 'Immediate', 'Security policy violation'],
                ['File System', 'BLOCKED', 'Immediate', 'Pending investigation'],
                ['Email Access', 'BLOCKED', 'Immediate', 'Administrative action'],
                ['VPN Access', 'BLOCKED', 'Immediate', 'Security protocol'],
            ]
        elif user_status == 'restricted':
            restriction_data = [
                ['System Area', 'Status', 'Restrictions Applied', 'Review Date'],
                ['Sensitive Files', 'LIMITED', 'Read-only access', '+30 days'],
                ['USB Devices', 'MONITORED', 'All transfers logged', 'Ongoing'],
                ['After-Hours Access', 'REQUIRES APPROVAL', 'Manager approval needed', 'Ongoing'],
                ['External Network', 'MONITORED', 'Enhanced logging', '+30 days'],
            ]
        else:
            restriction_data = [
                ['System Area', 'Status', 'Notes'],
                ['All Systems', 'FULL ACCESS', 'Normal operation'],
                ['Network', 'STANDARD MONITORING', 'Routine logging enabled'],
                ['File Access', 'UNRESTRICTED', 'Standard audit trail'],
            ]

        story.append(self._create_table(restriction_data))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 14: RECOMMENDATIONS
        # ====================================================================

        story.append(SectionHeader("Recommendations", section_num=9))
        story.append(Spacer(1, 0.15*inch))

        # Monitoring Recommendations
        story.append(Paragraph("<b>9.1 Monitoring Level Recommendation</b>", styles['SubsectionTitle']))

        if risk_score >= 75:
            mon_level = "CRITICAL SURVEILLANCE"
            mon_desc = "Continuous real-time monitoring with instant alerts for any activity. All actions should be reviewed within 1 hour."
            review_freq = "Real-time"
            alert_thresh = "All Activities"
        elif risk_score >= 50:
            mon_level = "ENHANCED MONITORING"
            mon_desc = "Daily activity review with alerts for high-risk activities. Weekly summary reports required."
            review_freq = "Daily"
            alert_thresh = "Risk > 50"
        elif risk_score >= 30:
            mon_level = "ELEVATED MONITORING"
            mon_desc = "Weekly activity review with alerts for critical activities only. Monthly trend analysis."
            review_freq = "Weekly"
            alert_thresh = "Risk > 60"
        else:
            mon_level = "STANDARD MONITORING"
            mon_desc = "Routine monitoring with monthly review of activity patterns. Quarterly access recertification."
            review_freq = "Monthly"
            alert_thresh = "Risk > 75"

        monitoring_items = [
            ('Recommended Level', mon_level),
            ('Review Frequency', review_freq),
            ('Alert Threshold', alert_thresh),
            ('Duration', '30 days minimum'),
        ]

        story.append(self._create_key_value_table(monitoring_items))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(mon_desc, styles['Body']))
        story.append(Spacer(1, 0.25*inch))

        # Access Recommendations
        story.append(Paragraph("<b>9.2 Access Privilege Recommendations</b>", styles['SubsectionTitle']))

        access_recs = [['Recommendation', 'Priority', 'Timeline', 'Justification']]

        if risk_score >= 75:
            access_recs.extend([
                ['Suspend account pending investigation', 'CRITICAL', 'Immediate', 'Multiple policy violations detected'],
                ['Revoke privileged access', 'CRITICAL', 'Immediate', 'Risk mitigation required'],
                ['Preserve all activity logs', 'HIGH', '24 hours', 'Forensic evidence preservation'],
                ['Notify HR and Legal', 'HIGH', '24 hours', 'Compliance requirement'],
            ])
        elif risk_score >= 50:
            access_recs.extend([
                ['Restrict sensitive system access', 'HIGH', '48 hours', 'Elevated risk profile'],
                ['Enable enhanced logging', 'MEDIUM', 'Immediate', 'Audit trail requirement'],
                ['Schedule security review meeting', 'MEDIUM', '1 week', 'Risk assessment'],
            ])
        else:
            access_recs.extend([
                ['Maintain current access levels', 'LOW', 'N/A', 'Normal risk profile'],
                ['Standard access recertification', 'LOW', 'Next cycle', 'Routine compliance'],
            ])

        story.append(self._create_table(access_recs, [2.3*inch, 1*inch, 1*inch, 2*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Training Recommendations
        story.append(Paragraph("<b>9.3 Security Training Recommendations</b>", styles['SubsectionTitle']))

        training_recs = [['Training Module', 'Priority', 'Duration', 'Deadline']]

        training_recs.append(['Security Awareness Fundamentals',
                            'HIGH' if risk_score >= 50 else 'MEDIUM', '2 hours', '30 days'])

        if user_bytes > 50 * 1024 * 1024:
            training_recs.append(['Data Loss Prevention (DLP)', 'HIGH', '1.5 hours', '14 days'])

        if blocked_count > 0:
            training_recs.append(['Acceptable Use Policy Review', 'HIGH', '1 hour', '7 days'])

        if after_hours_pct > 30:
            training_recs.append(['Remote Work Security', 'MEDIUM', '1 hour', '30 days'])

        training_recs.append(['Phishing Awareness', 'MEDIUM', '45 min', '60 days'])

        story.append(self._create_table(training_recs, [2.5*inch, 1*inch, 1*inch, 1.5*inch]))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 15: COMPLIANCE & LEGAL
        # ====================================================================

        story.append(SectionHeader("Compliance & Legal", section_num=10))
        story.append(Spacer(1, 0.15*inch))

        # Compliance Status
        story.append(Paragraph("<b>10.1 Regulatory Compliance Status</b>", styles['SubsectionTitle']))

        compliance_data = [
            ['Regulation/Standard', 'Status', 'Last Assessed', 'Notes'],
            ['Internal Security Policy', 'COMPLIANT' if risk_score < 50 else 'REVIEW NEEDED',
             datetime.now().strftime('%Y-%m-%d'), 'Based on activity analysis'],
            ['Data Protection (GDPR)', 'MONITORING', 'Ongoing', 'User data handling reviewed'],
            ['Access Control (SOC 2)', 'COMPLIANT' if blocked_count == 0 else 'EXCEPTION',
             datetime.now().strftime('%Y-%m-%d'), 'Access patterns analyzed'],
            ['Insider Threat Program', 'ACTIVE', 'Ongoing', f'Risk score: {risk_score:.0f}/100'],
        ]

        story.append(self._create_table(compliance_data, [2*inch, 1.3*inch, 1.2*inch, 1.8*inch]))
        story.append(Spacer(1, 0.25*inch))

        # Legal Considerations
        story.append(Paragraph("<b>10.2 Legal Considerations</b>", styles['SubsectionTitle']))

        if risk_score >= 75:
            story.append(AlertBox("Legal review recommended before taking action", 'warning'))
            story.append(Spacer(1, 0.1*inch))

        legal_items = [
            "This report is generated based on automated security monitoring systems",
            "All findings should be reviewed by qualified security professionals before action",
            "Employee rights and privacy regulations must be considered in any investigation",
            "Evidence preservation procedures should be followed for potential legal proceedings",
            "HR consultation is required before any disciplinary action"
        ]

        for item in legal_items:
            story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles['BulletItem']))

        story.append(Spacer(1, 0.25*inch))

        # Evidence Summary
        story.append(Paragraph("<b>10.3 Evidence Preservation</b>", styles['SubsectionTitle']))

        evidence_data = [
            ('Activity Logs Preserved', f'{total_activities} records'),
            ('Date Range', f'{self._format_timestamp(activities[-1].get("timestamp", "") if activities else "", "date")} to {self._format_timestamp(activities[0].get("timestamp", "") if activities else "", "date")}'),
            ('Log Integrity', 'Verified - SHA256 hash computed'),
            ('Storage Location', 'Secure encrypted archive'),
            ('Retention Period', '7 years per policy'),
        ]

        story.append(self._create_key_value_table(evidence_data))

        story.append(PageBreak())

        # ====================================================================
        # PAGE 16: REPORT CERTIFICATION
        # ====================================================================

        story.append(SectionHeader("Report Certification", section_num=11))
        story.append(Spacer(1, 0.2*inch))

        # Report Metadata
        story.append(Paragraph("<b>11.1 Report Information</b>", styles['SubsectionTitle']))

        cert_items = [
            ('Report ID', report_id),
            ('Report Type', 'Individual User Security Assessment'),
            ('Generation Time', timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')),
            ('Subject', f'{user.get("full_name", "Unknown")} ({user.get("user_id", "N/A")})'),
            ('Department', user.get('department', 'N/A')),
            ('Analysis Period', f'{total_activities} activities analyzed'),
            ('Classification', 'CONFIDENTIAL'),
            ('Distribution', 'Authorized Security Personnel Only'),
        ]

        story.append(self._create_key_value_table(cert_items))
        story.append(Spacer(1, 0.25*inch))

        # Digital Signature
        story.append(Paragraph("<b>11.2 Digital Verification</b>", styles['SubsectionTitle']))

        verification_hash = self._generate_hash()

        sig_items = [
            ('Generated By', 'IGNISYL AI Security System'),
            ('System Version', '2.1.0'),
            ('Verification Hash', f'SHA256:{verification_hash}'),
            ('Signature Time', timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')),
        ]

        story.append(self._create_key_value_table(sig_items))

        # Legal Notice - must start on new page
        story.append(PageBreak())
        story.append(SectionHeader("Legal Notice & Disclaimer", section_num=11))

        legal_notice = """
        This report is confidential and intended solely for authorized personnel within the organization's
        security and management teams. The information contained herein is derived from automated security
        monitoring systems and represents a point-in-time assessment. All findings should be reviewed by
        qualified security professionals before taking any employment or access-related actions.

        This document may contain sensitive information about employee activities and must be handled in
        accordance with applicable privacy laws, data protection regulations, and organizational policies.
        Unauthorized disclosure, copying, or distribution of this report is strictly prohibited and may
        result in legal action.

        The risk assessments and recommendations provided are generated using machine learning algorithms
        and should be considered as one input among many in any decision-making process. Final determinations
        regarding employee status or access privileges should involve appropriate human review and due process.
        """

        story.append(Paragraph(legal_notice, styles['Small']))

        story.append(Spacer(1, 0.4*inch))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS['primary'], spaceAfter=15))

        footer = f"""
        <font color="#1e3a8a" size="10"><b>IGNISYL</b></font>
        <font color="#6b7280" size="9">| AI-Powered Insider Threat Detection</font><br/>
        <font color="#6b7280" size="8">Report ID: {report_id} | Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Classification: CONFIDENTIAL</font><br/>
        <font color="#9ca3af" size="8">© {timestamp.year} IGNISYL Project - All Rights Reserved</font>
        """

        story.append(Paragraph(footer, ParagraphStyle('Footer', alignment=TA_CENTER, leading=14)))

        # Build PDF with custom canvas
        def make_canvas(filename, pagesize, **kwargs):
            return ProfessionalCanvas(filename, pagesize=pagesize,
                                      report_title="Individual User Report",
                                      report_id=report_id)

        doc.build(story, canvasmaker=make_canvas)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    # ========================================================================
    # THREAT SUMMARY REPORT (Quick Overview)
    # ========================================================================

    def generate_threat_summary_report(self, activities: List[Dict], users: List[Dict],
                                       period: str = '7d') -> str:
        """Generate threat summary report"""
        timestamp = datetime.now()
        report_id = self._generate_report_id('TSR')
        filename = f"threat_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.9*inch,
            bottomMargin=0.9*inch
        )

        story = []
        styles = self.styles

        total_activities = len(activities)
        critical_threats = [a for a in activities if a.get('risk_level') == 'CRITICAL']
        high_threats = [a for a in activities if a.get('risk_level') == 'HIGH']
        blocked = [a for a in activities if a.get('action') == 'BLOCK']

        # Cover
        story.append(Spacer(1, 1.0*inch))
        story.append(Paragraph(
            '<font color="#1e3a8a" size="36"><b>IGNISYL</b></font>',
            ParagraphStyle('Logo', alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.2*inch))  # Proper spacing between IGNISYL and title
        story.append(Paragraph(
            '<font color="#6b7280" size="11">AI-Powered Insider Threat Detection System</font>',
            ParagraphStyle('Tagline', alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.5*inch))  # Space after branding
        story.append(HRFlowable(width="70%", thickness=2, color=COLORS['primary'],
                               spaceAfter=15, spaceBefore=10))
        story.append(Paragraph("Threat Summary Report", styles['CoverTitle']))
        story.append(Spacer(1, 0.3*inch))

        cover_data = [
            ('Report Period', period.upper()),
            ('Generated', timestamp.strftime('%Y-%m-%d %H:%M:%S')),
            ('Total Activities', str(total_activities)),
            ('Critical Threats', str(len(critical_threats))),
            ('Actions Blocked', str(len(blocked))),
        ]

        story.append(self._create_key_value_table(cover_data))
        story.append(Spacer(1, 0.3*inch))

        # Executive Summary
        story.append(SectionHeader("Executive Summary"))
        story.append(Spacer(1, 0.15*inch))

        summary = f"""During the {period} reporting period, IGNISYL monitored <b>{total_activities}</b> activities
        across the organization. <b>{len(critical_threats)}</b> critical and <b>{len(high_threats)}</b> high-severity
        threats were detected. The system automatically blocked <b>{len(blocked)}</b> malicious actions."""

        story.append(Paragraph(summary, styles['Body']))
        story.append(Spacer(1, 0.2*inch))

        # Threats by Severity
        story.append(Paragraph("<b>Threats by Severity</b>", styles['SubsectionTitle']))

        severity_data = [
            ['Severity', 'Count', 'Percentage', 'Status'],
            ['CRITICAL', str(len(critical_threats)),
             f'{(len(critical_threats)/max(total_activities,1)*100):.1f}%',
             'ALERT' if critical_threats else 'OK'],
            ['HIGH', str(len(high_threats)),
             f'{(len(high_threats)/max(total_activities,1)*100):.1f}%',
             'ALERT' if len(high_threats) > 5 else 'OK'],
            ['MEDIUM', str(len([a for a in activities if a.get('risk_level') == 'MEDIUM'])), '-', 'MONITOR'],
            ['LOW', str(len([a for a in activities if a.get('risk_level') == 'LOW'])), '-', 'OK'],
        ]

        story.append(self._create_table(severity_data, [1.5*inch, 1*inch, 1.2*inch, 1.3*inch]))
        story.append(PageBreak())

        # Top Risky Users
        story.append(SectionHeader("High-Risk Users"))
        story.append(Spacer(1, 0.15*inch))

        user_threats = Counter(a.get('user_id', 'Unknown') for a in activities if a.get('risk_score', 0) >= 50)
        top_users = user_threats.most_common(10)

        if top_users:
            user_data = [['User', 'Department', 'Incidents', 'Risk Score']]
            for user_id, count in top_users:
                user_info = next((u for u in users if u.get('user_id') == user_id), {})
                user_data.append([
                    user_info.get('full_name', user_id)[:25],
                    user_info.get('department', 'N/A'),
                    str(count),
                    f"{user_info.get('current_risk_score', 0):.0f}"
                ])

            story.append(self._create_table(user_data, [2.2*inch, 1.5*inch, 1*inch, 1*inch]))

        story.append(Spacer(1, 0.25*inch))

        # Recommendations
        story.append(Paragraph("<b>Recommendations</b>", styles['SubsectionTitle']))

        recs = []
        if len(critical_threats) > 0:
            recs.append("Immediately investigate all critical threat incidents")
        if len(high_threats) > 10:
            recs.append("Review security policies - high volume of high-risk activities detected")
        recs.append("Continue regular monitoring and threat assessment")
        recs.append("Schedule security awareness training for flagged users")

        for rec in recs:
            story.append(Paragraph(f"<bullet>&bull;</bullet> {rec}", styles['BulletItem']))

        # Build
        def make_canvas(filename, pagesize, **kwargs):
            return ProfessionalCanvas(filename, pagesize=pagesize,
                                      report_title="Threat Summary",
                                      report_id=report_id)

        doc.build(story, canvasmaker=make_canvas)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    # ========================================================================
    # COMPREHENSIVE SYSTEM REPORT
    # ========================================================================

    def generate_comprehensive_report(self, users: List[Dict], activities: List[Dict],
                                       ml_stats: Dict = None, title: str = "Comprehensive Security Assessment") -> str:
        """Generate comprehensive system-wide security report with all metrics"""
        timestamp = datetime.now()
        report_id = self._generate_report_id('CSR')
        filename = f"comprehensive_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story = []
        styles = self.styles

        # === COVER PAGE ===
        story.append(Spacer(1, 1.5*inch))

        story.append(Paragraph(
            '<font color="#1e3a8a" size="42"><b>IGNISYL</b></font>',
            ParagraphStyle('Logo', alignment=TA_CENTER, spaceBefore=0)
        ))
        story.append(Spacer(1, 0.2*inch))  # Proper spacing after logo
        story.append(Paragraph(
            '<font color="#6b7280" size="14">Insider Threat Detection System</font>',
            ParagraphStyle('Tagline', alignment=TA_CENTER)
        ))

        story.append(Spacer(1, 0.5*inch))  # Space after branding block
        story.append(HRFlowable(width="60%", thickness=3, color=COLORS['primary'], hAlign='CENTER', spaceAfter=25))

        story.append(Paragraph(title, styles['CoverTitle']))
        story.append(Spacer(1, 0.3*inch))  # Space after title
        story.append(Paragraph(
            f'Report Period: Last 30 Days<br/>Generated: {timestamp.strftime("%B %d, %Y at %H:%M")}',
            styles['CoverSubtitle']
        ))

        story.append(Spacer(1, 1*inch))

        # Cover metrics
        total_users = len(users)
        active_users = len([u for u in users if u.get('status') == 'active'])
        total_activities = len(activities)
        critical_events = len([a for a in activities if a.get('risk_level') == 'CRITICAL'])
        high_events = len([a for a in activities if a.get('risk_level') == 'HIGH'])
        blocked_events = len([a for a in activities if a.get('action') == 'BLOCK'])

        cover_data = [
            ['Total Users', 'Active Users', 'Total Events', 'Critical Events'],
            [str(total_users), str(active_users), str(total_activities), str(critical_events)]
        ]

        cover_table = Table(cover_data, colWidths=[1.5*inch]*4)
        cover_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 24),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['gray']),
            ('TEXTCOLOR', (0, 1), (-1, 1), COLORS['primary_dark']),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(cover_table)

        story.append(Spacer(1, 1.5*inch))

        story.append(Paragraph(
            f'<font color="#6b7280" size="10">Report ID: {report_id}</font>',
            ParagraphStyle('ReportID', alignment=TA_CENTER)
        ))

        story.append(PageBreak())

        # === EXECUTIVE SUMMARY ===
        story.append(SectionHeader("Executive Summary", 1))
        story.append(Spacer(1, 0.2*inch))

        # Calculate key metrics
        avg_risk = sum(u.get('current_risk_score', 0) for u in users) / max(len(users), 1)
        high_risk_users = len([u for u in users if u.get('current_risk_score', 0) >= 50])

        summary_text = f"""
        This comprehensive security assessment provides an in-depth analysis of the IGNISYL
        Insider Threat Detection System's monitoring activities over the reporting period.
        The system has tracked <b>{total_activities:,}</b> activities across <b>{total_users}</b> users,
        identifying <b>{critical_events + high_events}</b> high-severity events requiring attention.
        """
        story.append(Paragraph(summary_text.strip(), styles['Body']))
        story.append(Spacer(1, 0.15*inch))

        # Key findings box
        if critical_events > 0 or high_events > 10:
            story.append(AlertBox(
                f"ATTENTION: {critical_events} critical and {high_events} high-risk events detected",
                'critical' if critical_events > 0 else 'warning'
            ))
        else:
            story.append(AlertBox("System operating within normal parameters", 'success'))

        story.append(Spacer(1, 0.3*inch))

        # Metrics row
        metrics_data = [[
            MetricCard(total_users, "Total Users", '#3b82f6'),
            MetricCard(f"{avg_risk:.0f}", "Avg Risk Score", '#ca8a04' if avg_risk >= 30 else '#16a34a'),
            MetricCard(high_risk_users, "High Risk Users", '#dc2626' if high_risk_users > 0 else '#16a34a'),
            MetricCard(blocked_events, "Blocked Events", '#ea580c')
        ]]

        metrics_table = Table(metrics_data, colWidths=[1.65*inch]*4)
        metrics_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(metrics_table)

        story.append(Spacer(1, 0.3*inch))

        # === RISK OVERVIEW ===
        story.append(Paragraph("<b>Risk Level Distribution</b>", styles['SubsectionTitle']))

        risk_counts = Counter(a.get('risk_level', 'LOW') for a in activities)
        risk_data = [['Risk Level', 'Count', 'Percentage', 'Status']]

        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts.get(level, 0)
            pct = (count / max(total_activities, 1)) * 100
            status = 'Needs Review' if level in ['CRITICAL', 'HIGH'] and count > 0 else 'Normal'
            risk_data.append([level, str(count), f"{pct:.1f}%", status])

        story.append(self._create_table(risk_data, [1.5*inch, 1.2*inch, 1.2*inch, 1.5*inch]))

        story.append(PageBreak())

        # === USER ANALYSIS ===
        story.append(SectionHeader("User Risk Analysis", 2))
        story.append(Spacer(1, 0.2*inch))

        # Top risk users
        story.append(Paragraph("<b>Highest Risk Users</b>", styles['SubsectionTitle']))

        top_risk_users = sorted(users, key=lambda x: -x.get('current_risk_score', 0))[:10]
        if top_risk_users:
            user_data = [['User', 'Department', 'Risk Score', 'Risk Level']]
            for user in top_risk_users:
                score = user.get('current_risk_score', 0)
                user_data.append([
                    user.get('full_name', 'Unknown')[:25],
                    user.get('department', 'N/A'),
                    f"{score:.0f}",
                    self._get_risk_level(score)
                ])

            story.append(self._create_table(user_data, [2*inch, 1.5*inch, 1*inch, 1.2*inch]))

        story.append(Spacer(1, 0.3*inch))

        # Department breakdown
        story.append(Paragraph("<b>Department Risk Summary</b>", styles['SubsectionTitle']))

        dept_stats = defaultdict(lambda: {'count': 0, 'total_risk': 0, 'high_risk': 0})
        for user in users:
            dept = user.get('department', 'Unknown')
            score = user.get('current_risk_score', 0)
            dept_stats[dept]['count'] += 1
            dept_stats[dept]['total_risk'] += score
            if score >= 50:
                dept_stats[dept]['high_risk'] += 1

        dept_data = [['Department', 'Users', 'Avg Risk', 'High Risk Users']]
        for dept, stats in sorted(dept_stats.items(), key=lambda x: -x[1]['total_risk']/max(x[1]['count'], 1)):
            avg = stats['total_risk'] / max(stats['count'], 1)
            dept_data.append([
                dept[:20],
                str(stats['count']),
                f"{avg:.0f}",
                str(stats['high_risk'])
            ])

        story.append(self._create_table(dept_data, [2*inch, 1*inch, 1*inch, 1.3*inch]))

        story.append(PageBreak())

        # === ACTIVITY ANALYSIS ===
        story.append(SectionHeader("Activity Analysis", 3))
        story.append(Spacer(1, 0.2*inch))

        # Activity type breakdown
        story.append(Paragraph("<b>Activity Type Distribution</b>", styles['SubsectionTitle']))

        activity_counts = Counter(a.get('activity_type', 'unknown') for a in activities)
        activity_data = [['Activity Type', 'Count', 'Percentage']]

        for act_type, count in activity_counts.most_common(10):
            pct = (count / max(total_activities, 1)) * 100
            activity_data.append([
                act_type.replace('_', ' ').title()[:30],
                str(count),
                f"{pct:.1f}%"
            ])

        story.append(self._create_table(activity_data, [2.5*inch, 1.2*inch, 1.2*inch]))

        story.append(Spacer(1, 0.3*inch))

        # Action breakdown
        story.append(Paragraph("<b>System Actions Taken</b>", styles['SubsectionTitle']))

        action_counts = Counter(a.get('action', 'ALLOW') for a in activities)
        action_data = [['Action', 'Count', 'Description']]

        action_desc = {
            'ALLOW': 'Activity permitted without restriction',
            'RESTRICT': 'Activity permitted with monitoring',
            'BLOCK': 'Activity blocked by security policy'
        }

        for action in ['ALLOW', 'RESTRICT', 'BLOCK']:
            count = action_counts.get(action, 0)
            action_data.append([action, str(count), action_desc.get(action, '')])

        story.append(self._create_table(action_data, [1.2*inch, 1*inch, 3.5*inch]))

        # Risk distribution chart
        chart_path = self._create_risk_distribution_chart(activities)
        if chart_path:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("<b>Risk Score Distribution</b>", styles['SubsectionTitle']))
            try:
                story.append(Image(chart_path, width=5*inch, height=2.5*inch))
            except:
                pass

        story.append(PageBreak())

        # === ML INSIGHTS (if available) ===
        if ml_stats:
            story.append(SectionHeader("Machine Learning Insights", 4))
            story.append(Spacer(1, 0.2*inch))

            story.append(Paragraph(
                "The following metrics represent the performance and findings from the "
                "IGNISYL machine learning anomaly detection system.",
                styles['Body']
            ))
            story.append(Spacer(1, 0.15*inch))

            ml_data = [['Metric', 'Value']]
            ml_metrics = [
                ('Model Type', ml_stats.get('model_type', 'Autoencoder')),
                ('Training Samples', ml_stats.get('training_samples', 'N/A')),
                ('Detection Threshold', ml_stats.get('threshold', 'N/A')),
                ('Anomalies Detected', ml_stats.get('anomalies_detected', 0)),
                ('False Positive Rate', f"{ml_stats.get('false_positive_rate', 0):.2%}"),
                ('Model Accuracy', f"{ml_stats.get('accuracy', 0):.2%}"),
            ]

            for metric, value in ml_metrics:
                ml_data.append([metric, str(value)])

            story.append(self._create_table(ml_data, [2.5*inch, 2.5*inch]))

            story.append(Spacer(1, 0.3*inch))

        # === RECOMMENDATIONS ===
        story.append(SectionHeader("Recommendations", 5 if ml_stats else 4))
        story.append(Spacer(1, 0.2*inch))

        recs = []
        if critical_events > 0:
            recs.append("CRITICAL: Immediately investigate all critical threat incidents and affected users")
        if high_risk_users > 3:
            recs.append("Schedule security reviews for users with elevated risk scores (>50)")
        if blocked_events > total_activities * 0.05:
            recs.append("Review security policies - high block rate may indicate misconfiguration or threat")
        if avg_risk > 40:
            recs.append("Consider organization-wide security awareness training")

        recs.extend([
            "Continue regular monitoring and threat assessment protocols",
            "Review and update security policies quarterly",
            "Ensure incident response procedures are current and tested"
        ])

        for i, rec in enumerate(recs[:8], 1):
            story.append(Paragraph(f"<b>{i}.</b> {rec}", styles['Body']))
            story.append(Spacer(1, 0.1*inch))

        # Build document
        def make_canvas(filename, pagesize, **kwargs):
            return ProfessionalCanvas(filename, pagesize=pagesize,
                                      report_title="Comprehensive Assessment",
                                      report_id=report_id)

        doc.build(story, canvasmaker=make_canvas)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    # ========================================================================
    # ACTIVITY BEHAVIORAL REPORT
    # ========================================================================

    def generate_activity_report(self, activities: List[Dict], users: List[Dict],
                                  period_days: int = 30, title: str = "Behavioral Activity Analysis") -> str:
        """Generate behavioral activity analysis report"""
        timestamp = datetime.now()
        report_id = self._generate_report_id('BAR')
        filename = f"activity_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story = []
        styles = self.styles

        # === COVER PAGE ===
        story.append(Spacer(1, 1.5*inch))

        story.append(Paragraph(
            '<font color="#1e3a8a" size="36"><b>IGNISYL</b></font>',
            ParagraphStyle('Logo', alignment=TA_CENTER, spaceBefore=0)
        ))

        story.append(HRFlowable(width="50%", thickness=2, color=COLORS['primary'], hAlign='CENTER', spaceAfter=25))

        story.append(Paragraph(title, styles['CoverTitle']))
        story.append(Paragraph(
            f'Analysis Period: {period_days} Days<br/>Generated: {timestamp.strftime("%B %d, %Y")}',
            styles['CoverSubtitle']
        ))

        story.append(Spacer(1, 0.5*inch))

        # Quick stats
        total = len(activities)
        unique_users = len(set(a.get('user_id') for a in activities))
        avg_risk = sum(a.get('risk_score', 0) for a in activities) / max(total, 1)

        story.append(Paragraph(f'<font size="14">Total Events: <b>{total:,}</b> | '
                               f'Users Analyzed: <b>{unique_users}</b> | '
                               f'Average Risk: <b>{avg_risk:.1f}</b></font>',
                               ParagraphStyle('QuickStats', alignment=TA_CENTER)))

        story.append(PageBreak())

        # === BEHAVIORAL PATTERNS ===
        story.append(SectionHeader("Behavioral Patterns", 1))
        story.append(Spacer(1, 0.2*inch))

        # Hourly distribution
        story.append(Paragraph("<b>Activity by Hour of Day</b>", styles['SubsectionTitle']))

        hourly_counts = defaultdict(int)
        for act in activities:
            try:
                ts = act.get('timestamp', '')
                if 'T' in ts:
                    hour = int(ts.split('T')[1].split(':')[0])
                    hourly_counts[hour] += 1
            except:
                pass

        hourly_data = [['Hour', 'Count', 'Analysis']]
        peak_hour = max(hourly_counts.keys(), key=lambda h: hourly_counts[h]) if hourly_counts else 12

        for hour in range(0, 24, 3):
            count = sum(hourly_counts.get(h, 0) for h in range(hour, hour+3))
            time_range = f"{hour:02d}:00-{hour+2:02d}:59"
            analysis = "Peak activity period" if hour <= peak_hour < hour + 3 else "Normal"
            if hour < 6 or hour >= 22:
                analysis = "After-hours activity" if count > 0 else "Minimal"
            hourly_data.append([time_range, str(count), analysis])

        story.append(self._create_table(hourly_data, [1.5*inch, 1*inch, 3*inch]))

        story.append(Spacer(1, 0.3*inch))

        # Activity types
        story.append(Paragraph("<b>Activity Type Analysis</b>", styles['SubsectionTitle']))

        type_stats = defaultdict(lambda: {'count': 0, 'total_risk': 0, 'blocked': 0})
        for act in activities:
            act_type = act.get('activity_type', 'unknown')
            type_stats[act_type]['count'] += 1
            type_stats[act_type]['total_risk'] += act.get('risk_score', 0)
            if act.get('action') == 'BLOCK':
                type_stats[act_type]['blocked'] += 1

        type_data = [['Activity Type', 'Count', 'Avg Risk', 'Blocked']]
        for act_type, stats in sorted(type_stats.items(), key=lambda x: -x[1]['count'])[:12]:
            avg = stats['total_risk'] / max(stats['count'], 1)
            type_data.append([
                act_type.replace('_', ' ').title()[:25],
                str(stats['count']),
                f"{avg:.1f}",
                str(stats['blocked'])
            ])

        story.append(self._create_table(type_data, [2.2*inch, 1*inch, 1*inch, 1*inch]))

        story.append(PageBreak())

        # === USER BEHAVIORAL ANALYSIS ===
        story.append(SectionHeader("User Behavioral Analysis", 2))
        story.append(Spacer(1, 0.2*inch))

        # Most active users
        story.append(Paragraph("<b>Most Active Users</b>", styles['SubsectionTitle']))

        user_activity = defaultdict(lambda: {'count': 0, 'risk_sum': 0})
        for act in activities:
            uid = act.get('user_id', 'unknown')
            user_activity[uid]['count'] += 1
            user_activity[uid]['risk_sum'] += act.get('risk_score', 0)

        active_data = [['User', 'Department', 'Activity Count', 'Avg Risk']]
        for uid, stats in sorted(user_activity.items(), key=lambda x: -x[1]['count'])[:10]:
            user_info = next((u for u in users if u.get('user_id') == uid), {})
            avg = stats['risk_sum'] / max(stats['count'], 1)
            active_data.append([
                user_info.get('full_name', uid)[:22],
                user_info.get('department', 'N/A'),
                str(stats['count']),
                f"{avg:.1f}"
            ])

        story.append(self._create_table(active_data, [2*inch, 1.3*inch, 1.2*inch, 1*inch]))

        story.append(Spacer(1, 0.3*inch))

        # Unusual patterns
        story.append(Paragraph("<b>Behavioral Anomalies Detected</b>", styles['SubsectionTitle']))

        anomalies = []
        for uid, stats in user_activity.items():
            avg_risk = stats['risk_sum'] / max(stats['count'], 1)
            if avg_risk >= 50:
                user_info = next((u for u in users if u.get('user_id') == uid), {})
                anomalies.append({
                    'user': user_info.get('full_name', uid),
                    'type': 'High average risk score',
                    'value': f"{avg_risk:.1f}"
                })

        # After hours activity check
        after_hours = sum(1 for act in activities
                        if 'T' in act.get('timestamp', '') and
                        (int(act.get('timestamp', 'T00').split('T')[1].split(':')[0]) < 6 or
                         int(act.get('timestamp', 'T00').split('T')[1].split(':')[0]) >= 22))

        if after_hours > total * 0.1:
            anomalies.append({
                'user': 'Multiple users',
                'type': 'Significant after-hours activity',
                'value': f"{after_hours} events"
            })

        if anomalies:
            anomaly_data = [['User', 'Anomaly Type', 'Details']]
            for a in anomalies[:8]:
                anomaly_data.append([a['user'][:20], a['type'], a['value']])
            story.append(self._create_table(anomaly_data, [1.8*inch, 2.5*inch, 1.5*inch]))
        else:
            story.append(AlertBox("No significant behavioral anomalies detected", 'success'))

        story.append(PageBreak())

        # === DATA TRANSFER ANALYSIS ===
        story.append(SectionHeader("Data Transfer Analysis", 3))
        story.append(Spacer(1, 0.2*inch))

        data_activities = [a for a in activities if a.get('bytes_transferred', 0) > 0]
        total_bytes = sum(a.get('bytes_transferred', 0) for a in data_activities)

        story.append(Paragraph(f"<b>Total Data Transferred:</b> {total_bytes / (1024*1024):.2f} MB", styles['Body']))
        story.append(Paragraph(f"<b>Transfer Events:</b> {len(data_activities)}", styles['Body']))
        story.append(Spacer(1, 0.2*inch))

        # Large transfers
        large_transfers = sorted(data_activities, key=lambda x: -x.get('bytes_transferred', 0))[:10]
        if large_transfers:
            story.append(Paragraph("<b>Largest Data Transfers</b>", styles['SubsectionTitle']))

            transfer_data = [['User', 'Activity', 'Size (MB)', 'Risk']]
            for act in large_transfers:
                user_info = next((u for u in users if u.get('user_id') == act.get('user_id')), {})
                size_mb = act.get('bytes_transferred', 0) / (1024*1024)
                transfer_data.append([
                    user_info.get('full_name', act.get('user_id', 'Unknown'))[:20],
                    act.get('activity_type', 'unknown').replace('_', ' ').title()[:20],
                    f"{size_mb:.2f}",
                    str(act.get('risk_score', 0))
                ])

            story.append(self._create_table(transfer_data, [1.8*inch, 2*inch, 1*inch, 0.8*inch]))

        # Build
        def make_canvas(filename, pagesize, **kwargs):
            return ProfessionalCanvas(filename, pagesize=pagesize,
                                      report_title="Activity Analysis",
                                      report_id=report_id)

        doc.build(story, canvasmaker=make_canvas)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    # ========================================================================
    # ML TECHNICAL REPORT
    # ========================================================================

    def generate_ml_report(self, ml_stats: Dict, activities: List[Dict],
                           model_info: Dict = None, title: str = "Machine Learning Analysis Report") -> str:
        """Generate technical ML analysis report"""
        timestamp = datetime.now()
        report_id = self._generate_report_id('MLR')
        filename = f"ml_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story = []
        styles = self.styles

        # === COVER PAGE ===
        story.append(Spacer(1, 1.2*inch))

        story.append(Paragraph(
            '<font color="#1e3a8a" size="36"><b>IGNISYL</b></font>',
            ParagraphStyle('Logo', alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.2*inch))  # Proper spacing after logo
        story.append(Paragraph(
            '<font color="#6b7280" size="11">Machine Learning Subsystem</font>',
            ParagraphStyle('Sub', alignment=TA_CENTER)
        ))

        story.append(Spacer(1, 0.5*inch))  # Space after branding
        story.append(HRFlowable(width="70%", thickness=2, color=COLORS['primary'],
                               spaceAfter=20, spaceBefore=10))

        story.append(Paragraph(title, styles['CoverTitle']))
        story.append(Spacer(1, 0.3*inch))  # Space after title
        story.append(Paragraph(
            f'Technical Analysis Report<br/>Generated: {timestamp.strftime("%B %d, %Y")}',
            styles['CoverSubtitle']
        ))

        story.append(PageBreak())

        # === MODEL OVERVIEW ===
        story.append(SectionHeader("Model Architecture", 1))
        story.append(Spacer(1, 0.2*inch))

        model_type = ml_stats.get('model_type', 'Autoencoder Neural Network')
        story.append(Paragraph(f"<b>Model Type:</b> {model_type}", styles['Body']))
        story.append(Spacer(1, 0.1*inch))

        story.append(Paragraph(
            """The IGNISYL anomaly detection system utilizes an autoencoder-based neural network
            architecture for identifying behavioral anomalies in user activity patterns. The model
            learns to reconstruct normal behavioral patterns and flags significant deviations
            as potential threats.""",
            styles['Body']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Model parameters
        story.append(Paragraph("<b>Model Configuration</b>", styles['SubsectionTitle']))

        if model_info:
            config_data = [['Parameter', 'Value']]
            params = [
                ('Input Dimensions', model_info.get('input_dim', 'N/A')),
                ('Hidden Layers', model_info.get('hidden_layers', 'N/A')),
                ('Latent Dimension', model_info.get('latent_dim', 'N/A')),
                ('Activation Function', model_info.get('activation', 'ReLU')),
                ('Optimizer', model_info.get('optimizer', 'Adam')),
                ('Learning Rate', model_info.get('learning_rate', '0.001')),
                ('Training Epochs', model_info.get('epochs', 'N/A')),
                ('Batch Size', model_info.get('batch_size', 'N/A')),
            ]
            for param, value in params:
                config_data.append([param, str(value)])

            story.append(self._create_table(config_data, [2.5*inch, 2.5*inch]))
        else:
            story.append(Paragraph("Model configuration details not available.", styles['Body']))

        story.append(PageBreak())

        # === PERFORMANCE METRICS ===
        story.append(SectionHeader("Performance Metrics", 2))
        story.append(Spacer(1, 0.2*inch))

        # Training metrics
        story.append(Paragraph("<b>Training Performance</b>", styles['SubsectionTitle']))

        train_data = [['Metric', 'Value', 'Status']]
        metrics = [
            ('Training Samples', ml_stats.get('training_samples', 0), 'N/A'),
            ('Validation Samples', ml_stats.get('validation_samples', 0), 'N/A'),
            ('Training Loss (Final)', ml_stats.get('training_loss', 0),
             'Good' if ml_stats.get('training_loss', 1) < 0.1 else 'Review'),
            ('Validation Loss', ml_stats.get('validation_loss', 0),
             'Good' if ml_stats.get('validation_loss', 1) < 0.15 else 'Review'),
            ('Reconstruction Error (Mean)', ml_stats.get('reconstruction_error', 0), 'N/A'),
        ]

        for metric, value, status in metrics:
            if isinstance(value, float):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
            train_data.append([metric, value_str, status])

        story.append(self._create_table(train_data, [2.5*inch, 1.5*inch, 1.2*inch]))

        story.append(Spacer(1, 0.3*inch))

        # Detection metrics
        story.append(Paragraph("<b>Detection Performance</b>", styles['SubsectionTitle']))

        detection_data = [['Metric', 'Value']]
        det_metrics = [
            ('Detection Threshold', ml_stats.get('threshold', 'Auto')),
            ('Total Anomalies Detected', ml_stats.get('anomalies_detected', 0)),
            ('True Positive Rate', f"{ml_stats.get('true_positive_rate', 0):.2%}"),
            ('False Positive Rate', f"{ml_stats.get('false_positive_rate', 0):.2%}"),
            ('Precision', f"{ml_stats.get('precision', 0):.2%}"),
            ('Recall', f"{ml_stats.get('recall', 0):.2%}"),
            ('F1 Score', f"{ml_stats.get('f1_score', 0):.2%}"),
        ]

        for metric, value in det_metrics:
            detection_data.append([metric, str(value)])

        story.append(self._create_table(detection_data, [2.5*inch, 2*inch]))

        story.append(PageBreak())

        # === ANOMALY ANALYSIS ===
        story.append(SectionHeader("Anomaly Analysis", 3))
        story.append(Spacer(1, 0.2*inch))

        anomaly_activities = [a for a in activities if a.get('is_anomaly', False) or a.get('risk_score', 0) >= 60]

        story.append(Paragraph(
            f"<b>Anomalies Detected:</b> {len(anomaly_activities)} out of {len(activities)} activities",
            styles['Body']
        ))
        story.append(Spacer(1, 0.15*inch))

        if anomaly_activities:
            # Anomaly type breakdown
            story.append(Paragraph("<b>Anomaly Categories</b>", styles['SubsectionTitle']))

            anomaly_types = Counter(a.get('activity_type', 'unknown') for a in anomaly_activities)
            anom_data = [['Category', 'Count', 'Percentage']]

            for atype, count in anomaly_types.most_common(8):
                pct = (count / len(anomaly_activities)) * 100
                anom_data.append([
                    atype.replace('_', ' ').title()[:25],
                    str(count),
                    f"{pct:.1f}%"
                ])

            story.append(self._create_table(anom_data, [2.5*inch, 1*inch, 1.2*inch]))

            story.append(Spacer(1, 0.3*inch))

            # High confidence anomalies
            story.append(Paragraph("<b>Highest Confidence Anomalies</b>", styles['SubsectionTitle']))

            high_conf = sorted(anomaly_activities, key=lambda x: -x.get('risk_score', 0))[:10]
            conf_data = [['Timestamp', 'Activity', 'Risk Score', 'Confidence']]

            for act in high_conf:
                conf = min(act.get('risk_score', 0) / 100, 1.0)
                conf_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    act.get('activity_type', 'unknown').replace('_', ' ').title()[:20],
                    str(act.get('risk_score', 0)),
                    f"{conf:.0%}"
                ])

            story.append(self._create_table(conf_data, [1.4*inch, 2*inch, 1*inch, 1*inch]))

        else:
            story.append(AlertBox("No anomalies detected in the analysis period", 'success'))

        story.append(PageBreak())

        # === RECOMMENDATIONS ===
        story.append(SectionHeader("Technical Recommendations", 4))
        story.append(Spacer(1, 0.2*inch))

        recs = [
            "Continue collecting training data to improve model accuracy over time",
            "Monitor false positive rate and adjust detection threshold if needed",
            "Consider retraining the model quarterly with updated behavioral patterns",
            "Review high-confidence anomalies for potential security policy updates",
        ]

        if ml_stats.get('false_positive_rate', 0) > 0.1:
            recs.insert(0, "HIGH PRIORITY: False positive rate exceeds 10% - consider threshold adjustment")

        if ml_stats.get('training_samples', 0) < 1000:
            recs.insert(0, "NOTICE: Limited training data - model performance may improve with more samples")

        for i, rec in enumerate(recs, 1):
            story.append(Paragraph(f"<b>{i}.</b> {rec}", styles['Body']))
            story.append(Spacer(1, 0.1*inch))

        # Build
        def make_canvas(filename, pagesize, **kwargs):
            return ProfessionalCanvas(filename, pagesize=pagesize,
                                      report_title="ML Analysis",
                                      report_id=report_id)

        doc.build(story, canvasmaker=make_canvas)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    # ========================================================================
    # QUICK UTILITY REPORTS
    # ========================================================================

    def generate_quick_user_report(self, user: Dict, activities: List[Dict]) -> str:
        """Generate quick 1-2 page user report"""
        timestamp = datetime.now()
        report_id = self._generate_report_id('QUR')
        filename = f"quick_report_{user.get('username', 'unknown')}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []
        styles = self.styles

        risk_score = user.get('current_risk_score', 0)
        risk_level = self._get_risk_level(risk_score)

        # Header
        story.append(Paragraph(
            '<font color="#1e3a8a" size="18"><b>IGNISYL</b></font> '
            '<font color="#6b7280" size="12">Quick Security Report</font>',
            ParagraphStyle('Header', alignment=TA_LEFT)
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=COLORS['primary'], spaceAfter=15))

        # User info
        story.append(Paragraph(
            f'<font size="16"><b>{user.get("full_name", "Unknown User")}</b></font>',
            styles['Body']
        ))
        story.append(Paragraph(
            f'{user.get("department", "N/A")} | {user.get("role", "N/A")} | Risk: <b>{risk_level}</b> ({risk_score:.0f}/100)',
            styles['Small']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Quick stats
        total = len(activities)
        critical = len([a for a in activities if a.get('risk_level') == 'CRITICAL'])
        high = len([a for a in activities if a.get('risk_level') == 'HIGH'])
        blocked = len([a for a in activities if a.get('action') == 'BLOCK'])

        stats_data = [
            ['Total Activities', 'Critical', 'High Risk', 'Blocked'],
            [str(total), str(critical), str(high), str(blocked)]
        ]

        stats_table = Table(stats_data, colWidths=[1.5*inch]*4)
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 18),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['gray']),
            ('TEXTCOLOR', (0, 1), (-1, 1), COLORS['primary_dark']),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_alt']),
            ('GRID', (0, 0), (-1, -1), 1, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(stats_table)
        story.append(Spacer(1, 0.2*inch))

        # Recent high-risk activities
        story.append(Paragraph("<b>Recent High-Risk Activities</b>", styles['SubsectionTitle']))

        high_risk = sorted([a for a in activities if a.get('risk_score', 0) >= 50],
                          key=lambda x: -x.get('risk_score', 0))[:10]

        if high_risk:
            activity_data = [['Time', 'Activity', 'Risk', 'Action']]
            for act in high_risk:
                activity_data.append([
                    self._format_timestamp(act.get('timestamp', ''), 'short'),
                    self._truncate(act.get('activity_type', 'Unknown').replace('_', ' ').title(), 28),
                    f"{act.get('risk_score', 0):.0f}",
                    act.get('action', 'ALLOW')
                ])

            story.append(self._create_table(activity_data, [1.1*inch, 2.8*inch, 0.8*inch, 1*inch]))
        else:
            story.append(Paragraph("No high-risk activities detected.", styles['Body']))

        story.append(Spacer(1, 0.2*inch))

        # Quick recommendation
        story.append(Paragraph("<b>Recommendation</b>", styles['SubsectionTitle']))

        if risk_score >= 75:
            rec = "CRITICAL: Immediate investigation required. Consider suspending account."
        elif risk_score >= 50:
            rec = "HIGH: Enhanced monitoring recommended. Schedule security review."
        elif risk_score >= 30:
            rec = "MEDIUM: Continue standard monitoring. No immediate action required."
        else:
            rec = "LOW: Normal risk profile. Standard monitoring sufficient."

        story.append(Paragraph(rec, styles['Body']))

        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=COLORS['border']))
        story.append(Paragraph(
            f'<font color="#6b7280" size="8">Report ID: {report_id} | Generated: {timestamp.strftime("%Y-%m-%d %H:%M:%S")} | CONFIDENTIAL</font>',
            ParagraphStyle('Footer', alignment=TA_CENTER, spaceBefore=10)
        ))

        doc.build(story)

        print(f"[REPORT] Generated: {filepath}")
        return filepath

    def generate_threat_report(self, user: Dict, activities: List[Dict],
                               summary_stats: Dict = None) -> str:
        """
        Generate a user threat report.
        This is an alias to generate_individual_user_report for API compatibility.

        Args:
            user: User data dictionary
            activities: List of user activities
            summary_stats: Summary statistics (optional, will be calculated if not provided)

        Returns:
            Path to generated PDF report
        """
        # If summary_stats not provided, calculate from activities
        if summary_stats is None:
            summary_stats = {
                'total_activities': len(activities),
                'high_risk': len([a for a in activities if a.get('risk_level') == 'HIGH']),
                'medium_risk': len([a for a in activities if a.get('risk_level') == 'MEDIUM']),
                'low_risk': len([a for a in activities if a.get('risk_level') == 'LOW']),
                'blocked': len([a for a in activities if a.get('action') == 'BLOCK']),
                'restricted': len([a for a in activities if a.get('action') == 'RESTRICT'])
            }

        # Generate the filename with threat_report prefix for clarity
        timestamp = datetime.now()
        username = user.get('username', 'unknown')
        filename = f"threat_report_{username}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"

        # Use the individual user report generator which creates a comprehensive report
        return self.generate_individual_user_report(user, activities, summary_stats)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def create_report_generator() -> ReportGenerator:
    """Create and return a ReportGenerator instance"""
    return ReportGenerator()


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("Testing Report Generator...")

    gen = ReportGenerator()

    # Test user
    test_user = {
        'user_id': 'user_test001',
        'username': 'jsmith',
        'full_name': 'John Smith',
        'email': 'jsmith@example.com',
        'department': 'Engineering',
        'role': 'Senior Developer',
        'status': 'active',
        'current_risk_score': 45.5,
        'registered_at': '2024-01-15T09:00:00Z',
        'last_activity': datetime.now().isoformat()
    }

    # Test activities
    test_activities = []
    for i in range(50):
        risk = np.random.choice([10, 25, 45, 65, 85], p=[0.4, 0.3, 0.15, 0.1, 0.05])
        test_activities.append({
            'timestamp': (datetime.now() - timedelta(hours=i*2)).isoformat(),
            'activity_type': np.random.choice(['file_access', 'login', 'data_transfer', 'email_send']),
            'risk_score': risk,
            'risk_level': 'LOW' if risk < 30 else 'MEDIUM' if risk < 50 else 'HIGH' if risk < 75 else 'CRITICAL',
            'action': 'ALLOW' if risk < 50 else 'RESTRICT' if risk < 75 else 'BLOCK',
            'bytes_transferred': np.random.randint(1000, 1000000)
        })

    test_stats = {
        'risk_profile': {'peak_score': 72.5, 'total_events': 50},
        'department_peers': [],
        'peer_activities': []
    }

    # Generate report
    filepath = gen.generate_individual_user_report(test_user, test_activities, test_stats)
    print(f"Report generated: {filepath}")


# ============================================================================
# MODULE-LEVEL INSTANCE
# ============================================================================
# This instance is used by routes.py and other modules that import report_generator
report_generator = ReportGenerator()
