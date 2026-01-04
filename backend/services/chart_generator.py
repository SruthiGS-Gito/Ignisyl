"""
IGNISYL Professional Chart Generator
====================================
High-quality matplotlib charts matching enterprise security report standards.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple
import io
import os
import tempfile


# =============================================================================
# COLOR SCHEME (matching report_templates.py)
# =============================================================================

class ChartColors:
    """Professional color palette for charts"""

    # Primary Blues
    PRIMARY_BLUE = '#1e3a8a'
    MEDIUM_BLUE = '#3b82f6'
    LIGHT_BLUE = '#60a5fa'
    PALE_BLUE = '#dbeafe'

    # Risk Level Colors
    CRITICAL = '#dc2626'
    HIGH = '#ea580c'
    MEDIUM = '#eab308'
    LOW = '#16a34a'

    # Chart specific
    GRID_COLOR = '#e5e7eb'
    TEXT_COLOR = '#374151'
    AXIS_COLOR = '#6b7280'

    # Gradients
    BLUE_GRADIENT = ['#dbeafe', '#93c5fd', '#60a5fa', '#3b82f6', '#1e3a8a']

    @classmethod
    def get_risk_color(cls, risk_level: str) -> str:
        """Get color for risk level"""
        return {
            'CRITICAL': cls.CRITICAL,
            'HIGH': cls.HIGH,
            'MEDIUM': cls.MEDIUM,
            'LOW': cls.LOW,
        }.get(risk_level.upper(), cls.AXIS_COLOR)


# =============================================================================
# CHART STYLING UTILITIES
# =============================================================================

def apply_professional_style(ax, title: str = None, xlabel: str = None, ylabel: str = None):
    """Apply consistent professional styling to chart axes"""

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(ChartColors.AXIS_COLOR)
    ax.spines['bottom'].set_color(ChartColors.AXIS_COLOR)

    # Grid styling
    ax.grid(True, axis='y', linestyle='-', alpha=0.3, color=ChartColors.GRID_COLOR)
    ax.set_axisbelow(True)

    # Tick styling
    ax.tick_params(colors=ChartColors.TEXT_COLOR, labelsize=9)

    # Labels
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', color=ChartColors.PRIMARY_BLUE, pad=15)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=ChartColors.TEXT_COLOR, labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=ChartColors.TEXT_COLOR, labelpad=10)


def save_chart_to_file(fig, prefix: str = "chart") -> str:
    """Save chart to temporary file and return path"""
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filepath = os.path.join(temp_dir, f"{prefix}_{timestamp}.png")

    fig.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none',
                pad_inches=0.2)
    plt.close(fig)

    return filepath


# =============================================================================
# CHART 1: ACTIVITY TIMELINE (Stacked Bar Chart)
# =============================================================================

def create_activity_timeline_chart(activities: List[Dict], days: int = 7) -> Optional[str]:
    """
    Create professional stacked bar chart showing activity by risk level over time.

    Args:
        activities: List of activity dicts with 'timestamp' and 'risk_level'
        days: Number of days to show

    Returns:
        Path to saved chart image
    """
    if not activities:
        return None

    # Prepare data by day
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Initialize daily counts
    daily_data = defaultdict(lambda: {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0})

    for activity in activities:
        timestamp = activity.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue

        if timestamp and start_date <= timestamp <= end_date:
            day_key = timestamp.strftime('%m/%d')
            risk_level = activity.get('risk_level', 'LOW').upper()
            if risk_level in daily_data[day_key]:
                daily_data[day_key][risk_level] += 1

    # Create date range
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%m/%d'))
        current += timedelta(days=1)

    # Prepare data arrays
    critical_counts = [daily_data[d]['CRITICAL'] for d in dates]
    high_counts = [daily_data[d]['HIGH'] for d in dates]
    medium_counts = [daily_data[d]['MEDIUM'] for d in dates]
    low_counts = [daily_data[d]['LOW'] for d in dates]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(dates))
    width = 0.7

    # Create stacked bars
    bars_low = ax.bar(x, low_counts, width, label='Low', color=ChartColors.LOW, alpha=0.9)
    bars_medium = ax.bar(x, medium_counts, width, bottom=low_counts,
                         label='Medium', color=ChartColors.MEDIUM, alpha=0.9)
    bars_high = ax.bar(x, high_counts, width,
                       bottom=[l+m for l,m in zip(low_counts, medium_counts)],
                       label='High', color=ChartColors.HIGH, alpha=0.9)
    bars_critical = ax.bar(x, critical_counts, width,
                           bottom=[l+m+h for l,m,h in zip(low_counts, medium_counts, high_counts)],
                           label='Critical', color=ChartColors.CRITICAL, alpha=0.9)

    # Apply professional styling
    apply_professional_style(ax,
                            title='Activity Timeline by Risk Level',
                            xlabel='Date',
                            ylabel='Number of Activities')

    # X-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)

    # Legend
    ax.legend(loc='upper left', frameon=True, fancybox=True,
              shadow=False, fontsize=9, ncol=4,
              bbox_to_anchor=(0, 1.02, 1, 0.1), mode='expand')

    # Add value labels on top of bars
    totals = [l+m+h+c for l,m,h,c in zip(low_counts, medium_counts, high_counts, critical_counts)]
    for i, total in enumerate(totals):
        if total > 0:
            ax.annotate(str(total), xy=(i, total), ha='center', va='bottom',
                       fontsize=8, color=ChartColors.TEXT_COLOR)

    plt.tight_layout()
    return save_chart_to_file(fig, "timeline")


# =============================================================================
# CHART 2: RISK SCORE TREND (Area Chart with Gradient)
# =============================================================================

def create_risk_trend_chart(activities: List[Dict], days: int = 7) -> Optional[str]:
    """
    Create professional area chart showing risk score trends over time.

    Features:
    - Gradient fill under the line
    - Average line (blue solid)
    - Peak line (red dashed)
    - Threshold lines (critical: 75, high: 50)

    Returns:
        Path to saved chart image
    """
    if not activities:
        return None

    # Prepare data by day
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    daily_scores = defaultdict(list)

    for activity in activities:
        timestamp = activity.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue

        risk_score = activity.get('risk_score', 0)
        if timestamp and start_date <= timestamp <= end_date:
            day_key = timestamp.strftime('%m/%d')
            daily_scores[day_key].append(risk_score)

    # Create date range
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%m/%d'))
        current += timedelta(days=1)

    # Calculate averages and peaks
    avg_scores = []
    peak_scores = []
    for d in dates:
        scores = daily_scores.get(d, [0])
        avg_scores.append(np.mean(scores) if scores else 0)
        peak_scores.append(max(scores) if scores else 0)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(dates))

    # Create gradient fill under average line
    ax.fill_between(x, avg_scores, alpha=0.3, color=ChartColors.LIGHT_BLUE)

    # Plot average line
    ax.plot(x, avg_scores, color=ChartColors.MEDIUM_BLUE, linewidth=2.5,
            label='Average Risk Score', marker='o', markersize=5)

    # Plot peak line (dashed)
    ax.plot(x, peak_scores, color=ChartColors.CRITICAL, linewidth=1.5,
            linestyle='--', label='Peak Risk Score', alpha=0.8)

    # Threshold lines
    ax.axhline(y=75, color=ChartColors.CRITICAL, linestyle=':', linewidth=1, alpha=0.7, label='Critical Threshold (75)')
    ax.axhline(y=50, color=ChartColors.HIGH, linestyle=':', linewidth=1, alpha=0.7, label='High Threshold (50)')

    # Apply professional styling
    apply_professional_style(ax,
                            title='Risk Score Trend Analysis',
                            xlabel='Date',
                            ylabel='Risk Score')

    # Y-axis limits
    ax.set_ylim(0, 100)

    # X-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)

    # Legend
    ax.legend(loc='upper right', frameon=True, fancybox=True, fontsize=8)

    plt.tight_layout()
    return save_chart_to_file(fig, "risk_trend")


# =============================================================================
# CHART 3: ACTIVITY DISTRIBUTION (Professional Pie Chart)
# =============================================================================

def create_distribution_pie_chart(activities: List[Dict],
                                  group_by: str = 'activity_type') -> Optional[str]:
    """
    Create professional pie chart showing activity distribution.

    Args:
        activities: List of activity dicts
        group_by: Field to group by ('activity_type', 'risk_level', etc.)

    Returns:
        Path to saved chart image
    """
    if not activities:
        return None

    # Count by group
    counts = Counter(a.get(group_by, 'Unknown') for a in activities)

    if not counts:
        return None

    # Sort by count
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    # Limit to top 8 categories
    if len(sorted_items) > 8:
        top_items = sorted_items[:7]
        other_count = sum(c for _, c in sorted_items[7:])
        top_items.append(('Other', other_count))
        sorted_items = top_items

    labels = [item[0] for item in sorted_items]
    sizes = [item[1] for item in sorted_items]

    # Color palette
    if group_by == 'risk_level':
        colors = [ChartColors.get_risk_color(label) for label in labels]
    else:
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(labels)))

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        colors=colors,
        startangle=90,
        explode=[0.02] * len(sizes),
        shadow=False,
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
    )

    # Style percentage labels
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    # Add legend
    legend_labels = [f'{label} ({count:,})' for label, count in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, title="Activity Types",
              loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=9, title_fontsize=10)

    # Title
    title_map = {
        'activity_type': 'Activity Type Distribution',
        'risk_level': 'Risk Level Distribution',
        'action': 'Action Distribution',
    }
    ax.set_title(title_map.get(group_by, 'Distribution'),
                 fontsize=12, fontweight='bold',
                 color=ChartColors.PRIMARY_BLUE, pad=20)

    plt.tight_layout()
    return save_chart_to_file(fig, "distribution")


def create_risk_distribution_pie_chart(activities: List[Dict]) -> Optional[str]:
    """Create pie chart specifically for risk level distribution"""
    if not activities:
        return None

    # Count by risk level
    risk_counts = Counter(a.get('risk_level', 'LOW').upper() for a in activities)

    # Ensure all risk levels are represented
    for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if level not in risk_counts:
            risk_counts[level] = 0

    # Order: CRITICAL, HIGH, MEDIUM, LOW
    order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    labels = [l for l in order if risk_counts[l] > 0]
    sizes = [risk_counts[l] for l in labels]
    colors = [ChartColors.get_risk_color(l) for l in labels]

    if not sizes:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 2 else '',
        colors=colors,
        startangle=90,
        explode=[0.03 if l == 'CRITICAL' else 0.01 for l in labels],
        shadow=False,
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
    )

    # Style percentage labels
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    # Add legend
    legend_labels = [f'{label} ({count:,})' for label, count in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, title="Risk Levels",
              loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=10, title_fontsize=11)

    ax.set_title('Risk Level Distribution',
                 fontsize=12, fontweight='bold',
                 color=ChartColors.PRIMARY_BLUE, pad=20)

    plt.tight_layout()
    return save_chart_to_file(fig, "risk_pie")


# =============================================================================
# CHART 4: HOURLY ACTIVITY PATTERN (Dual-Axis Chart)
# =============================================================================

def create_hourly_pattern_chart(activities: List[Dict]) -> Optional[str]:
    """
    Create professional dual-axis chart showing hourly activity patterns.

    Features:
    - Bars: activity count (blue for business hours, orange for after-hours)
    - Line: average risk score (red line, secondary axis)
    - After-hours highlighting (6PM-6AM background shading)

    Returns:
        Path to saved chart image
    """
    if not activities:
        return None

    # Initialize hourly data
    hourly_counts = defaultdict(int)
    hourly_risk_scores = defaultdict(list)

    for activity in activities:
        timestamp = activity.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue

        if timestamp:
            hour = timestamp.hour
            hourly_counts[hour] += 1
            hourly_risk_scores[hour].append(activity.get('risk_score', 0))

    # Prepare data
    hours = list(range(24))
    counts = [hourly_counts[h] for h in hours]
    avg_risks = [np.mean(hourly_risk_scores[h]) if hourly_risk_scores[h] else 0 for h in hours]

    # Determine bar colors (business hours vs after-hours)
    bar_colors = []
    for h in hours:
        if 6 <= h < 18:  # 6 AM to 6 PM = business hours
            bar_colors.append(ChartColors.MEDIUM_BLUE)
        else:
            bar_colors.append(ChartColors.HIGH)  # After-hours

    # Create figure with dual axes
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    # After-hours background shading
    ax1.axvspan(-0.5, 5.5, alpha=0.1, color=ChartColors.HIGH, label='After Hours')
    ax1.axvspan(17.5, 23.5, alpha=0.1, color=ChartColors.HIGH)

    # Bar chart (activity counts)
    bars = ax1.bar(hours, counts, color=bar_colors, alpha=0.8, width=0.8)

    # Line chart (risk scores)
    line = ax2.plot(hours, avg_risks, color=ChartColors.CRITICAL, linewidth=2,
                    marker='o', markersize=4, label='Avg Risk Score')

    # Styling for ax1 (left axis)
    ax1.set_xlabel('Hour of Day', fontsize=10, color=ChartColors.TEXT_COLOR)
    ax1.set_ylabel('Activity Count', fontsize=10, color=ChartColors.MEDIUM_BLUE)
    ax1.tick_params(axis='y', labelcolor=ChartColors.MEDIUM_BLUE)
    ax1.set_xticks(hours)
    ax1.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right', fontsize=7)

    # Styling for ax2 (right axis)
    ax2.set_ylabel('Average Risk Score', fontsize=10, color=ChartColors.CRITICAL)
    ax2.tick_params(axis='y', labelcolor=ChartColors.CRITICAL)
    ax2.set_ylim(0, 100)

    # Remove spines
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)

    # Title
    ax1.set_title('Hourly Activity Pattern Analysis',
                  fontsize=12, fontweight='bold',
                  color=ChartColors.PRIMARY_BLUE, pad=15)

    # Combined legend
    business_patch = mpatches.Patch(color=ChartColors.MEDIUM_BLUE, alpha=0.8, label='Business Hours (6AM-6PM)')
    after_patch = mpatches.Patch(color=ChartColors.HIGH, alpha=0.8, label='After Hours')
    risk_line = plt.Line2D([0], [0], color=ChartColors.CRITICAL, linewidth=2, label='Avg Risk Score')

    ax1.legend(handles=[business_patch, after_patch, risk_line],
               loc='upper left', frameon=True, fontsize=8)

    # Grid
    ax1.grid(True, axis='y', linestyle='-', alpha=0.3)
    ax1.set_axisbelow(True)

    plt.tight_layout()
    return save_chart_to_file(fig, "hourly_pattern")


# =============================================================================
# ADDITIONAL CHART TYPES
# =============================================================================

def create_ml_performance_chart(metrics: Dict) -> Optional[str]:
    """
    Create chart showing ML model performance metrics.

    Args:
        metrics: Dict with accuracy, precision, recall, f1_score

    Returns:
        Path to saved chart image
    """
    if not metrics:
        return None

    # Prepare data
    labels = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
    values = [
        metrics.get('accuracy', 0),
        metrics.get('precision', 0),
        metrics.get('recall', 0),
        metrics.get('f1_score', 0)
    ]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(labels))

    # Create bars with gradient colors
    colors = [ChartColors.PRIMARY_BLUE, ChartColors.MEDIUM_BLUE,
              ChartColors.LIGHT_BLUE, ChartColors.LOW]

    bars = ax.bar(x, values, color=colors, alpha=0.9, width=0.6)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'{val:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold',
                    color=ChartColors.TEXT_COLOR)

    # Apply styling
    apply_professional_style(ax,
                            title='ML Model Performance Metrics',
                            ylabel='Percentage (%)')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 110)

    # Target line
    ax.axhline(y=80, color=ChartColors.LOW, linestyle='--', linewidth=1,
               alpha=0.7, label='Target (80%)')
    ax.legend(loc='upper right', fontsize=9)

    plt.tight_layout()
    return save_chart_to_file(fig, "ml_performance")


def create_user_comparison_chart(users_data: List[Dict]) -> Optional[str]:
    """
    Create horizontal bar chart comparing user risk scores.

    Args:
        users_data: List of dicts with 'username' and 'risk_score'

    Returns:
        Path to saved chart image
    """
    if not users_data:
        return None

    # Sort by risk score (descending)
    sorted_users = sorted(users_data, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]

    usernames = [u.get('username', 'Unknown') for u in sorted_users]
    scores = [u.get('risk_score', 0) for u in sorted_users]

    # Determine colors based on risk score
    colors = []
    for score in scores:
        if score >= 75:
            colors.append(ChartColors.CRITICAL)
        elif score >= 50:
            colors.append(ChartColors.HIGH)
        elif score >= 25:
            colors.append(ChartColors.MEDIUM)
        else:
            colors.append(ChartColors.LOW)

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))

    y = np.arange(len(usernames))

    # Horizontal bars
    bars = ax.barh(y, scores, color=colors, alpha=0.9, height=0.6)

    # Add value labels
    for bar, score in zip(bars, scores):
        width = bar.get_width()
        ax.annotate(f'{score:.0f}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=9,
                    color=ChartColors.TEXT_COLOR)

    # Apply styling
    ax.set_yticks(y)
    ax.set_yticklabels(usernames, fontsize=9)
    ax.set_xlim(0, 110)
    ax.invert_yaxis()  # Highest at top

    apply_professional_style(ax,
                            title='User Risk Score Comparison',
                            xlabel='Risk Score')

    # Threshold lines
    ax.axvline(x=75, color=ChartColors.CRITICAL, linestyle=':', alpha=0.7, label='Critical')
    ax.axvline(x=50, color=ChartColors.HIGH, linestyle=':', alpha=0.7, label='High')

    plt.tight_layout()
    return save_chart_to_file(fig, "user_comparison")


def create_threat_type_chart(activities: List[Dict]) -> Optional[str]:
    """
    Create horizontal bar chart showing threat types by count.

    Returns:
        Path to saved chart image
    """
    if not activities:
        return None

    # Count threat types (high risk activities only)
    threat_activities = [a for a in activities if a.get('risk_level', '').upper() in ['CRITICAL', 'HIGH']]

    if not threat_activities:
        return None

    threat_counts = Counter(a.get('activity_type', 'Unknown') for a in threat_activities)

    # Sort by count
    sorted_threats = sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    labels = [t[0] for t in sorted_threats]
    counts = [t[1] for t in sorted_threats]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))

    y = np.arange(len(labels))

    # Color gradient based on count
    max_count = max(counts) if counts else 1
    colors = [plt.cm.Reds(0.3 + 0.6 * (c / max_count)) for c in counts]

    # Horizontal bars
    bars = ax.barh(y, counts, color=colors, alpha=0.9, height=0.6)

    # Add value labels
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.annotate(f'{count:,}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=9,
                    color=ChartColors.TEXT_COLOR)

    # Apply styling
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()

    apply_professional_style(ax,
                            title='Threat Types (High/Critical)',
                            xlabel='Count')

    plt.tight_layout()
    return save_chart_to_file(fig, "threat_types")


# =============================================================================
# SYSTEM-LEVEL CHARTS
# =============================================================================

def create_system_activity_timeline(activities: List[Dict], days: int = 7) -> Optional[str]:
    """Create system-wide activity timeline for comprehensive reports"""
    return create_activity_timeline_chart(activities, days)


def create_system_risk_pie(activities: List[Dict]) -> Optional[str]:
    """Create system-wide risk distribution pie chart"""
    return create_risk_distribution_pie_chart(activities)


# =============================================================================
# CLEANUP UTILITY
# =============================================================================

def cleanup_chart_files(filepaths: List[str]):
    """Clean up temporary chart files"""
    for filepath in filepaths:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not remove chart file {filepath}: {e}")
