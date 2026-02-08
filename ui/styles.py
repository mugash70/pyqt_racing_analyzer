"""
Modern PyQt6 Styling - Professional Betting Intelligence Terminal
Clean, minimal, data-first design inspired by Bloomberg terminals
"""

# Modern professional color scheme - light theme with subtle accents
COLORS = {
    # Background colors
    'background_primary': '#ffffff',     # Pure white
    'background_secondary': '#f8f9fa',   # Light gray
    'background_tertiary': '#e9ecef',    # Medium gray
    'background_accent': '#f1f3f4',      # Subtle accent

    # Text colors
    'text_primary': '#1a1a1a',           # Near black
    'text_secondary': '#5f6368',         # Medium gray
    'text_muted': '#80868b',             # Light gray
    'text_success': '#0d652d',           # Dark green
    'text_warning': '#b45000',           # Dark orange
    'text_error': '#c5221f',             # Dark red

    # Border colors
    'border_light': '#dadce0',           # Light border
    'border_medium': '#bdc1c6',          # Medium border
    'border_dark': '#9aa0a6',            # Dark border

    # Accent colors (subtle, professional)
    'accent_primary': '#1a73e8',         # Google blue
    'accent_success': '#34a853',         # Google green
    'accent_warning': '#fbbc04',         # Google yellow
    'accent_error': '#ea4335',           # Google red

    # Status colors
    'status_live': '#0d652d',            # Live indicator
    'status_updating': '#b45000',        # Updating indicator
    'status_error': '#c5221f',           # Error indicator

    # Data visualization
    'chart_primary': '#1a73e8',
    'chart_secondary': '#34a853',
    'chart_tertiary': '#fbbc04',
    'chart_quaternary': '#ea4335',
}

