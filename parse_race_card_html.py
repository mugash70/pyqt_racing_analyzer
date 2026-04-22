#!/usr/bin/env python3
"""
Parse race card HTML directly from HKJC website.
"""

import re

HTML_DATA = """
1	Lucky Star
Wu Weijie
11/7/8/12/1/7
2	Divine Steed
Liao Kangming
1/10/12/5/10/6
3	魅力知福
蔡約翰
11/9/14/11/6/11
"""


def parse_race_card_html(html_content: str) -> list:
    """Parse race card HTML and extract horse data."""
    horses = []
    
    lines = html_content.split('\n')
    current_horse = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if any(skip in line for skip in ['serial number', 'Horse Name', 'April 22', 'Race', 'Wednesday', 'Turf', 
                                    'Prize', 'test gate', 'Fast sex', 'pacing', 'swim', 'Horse Treadmill',
                                    'Horse walking', 'Rest', 'All morning', 'Details', '詳情', '後備馬匹']):
            continue
        
        # Check if line starts with a number (horse serial number)
        if re.match(r'^\d+\t', line):
            # Save previous horse
            if current_horse and current_horse.get('name'):
                horses.append(current_horse)
            
            parts = line.split('\t')
            current_horse = {
                'number': int(parts[0]),
                'name': parts[1].strip() if len(parts) > 1 else '',
                'trainer': parts[2].strip() if len(parts) > 2 else '',
            }
        elif current_horse and not current_horse.get('name'):
            # Try to extract name from messy format
            match = re.search(r'[\d]+\t+(.+?)\n', line)
            if match:
                current_horse['name'] = match.group(1).strip()
    
    if current_horse and current_horse.get('name'):
        horses.append(current_horse)
    
    return horses


def test_parse():
    """Test parsing with sample data."""
    horses = parse_race_card_html(HTML_DATA)
    print(f"Found {len(horses)} horses:")
    for h in horses:
        print(f"  #{h.get('number')}: {h.get('name')} ({h.get('trainer', 'N/A')})")


if __name__ == "__main__":
    test_parse()