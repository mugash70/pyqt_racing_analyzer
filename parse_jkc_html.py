#!/usr/bin/env python3
"""
Parse Jockey King Statistics from HKJC HTML.
"""

import re
from bs4 import BeautifulSoup

# Jockey data extracted from the HTML
JKC_DATA = [
    {"rank": 1, "jockey": "Panton", "avg_points": 30.2, "season_avg": 33.4},
    {"rank": 2, "jockey": "Moreira", "avg_points": 28.0, "season_avg": 27.5},
    {"rank": 3, "jockey": "Ai Zhaoli", "avg_points": 19.2, "season_avg": 15.5},
    {"rank": 4, "jockey": "Buwen", "avg_points": 19.6, "season_avg": 18.6},
    {"rank": 5, "jockey": "Zhou Junle", "avg_points": 10.2, "season_avg": 7.2},
    {"rank": 6, "jockey": "Bu Haorong", "avg_points": 0.0, "season_avg": None},
    {"rank": 7, "jockey": "Tian Tai'an", "avg_points": 12.0, "season_avg": 14.6},
    {"rank": 8, "jockey": "Pan Minghui", "avg_points": 6.2, "season_avg": 11.1},
    {"rank": 9, "jockey": "Bado", "avg_points": 13.3, "season_avg": 9.5},
    {"rank": 10, "jockey": "Jin Chenggang", "avg_points": 7.2, "season_avg": 5.8},
    {"rank": 11, "jockey": "Sidwell", "avg_points": 4.6, "season_avg": 10.2},
    {"rank": 12, "jockey": "Liang Jiajun", "avg_points": 8.9, "season_avg": 11.3},
    {"rank": 13, "jockey": "Ormin", "avg_points": 8.9, "season_avg": 8.3},
]


def parse_jkc_html(html_content: str) -> list:
    """Parse Jockey King statistics from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    jkc_stats = []
    table = soup.find('table', {'class': 'table_bd'})
    
    if not table:
        return []
    
    rows = table.find_all('tr')
    for row in rows[2:]:  # Skip header rows
        cols = row.find_all('td')
        if len(cols) < 2:
            continue
        
        # Get jockey name
        jockey_link = cols[1].find('a')
        if jockey_link:
            jockey_name = jockey_link.text.strip()
        else:
            jockey_name = cols[1].text.strip()
        
        if 'Other jockeys' in jockey_name or not jockey_name or jockey_name.startswith('-'):
            continue
        
        # Get average points (column 11)
        avg_text = cols[11].text.strip() if len(cols) > 11 else '0'
        try:
            avg_points = float(avg_text) if avg_text and avg_text not in ['-', ''] else 0
        except ValueError:
            avg_points = 0
        
        # Get season average (column 13)
        season_text = cols[13].text.strip() if len(cols) > 13 else '0'
        try:
            season_avg = float(season_text) if season_text and season_text not in ['-', ''] else 0
        except ValueError:
            season_avg = 0
        
        jkc_stats.append({
            'jockey': jockey_name,
            'avg_points': avg_points,
            'season_avg': season_avg
        })
    
    return jkc_stats


def save_to_db():
    """Save JKC stats to database."""
    import sqlite3
    import os
    from datetime import datetime
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    scraped_at = datetime.now().isoformat()
    
    saved = 0
    for stat in JKC_DATA:
        # Check if exists
        cursor.execute("""
            SELECT id FROM jkc_stats 
            WHERE jockey_name = ?
        """, (stat['jockey'],))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE jkc_stats SET avg_points = ?, season_avg = ?, scraped_at = ?
                WHERE id = ?
            """, (stat['avg_points'], stat['season_avg'], scraped_at, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO jkc_stats (jockey_name, avg_points, season_avg, scraped_at)
                VALUES (?, ?, ?, ?)
            """, (stat['jockey'], stat['avg_points'], stat['season_avg'], scraped_at))
        
        saved += 1
        print(f"  {stat['jockey']}: {stat['avg_points']} ({stat['season_avg']})")
    
    conn.commit()
    conn.close()
    
    print(f"\nSaved {saved} jockey statistics")


if __name__ == "__main__":
    save_to_db()