# Global application stylesheet - Modern Professional Theme
APP_STYLESHEET = f"""
    /* Main application */
    QMainWindow {{
        background-color: {COLORS['background_primary']};
        color: {COLORS['text_primary']};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }}

    /* Widgets */
    QWidget {{
        background-color: {COLORS['background_primary']};
        color: {COLORS['text_primary']};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}

    /* Buttons - Primary */
    QPushButton {{
        background-color: {COLORS['accent_primary']};
        color: {COLORS['background_primary']};
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 13px;
        min-height: 16px;
    }}

    QPushButton:hover {{
        background-color: #1557b0;
    }}

    QPushButton:pressed {{
        background-color: #0d47a1;
    }}

    QPushButton:disabled {{
        background-color: {COLORS['border_light']};
        color: {COLORS['text_muted']};
    }}

    /* Secondary buttons */
    QPushButton[class="secondary"] {{
        background-color: {COLORS['background_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
    }}

    QPushButton[class="secondary"]:hover {{
        background-color: {COLORS['background_tertiary']};
        border-color: {COLORS['border_medium']};
    }}

    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: 13px;
    }}

    /* Progress bars */
    QProgressBar {{
        border: 1px solid {COLORS['border_light']};
        border-radius: 4px;
        text-align: center;
        background-color: {COLORS['background_secondary']};
        height: 20px;
    }}

    QProgressBar::chunk {{
        background-color: {COLORS['accent_primary']};
        border-radius: 3px;
    }}

    /* List widgets */
    QListWidget {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }}

    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 4px;
        margin: 2px;
        border: none;
    }}

    QListWidget::item:selected {{
        background-color: {COLORS['accent_primary']};
        color: {COLORS['background_primary']};
    }}

    QListWidget::item:hover {{
        background-color: {COLORS['background_secondary']};
    }}

    /* Table widgets */
    QTableWidget {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        gridline-color: {COLORS['border_light']};
        selection-background-color: {COLORS['background_secondary']};
    }}

    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {COLORS['border_light']};
        border-right: none;
        background-color: transparent;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['background_secondary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['background_secondary']};
        color: {COLORS['text_primary']};
        padding: 12px;
        border: none;
        border-bottom: 2px solid {COLORS['border_light']};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    QHeaderView::section:hover {{
        background-color: {COLORS['background_tertiary']};
    }}

    /* Text areas */
    QTextEdit {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        padding: 12px;
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['accent_primary']};
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 12px;
        line-height: 1.4;
    }}

    QTextEdit:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* Input fields */
    QLineEdit {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 4px;
        padding: 8px 12px;
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['accent_primary']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* Combo boxes */
    QComboBox {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 4px;
        padding: 8px 12px;
        color: {COLORS['text_primary']};
        min-width: 120px;
    }}

    QComboBox:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid {COLORS['text_secondary']};
        margin-right: 8px;
    }}

    /* Scroll bars */
    QScrollBar:vertical {{
        background-color: {COLORS['background_primary']};
        width: 14px;
        border-radius: 7px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['border_medium']};
        border-radius: 7px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_dark']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
    }}

    /* Tab widget */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border_light']};
        background-color: {COLORS['background_primary']};
        border-radius: 6px;
    }}

    QTabBar::tab {{
        background-color: {COLORS['background_secondary']};
        color: {COLORS['text_secondary']};
        padding: 12px 24px;
        margin-right: 2px;
        border: none;
        font-weight: 500;
        font-size: 13px;
        border-radius: 6px 6px 0 0;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['background_primary']};
        color: {COLORS['text_primary']};
        border-bottom: 2px solid {COLORS['accent_primary']};
    }}

    QTabBar::tab:hover {{
        color: {COLORS['text_primary']};
        background-color: {COLORS['background_tertiary']};
    }}

    /* Group boxes */
    QGroupBox {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 12px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 4px 8px;
        color: {COLORS['text_primary']};
        font-weight: 600;
        font-size: 14px;
    }}

    /* Checkboxes */
    QCheckBox {{
        spacing: 8px;
        color: {COLORS['text_primary']};
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLORS['border_light']};
        border-radius: 3px;
        background-color: {COLORS['background_primary']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent_primary']};
        border-color: {COLORS['accent_primary']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent_primary']};
    }}

    /* Spin boxes */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 4px;
        padding: 6px 8px;
        color: {COLORS['text_primary']};
        min-width: 80px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* Date edits */
    QDateEdit {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 4px;
        padding: 6px 8px;
        color: {COLORS['text_primary']};
        min-width: 120px;
    }}

    QDateEdit:focus {{
        border-color: {COLORS['accent_primary']};
    }}

    /* Status indicators */
    QLabel[class="status-live"] {{
        color: {COLORS['status_live']};
        font-weight: 600;
    }}

    QLabel[class="status-updating"] {{
        color: {COLORS['status_updating']};
        font-weight: 600;
    }}

    QLabel[class="status-error"] {{
        color: {COLORS['status_error']};
        font-weight: 600;
    }}
"""

# Component-specific styles
RACE_HEADER_STYLE = f"""
    RaceHeaderCard {{
        background-color: {COLORS['background_secondary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
    }}
"""

CONTENDERS_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {COLORS['background_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        gridline-color: {COLORS['border_light']};
    }}

    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {COLORS['border_light']};
        color: {COLORS['text_primary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['background_secondary']};
        color: {COLORS['text_primary']};
        padding: 12px;
        border: none;
        border-bottom: 2px solid {COLORS['border_light']};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
"""

PROBABILITY_BAR_STYLE = f"""
    ProbabilityBar {{
        background-color: transparent;
        margin: 2px 0;
    }}
"""

# Modern card styles
CARD_STYLE = f"""
    background-color: {COLORS['background_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 20px;
"""

HERO_SECTION_STYLE = f"""
    background: linear-gradient(135deg, {COLORS['accent_primary']} 0%, {COLORS['accent_success']} 100%);
    color: {COLORS['background_primary']};
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 24px;
"""

STATUS_INDICATOR_STYLE = f"""
    QLabel[class="status-live"] {{
        color: {COLORS['status_live']};
        font-weight: 600;
        font-size: 12px;
    }}

    QLabel[class="status-updating"] {{
        color: {COLORS['status_updating']};
        font-weight: 600;
        font-size: 12px;
    }}

    QLabel[class="status-error"] {{
        color: {COLORS['status_error']};
        font-weight: 600;
        font-size: 12px;
    }}
"""
