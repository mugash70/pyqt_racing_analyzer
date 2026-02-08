"""
SVG Icons for PyQt Racing Analyzer
Replaces emojis with proper vector icons
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize

class IconLabel(QLabel):
    """Label with embedded SVG icon"""

    def __init__(self, svg_content: str, size: int = 20, parent=None):
        super().__init__(parent)

        # Create SVG widget
        self.svg_widget = QSvgWidget()
        self.svg_widget.load(svg_content.encode('utf-8'))
        self.svg_widget.setFixedSize(QSize(size, size))

        # Set as child widget
        self.setFixedSize(QSize(size, size))
        self.svg_widget.setParent(self)

        # Center the SVG
        self.svg_widget.move(0, 0)

# Trophy icon (for consensus pick)
TROPHY_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="#F59E0B"/>
<path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="#F59E0B"/>
<path d="M9 20H15V22H9V20Z" fill="#F59E0B"/>
<path d="M6 18H18V20H6V18Z" fill="#F59E0B"/>
</svg>'''

# Chart/Bar icon (for market view)
CHART_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M3 3V21H21V3H3ZM5 5H19V19H5V5Z" fill="#10B981"/>
<path d="M7 7H9V17H7V7Z" fill="#10B981"/>
<path d="M11 10H13V17H11V10Z" fill="#10B981"/>
<path d="M15 13H17V17H15V13Z" fill="#10B981"/>
</svg>'''

# Lightning bolt icon (for pace setup)
LIGHTNING_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M13 2L11.5 9H17L10 22L11.5 15H6L13 2Z" fill="#F59E0B"/>
</svg>'''

# Target icon (for win analysis)
TARGET_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="12" cy="12" r="10" stroke="#3B82F6" stroke-width="2" fill="none"/>
<circle cx="12" cy="12" r="6" stroke="#3B82F6" stroke-width="2" fill="none"/>
<circle cx="12" cy="12" r="2" stroke="#3B82F6" stroke-width="2" fill="none"/>
<path d="M12 2V4" stroke="#3B82F6" stroke-width="2"/>
<path d="M12 20V22" stroke="#3B82F6" stroke-width="2"/>
<path d="M2 12H4" stroke="#3B82F6" stroke-width="2"/>
<path d="M20 12H22" stroke="#3B82F6" stroke-width="2"/>
</svg>'''

# Horse icon (for races)
HORSE_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M8 2L6 6L8 8L10 6L8 2Z" fill="#6B7280"/>
<path d="M14 4L12 8L14 10L16 8L14 4Z" fill="#6B7280"/>
<path d="M10 8L8 12L10 14L12 12L10 8Z" fill="#6B7280"/>
<path d="M6 10L4 14L6 16L8 14L6 10Z" fill="#6B7280"/>
<path d="M16 8L14 12L16 14L18 12L16 8Z" fill="#6B7280"/>
<path d="M12 12L10 16L12 18L14 16L12 12Z" fill="#6B7280"/>
<path d="M8 14L6 18L8 20L10 18L8 14Z" fill="#6B7280"/>
</svg>'''

# Gold medal (1st place)
GOLD_MEDAL_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="10" cy="10" r="8" fill="#F59E0B" stroke="#D97706" stroke-width="1"/>
<text x="10" y="13" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white">1</text>
</svg>'''

# Silver medal (2nd place)
SILVER_MEDAL_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="10" cy="10" r="8" fill="#9CA3AF" stroke="#6B7280" stroke-width="1"/>
<text x="10" y="13" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white">2</text>
</svg>'''

# Bronze medal (3rd place)
BRONZE_MEDAL_SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="10" cy="10" r="8" fill="#D97706" stroke="#B45309" stroke-width="1"/>
<text x="10" y="13" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="white">3</text>
</svg>'''

def create_icon_widget(icon_type: str, size: int = 20) -> IconLabel:
    """Create an icon widget of the specified type"""

    icon_map = {
        'trophy': TROPHY_SVG,
        'chart': CHART_SVG,
        'lightning': LIGHTNING_SVG,
        'target': TARGET_SVG,
        'horse': HORSE_SVG,
        'gold_medal': GOLD_MEDAL_SVG,
        'silver_medal': SILVER_MEDAL_SVG,
        'bronze_medal': BRONZE_MEDAL_SVG,
    }

    if icon_type not in icon_map:
        # Return a default circle icon
        default_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="{size//2}" cy="{size//2}" r="{size//2-2}" fill="#6B7280"/>
</svg>'''
        return IconLabel(default_svg, size)

    return IconLabel(icon_map[icon_type], size)