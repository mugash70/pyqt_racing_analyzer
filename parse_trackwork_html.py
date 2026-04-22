#!/usr/bin/env python3
"""
Parse and save trackwork data for 2026-04-22 Race 9 HV.
"""

import sqlite3
import os
from datetime import datetime

# Trackwork data from Race 9
RACE_DATE = "2026-04-22"
RACE_NUMBER = 9
RACECOURSE = "HV"

TRACKWORK_DATA = [
    {"horse_number": 1, "horse_name": "Zhi Man Tong Xing", "trainer": "Wen Jialiang", "recent": "1/4/4/2/1/2"},
    {"horse_number": 2, "horse_name": "True Legend", "trainer": "John Tsai", "recent": "10/8/7/5/6/8"},
    {"horse_number": 3, "horse_name": "好好戀愛", "trainer": "方嘉柏", "recent": "7/8/3/1/6/2"},
    {"horse_number": 4, "horse_name": "好節拍", "trainer": "沈集成", "recent": "1/1/10/2/8/1"},
    {"horse_number": 5, "horse_name": "非凡豪傑", "trainer": "巫偉傑", "recent": "10/7/10/2/2/10"},
    {"horse_number": 6, "horse_name": "粵港資駒", "trainer": "游達榮", "recent": "2/5/1/8/9"},
    {"horse_number": 7, "horse_name": "金牌活力", "trainer": "桂福特", "recent": "8/8/1/12/6/6"},
    {"horse_number": 8, "horse_name": "多威心得", "trainer": "大衛希斯", "recent": "11"},
    {"horse_number": 9, "horse_name": "快活英雄", "trainer": "黎昭昇", "recent": "4/1/4/10/8/1"},
    {"horse_number": 10, "horse_name": "撼天鐵翼", "trainer": "韋達", "recent": "7/5/6/7/6/8"},
    {"horse_number": 11, "horse_name": "御登", "trainer": "告東尼", "recent": ""},
    {"horse_number": 12, "horse_name": "包裝明將", "trainer": "姚本輝", "recent": "5/3/3/2/5/1"},
    # Reserve
    {"horse_number": 13, "horse_name": "喵喵怪", "trainer": "巫偉傑", "recent": "3/3/2/2/9/2"},
]


def save_trackwork():
    """Save trackwork to database."""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    scraped_at = datetime.now().isoformat()
    saved = 0
    
    for horse in TRACKWORK_DATA:
        # Check if exists
        cursor.execute("""
            SELECT id FROM detailed_trackwork 
            WHERE race_date = ? AND racecourse = ? AND race_number = ? AND horse_number = ?
        """, (RACE_DATE, RACECOURSE, RACE_NUMBER, str(horse['horse_number'])))
        
        existing = cursor.fetchone()
        
        # Combine info into remarks
        remarks = f"Trainer: {horse['trainer']} | Recent: {horse['recent']}"
        
        if existing:
            cursor.execute("""
                UPDATE detailed_trackwork SET
                horse_name = ?, remarks = ?, scraped_at = ?
                WHERE id = ?
            """, (horse['horse_name'], remarks, scraped_at, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO detailed_trackwork (
                    race_date, racecourse, race_number, horse_number,
                    horse_name, remarks, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (RACE_DATE, RACECOURSE, RACE_NUMBER, str(horse['horse_number']),
                  horse['horse_name'], remarks, scraped_at))
        
        saved += 1
        print(f"  #{horse['horse_number']}: {horse['horse_name']} ({horse['trainer']})")
    
    conn.commit()
    conn.close()
    
    print(f"\nSaved {saved} trackwork records for {RACE_DATE} R{RACE_NUMBER} ({RACECOURSE})")


if __name__ == "__main__":
    save_trackwork()