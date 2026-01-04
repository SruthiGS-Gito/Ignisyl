"""
IGNISYL Professional Report Templates
=====================================
Enterprise-grade PDF report styling with professional color schemes,
typography, and reusable components for security reports.
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    Paragraph, Table, TableStyle, Spacer, Image,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# =============================================================================
# IGNISYL COLOR SCHEME - Professional Blue Theme
# =============================================================================

class IGNISYLColors:
    """Professional color palette for IGNISYL reports"""

    # Primary Blues
    PRIMARY_BLUE = colors.HexColor('#1e3a8a')      # Deep navy blue
    MEDIUM_BLUE = colors.HexColor('#3b82f6')       # Bright blue
    LIGHT_BLUE = colors.HexColor('#60a5fa')        # Sky blue
    PALE_BLUE = colors.HexColor('#dbeafe')         # Very light blue
    DARK_BLUE = colors.HexColor('#1e40af')         # Dark blue

    # Risk Level Colors
    CRITICAL_RED = colors.HexColor('#dc2626')      # Critical - bright red
    HIGH_ORANGE = colors.HexColor('#ea580c')       # High - orange
    MEDIUM_YELLOW = colors.HexColor('#eab308')     # Medium - yellow
    LOW_GREEN = colors.HexColor('#16a34a')         # Low - green

    # Background variants (lighter)
    CRITICAL_BG = colors.HexColor('#fef2f2')       # Light red background
    HIGH_BG = colors.HexColor('#fff7ed')           # Light orange background
    MEDIUM_BG = colors.HexColor('#fefce8')         # Light yellow background
    LOW_BG = colors.HexColor('#f0fdf4')            # Light green background

    # Neutrals
    WHITE = colors.white
    BLACK = colors.black
    DARK_GRAY = colors.HexColor('#374151')
    MEDIUM_GRAY = colors.HexColor('#6b7280')
    LIGHT_GRAY = colors.HexColor('#9ca3af')
    PALE_GRAY = colors.HexColor('#f3f4f6')

    # Table colors
    TABLE_HEADER_BG = MEDIUM_BLUE
    TABLE_HEADER_TEXT = WHITE
    TABLE_ROW_ALT = colors.HexColor('#f8fafc')
    TABLE_BORDER = colors.HexColor('#e2e8f0')

    # Classification banner
    CONFIDENTIAL_BG = colors.HexColor('#fbbf24')   # Amber
    CONFIDENTIAL_TEXT = colors.HexColor('#78350f') # Dark amber

    @classmethod
    def get_risk_color(cls, risk_level: str):
        """Get color for risk level"""
        risk_map = {
            'CRITICAL': cls.CRITICAL_RED,
            'HIGH': cls.HIGH_ORANGE,
            'MEDIUM': cls.MEDIUM_YELLOW,
            'LOW': cls.LOW_GREEN,
        }
        return risk_map.get(risk_level.upper(), cls.MEDIUM_GRAY)

    @classmethod
    def get_risk_bg_color(cls, risk_level: str):
        """Get background color for risk level"""
        risk_map = {
            'CRITICAL': cls.CRITICAL_BG,
            'HIGH': cls.HIGH_BG,
            'MEDIUM': cls.MEDIUM_BG,
            'LOW': cls.LOW_BG,
        }
        return risk_map.get(risk_level.upper(), cls.PALE_GRAY)


# =============================================================================
# IGNISYL PARAGRAPH STYLES
# =============================================================================

class IGNISYLStyles:
    """Professional paragraph styles for IGNISYL reports"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create all custom paragraph styles"""

        # Cover Page Styles
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=32,
            textColor=IGNISYLColors.PRIMARY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=6,
            spaceBefore=0,
        ))

        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=18,
            textColor=IGNISYLColors.MEDIUM_BLUE,
            alignment=TA_CENTER,
            spaceAfter=30,
        ))

        self.styles.add(ParagraphStyle(
            name='CoverMeta',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))

        # Section Headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=IGNISYLColors.WHITE,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=0,
            leftIndent=10,
            rightIndent=10,
        ))

        self.styles.add(ParagraphStyle(
            name='SectionSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=IGNISYLColors.MEDIUM_GRAY,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=12,
        ))

        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=IGNISYLColors.PRIMARY_BLUE,
            alignment=TA_LEFT,
            spaceBefore=16,
            spaceAfter=8,
        ))

        # Body Text Styles
        self.styles.add(ParagraphStyle(
            name='IGBodyText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=8,
            leading=14,
        ))

        self.styles.add(ParagraphStyle(
            name='BodyTextLeft',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=8,
            leading=14,
        ))

        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=IGNISYLColors.MEDIUM_GRAY,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4,
        ))

        # Bullet/List Styles
        self.styles.add(ParagraphStyle(
            name='BulletItem',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4,
            leftIndent=20,
            bulletIndent=10,
        ))

        self.styles.add(ParagraphStyle(
            name='NumberedItem',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4,
            leftIndent=25,
            bulletIndent=10,
        ))

        # Alert/Highlight Styles
        self.styles.add(ParagraphStyle(
            name='CriticalAlert',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=IGNISYLColors.CRITICAL_RED,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=4,
        ))

        self.styles.add(ParagraphStyle(
            name='HighAlert',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=IGNISYLColors.HIGH_ORANGE,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=4,
        ))

        self.styles.add(ParagraphStyle(
            name='SuccessText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=IGNISYLColors.LOW_GREEN,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=4,
        ))

        # Metric/Stats Styles
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=IGNISYLColors.PRIMARY_BLUE,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=2,
        ))

        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=IGNISYLColors.MEDIUM_GRAY,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=8,
        ))

        # Footer/Header Styles
        self.styles.add(ParagraphStyle(
            name='PageFooter',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=IGNISYLColors.MEDIUM_GRAY,
            alignment=TA_CENTER,
        ))

        self.styles.add(ParagraphStyle(
            name='Confidential',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=IGNISYLColors.CONFIDENTIAL_TEXT,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=4,
        ))

        # Table Cell Styles
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=IGNISYLColors.WHITE,
            alignment=TA_LEFT,
        ))

        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_LEFT,
        ))

        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=IGNISYLColors.DARK_GRAY,
            alignment=TA_CENTER,
        ))

    def __getitem__(self, key):
        """Allow dictionary-style access to styles"""
        return self.styles[key]

    def get(self, key, default=None):
        """Get style with default fallback"""
        try:
            return self.styles[key]
        except KeyError:
            return default or self.styles['Normal']


