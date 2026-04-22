#!/usr/bin/env python3
"""
Import race cards from CSV file.
Usage: python import_race_cards_csv.py <csv_file>
"""

import sys
import os
import csv
import sqlite3
from datetime import datetime

def import_race_cards(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'hkjc_races.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    imported = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                race_date = row.get('race_date', '').strip()
                race_number = int(row.get('race_number', 0))
                racecourse = row.get('racecourse', 'ST').strip()
                horse_number = int(row.get('horse_number', 0))
                horse_name = row.get('horse_name', '').strip()
                jockey = row.get('jockey', '').strip()
                trainer = row.get('trainer', '').strip()
                weight = row.get('weight', '').strip()
                draw = int(row.get('draw', 0)) if row.get('draw') else 0
                
                if not race_date or not horse_name:
                    print(f"  Skipping: missing date or name")
                    continue
                
                # Check if exists
                cursor.execute("""
                    SELECT id FROM future_race_cards 
                    WHERE race_date = ? AND race_number = ? AND racecourse = ? AND horse_number = ?
                """, (race_date, race_number, racecourse, horse_number))
                
                existing = cursor.fetchone()
                scraped_at = datetime.now().isoformat()
                
                if existing:
                    cursor.execute("""
                        UPDATE future_race_cards SET
                        horse_name = ?, jockey = ?, trainer = ?, weight = ?, draw = ?, scraped_at = ?
                        WHERE id = ?
                    """, (horse_name, jockey, trainer, weight, draw, scraped_at, existing[0]))
                else:
                    cursor.execute("""
                        INSERT INTO future_race_cards (
                            race_date, race_number, racecourse, horse_number, horse_name,
                            jockey, trainer, weight, draw, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (race_date, race_number, racecourse, horse_number, horse_name,
                          jockey, trainer, weight, draw, scraped_at))
                
                imported += 1
                
            except Exception as e:
                errors += 1
                print(f"  Error: {e}")
                continue
    
    conn.commit()
    conn.close()
    
    print(f"\nDone! Imported: {imported}, Errors: {errors}")
    return imported


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_race_cards_csv.py <csv_file>")
        print("\nCSV Format:")
        print("  race_date,race_number,racecourse,horse_number,horse_name,jockey,trainer,weight,draw")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    import_race_cards(csv_file)