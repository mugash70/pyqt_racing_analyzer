#!/usr/bin/env python3
"""
Import race cards from raw HTML text copied from HKJC website.
Usage: paste the HTML from the website into this script.
"""

import re
import sqlite3
import os
from datetime import datetime

RACE_DATE = "2026-04-22"
RACE_NUMBER = 2
RACECOURSE = "HV"  # Happy Valley

# Horse data extracted from HKJC HTML
HORSES_DATA = [
    {"number": 1, "name": "Lucky Star", "trainer": "Wu Weijie", "jockey": "", "weight": "", "draw": 0},
    {"number": 2, "name": "Divine Steed", "trainer": "Liao Kangming", "jockey": "", "weight": "", "draw": 0},
    {"number": 3, "name": "魅力知福", "trainer": "蔡約翰", "jockey": "", "weight": "", "draw": 0},
    {"number": 4, "name": "電訊驕陽", "trainer": "徐雨石", "jockey": "", "weight": "", "draw": 0},
    {"number": 5, "name": "神燦金剛", "trainer": "葉楚航", "jockey": "", "weight": "", "draw": 0},
    {"number": 6, "name": "東方寶寶", "trainer": "姚本輝", "jockey": "", "weight": "", "draw": 0},
    {"number": 7, "name": "焦點", "trainer": "游達榮", "jockey": "", "weight": "", "draw": 0},
    {"number": 8, "name": "朗日雪峰", "trainer": "方嘉柏", "jockey": "", "weight": "", "draw": 0},
    {"number": 9, "name": "飛躍凱旋", "trainer": "桂福特", "jockey": "", "weight": "", "draw": 0},
    {"number": 10, "name": "美麗歡聲", "trainer": "告東尼", "jockey": "", "weight": "", "draw": 0},
    {"number": 11, "name": "風雲", "trainer": "丁冠豪", "jockey": "", "weight": "", "draw": 0},
    {"number": 12, "name": "領航傳祺", "trainer": "鄭俊偉", "jockey": "", "weight": "", "draw": 0},
    # Reserve horses
    {"number": 13, "name": "東方魅影", "trainer": "大衛希斯", "jockey": "", "weight": "", "draw": 0},
    {"number": 14, "name": "手到再來", "trainer": "伍鵬志", "jockey": "", "weight": "", "draw": 0},
]


def import_horses():
    """Import horses into database."""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    saved = 0
    for horse in HORSES_DATA:
        horse_number = horse['number']
        horse_name = horse['name']
        trainer = horse['trainer']
        
        # Check if exists
        cursor.execute("""
            SELECT id FROM future_race_cards 
            WHERE race_date = ? AND race_number = ? AND racecourse = ? AND horse_number = ?
        """, (RACE_DATE, RACE_NUMBER, RACECOURSE, horse_number))
        
        existing = cursor.fetchone()
        scraped_at = datetime.now().isoformat()
        
        if existing:
            cursor.execute("""
                UPDATE future_race_cards SET
                horse_name = ?, trainer = ?, scraped_at = ?
                WHERE id = ?
            """, (horse_name, trainer, scraped_at, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO future_race_cards (
                    race_date, race_number, racecourse, horse_number, horse_name,
                    trainer, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (RACE_DATE, RACE_NUMBER, RACECOURSE, horse_number, horse_name, trainer, scraped_at))
        
        saved += 1
        print(f"  #{horse_number}: {horse_name} ({trainer})")
    
    conn.commit()
    conn.close()
    
    print(f"\nImported {saved} horses for {RACE_DATE} R{RACE_NUMBER} ({RACECOURSE})")


if __name__ == "__main__":
    import_horses()