# =============================================================================
# TABLE TEMPLATES
# =============================================================================

class IGNISYLTableStyles:
    """Professional table styles for IGNISYL reports"""

    @staticmethod
    def get_standard_table_style(num_rows: int = 10) -> TableStyle:
        """Get standard table style with alternating rows"""
        style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), IGNISYLColors.MEDIUM_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), IGNISYLColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Body rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), IGNISYLColors.DARK_GRAY),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, IGNISYLColors.TABLE_BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, IGNISYLColors.PRIMARY_BLUE),

            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Add alternating row colors
        for i in range(1, num_rows + 1):
            if i % 2 == 0:
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i), IGNISYLColors.TABLE_ROW_ALT)
                )

        return TableStyle(style_commands)

    @staticmethod
    def get_compact_table_style(num_rows: int = 10) -> TableStyle:
        """Get compact table style for dense data"""
        style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), IGNISYLColors.LIGHT_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), IGNISYLColors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),

            # Body rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TEXTCOLOR', (0, 1), (-1, -1), IGNISYLColors.DARK_GRAY),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.25, IGNISYLColors.TABLE_BORDER),

            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Add alternating row colors
        for i in range(1, num_rows + 1):
            if i % 2 == 0:
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i), IGNISYLColors.PALE_GRAY)
                )

        return TableStyle(style_commands)

    @staticmethod
    def get_metric_card_style() -> TableStyle:
        """Get style for metric/stat cards"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), IGNISYLColors.PALE_BLUE),
            ('BOX', (0, 0), (-1, -1), 1, IGNISYLColors.LIGHT_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ])

    @staticmethod
    def get_risk_highlight_style(risk_level: str) -> TableStyle:
        """Get table style with risk-based highlighting"""
        bg_color = IGNISYLColors.get_risk_bg_color(risk_level)
        border_color = IGNISYLColors.get_risk_color(risk_level)

        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 2, border_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ])


# =============================================================================
# REUSABLE SECTION COMPONENTS
# =============================================================================

class IGNISYLComponents:
    """Reusable report components"""

    def __init__(self, styles: IGNISYLStyles):
        self.styles = styles

    def create_section_header(self, title: str, subtitle: str = None) -> list:
        """Create a professional section header with blue background"""
        elements = []

        # Create header table with blue background
        header_data = [[Paragraph(title, self.styles['SectionHeader'])]]
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), IGNISYLColors.MEDIUM_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(header_table)

        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['SectionSubtitle']))
        else:
            elements.append(Spacer(1, 8))

        return elements

    def create_subsection_header(self, title: str) -> Paragraph:
        """Create a subsection header"""
        return Paragraph(title, self.styles['SubsectionHeader'])

    def create_metric_cards(self, metrics: list) -> Table:
        """
        Create a row of metric cards
        metrics: list of dicts with 'value', 'label', 'color' (optional)
        """
        cells = []
        for metric in metrics:
            value = metric.get('value', '0')
            label = metric.get('label', '')
            color = metric.get('color', IGNISYLColors.PRIMARY_BLUE)

            cell_content = [
                Paragraph(f'<font color="{color.hexval()}">{value}</font>',
                         self.styles['MetricValue']),
                Paragraph(label, self.styles['MetricLabel'])
            ]
            cells.append(cell_content)

        # Create table
        table_data = [cells]
        col_width = (7*inch) / len(metrics)
        table = Table(table_data, colWidths=[col_width] * len(metrics))
        table.setStyle(IGNISYLTableStyles.get_metric_card_style())

        return table

    def create_risk_badge(self, risk_score: float, size: str = 'large') -> Table:
        """Create a risk score badge"""
        if risk_score >= 75:
            risk_level = 'CRITICAL'
        elif risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 25:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        color = IGNISYLColors.get_risk_color(risk_level)
        bg_color = IGNISYLColors.get_risk_bg_color(risk_level)

        if size == 'large':
            font_size = 36
            padding = 15
            width = 1.5*inch
        else:
            font_size = 18
            padding = 8
            width = 1*inch

        badge_data = [[
            Paragraph(
                f'<font size="{font_size}" color="{color.hexval()}"><b>{int(risk_score)}</b></font>',
                self.styles['MetricValue']
            )
        ], [
            Paragraph(
                f'<font size="10" color="{color.hexval()}">{risk_level}</font>',
                self.styles['MetricLabel']
            )
        ]]

        badge = Table(badge_data, colWidths=[width])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 2, color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), padding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ]))

        return badge

    def create_classification_banner(self, classification: str = "CONFIDENTIAL") -> Table:
        """Create a classification banner"""
        banner_data = [[
            Paragraph(
                f'<b>{classification} - INTERNAL USE ONLY</b>',
                self.styles['Confidential']
            )
        ]]

        banner = Table(banner_data, colWidths=[7*inch])
        banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), IGNISYLColors.CONFIDENTIAL_BG),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return banner

    def create_key_value_table(self, data: dict, title: str = None) -> list:
        """Create a key-value table for displaying properties"""
        elements = []

        if title:
            elements.append(self.create_subsection_header(title))

        table_data = []
        for key, value in data.items():
            table_data.append([
                Paragraph(f'<b>{key}</b>', self.styles['TableCell']),
                Paragraph(str(value), self.styles['TableCell'])
            ])

        table = Table(table_data, colWidths=[2*inch, 5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), IGNISYLColors.PALE_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, IGNISYLColors.TABLE_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        return elements

    def create_bullet_list(self, items: list, style: str = 'BulletItem') -> list:
        """Create a bullet list"""
        elements = []
        for item in items:
            elements.append(Paragraph(f'\u2022 {item}', self.styles[style]))
        return elements

    def create_numbered_list(self, items: list) -> list:
        """Create a numbered list"""
        elements = []
        for i, item in enumerate(items, 1):
            elements.append(Paragraph(f'{i}. {item}', self.styles['NumberedItem']))
        return elements

    def create_horizontal_line(self) -> HRFlowable:
        """Create a horizontal separator line"""
        return HRFlowable(
            width="100%",
            thickness=1,
            color=IGNISYLColors.LIGHT_BLUE,
            spaceBefore=10,
            spaceAfter=10
        )


# =============================================================================
# PAGE TEMPLATES
# =============================================================================

def add_page_header_footer(canvas, doc, report_title: str = "IGNISYL Security Report"):
    """Add header and footer to each page"""
    from datetime import datetime

    canvas.saveState()

    # Header
    canvas.setFillColor(IGNISYLColors.PRIMARY_BLUE)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(0.75*inch, 10.5*inch, "[SHIELD] IGNISYL")

    canvas.setFillColor(IGNISYLColors.MEDIUM_GRAY)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(7.75*inch, 10.5*inch, report_title)

    # Header line
    canvas.setStrokeColor(IGNISYLColors.LIGHT_BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, 10.4*inch, 7.75*inch, 10.4*inch)

    # Footer
    canvas.setFillColor(IGNISYLColors.MEDIUM_GRAY)
    canvas.setFont('Helvetica', 8)

    # Page number
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(4.25*inch, 0.5*inch, f"Page {page_num}")

    # Date
    canvas.drawString(0.75*inch, 0.5*inch, datetime.now().strftime("%Y-%m-%d"))

    # Confidential
    canvas.setFillColor(IGNISYLColors.HIGH_ORANGE)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawRightString(7.75*inch, 0.5*inch, "CONFIDENTIAL")

    # Footer line
    canvas.setStrokeColor(IGNISYLColors.LIGHT_BLUE)
    canvas.line(0.75*inch, 0.65*inch, 7.75*inch, 0.65*inch)

    canvas.restoreState()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_number(value: float, decimals: int = 1) -> str:
    """Format number with thousands separator"""
    if isinstance(value, int) or value == int(value):
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format as percentage"""
    return f"{value:.{decimals}f}%"


def format_risk_level(risk_score: float) -> str:
    """Get risk level from score"""
    if risk_score >= 75:
        return 'CRITICAL'
    elif risk_score >= 50:
        return 'HIGH'
    elif risk_score >= 25:
        return 'MEDIUM'
    return 'LOW'


def get_risk_color_hex(risk_level: str) -> str:
    """Get hex color for risk level (for matplotlib)"""
    colors_map = {
        'CRITICAL': '#dc2626',
        'HIGH': '#ea580c',
        'MEDIUM': '#eab308',
        'LOW': '#16a34a',
    }
    return colors_map.get(risk_level.upper(), '#6b7280')
