"""Live odds monitoring (5-second updates)."""

from typing import Dict, List
import threading
import time
from datetime import datetime
from ..core.data_integrator import DataIntegrator


class OddsMonitor:
    """Monitors live odds with 5-second update cycle."""
    
    def __init__(self, data_integrator: DataIntegrator):
        """Initialize odds monitor."""
        self.data = data_integrator
        self.monitoring = False
        self.update_thread = None
        self.callbacks = []
        self.current_odds = {}
    
    def start_monitoring(self, race_date: str, race_number: int, 
                        track: str, callback=None) -> None:
        """Start monitoring odds for a race."""
        self.monitoring = True
        
        if callback:
            self.callbacks.append(callback)
        
        self.update_thread = threading.Thread(
            target=self._monitor_loop,
            args=(race_date, race_number, track),
            daemon=True
        )
        self.update_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.monitoring = False
    
    def _monitor_loop(self, race_date: str, race_number: int, track: str) -> None:
        """Main monitoring loop (5-second updates)."""
        while self.monitoring:
            try:
                odds_data = self.data.get_live_odds(race_date, race_number, track)
                
                for odds in odds_data:
                    horse_number = str(odds['number'])
                    current_odds = odds['win_odds']
                    
                    if horse_number not in self.current_odds:
                        self.current_odds[horse_number] = {
                            'initial_odds': current_odds,
                            'current_odds': current_odds,
                            'history': [current_odds],
                            'timestamp': datetime.now()
                        }
                    else:
                        prev_odds = self.current_odds[horse_number]['current_odds']
                        self.current_odds[horse_number]['current_odds'] = current_odds
                        self.current_odds[horse_number]['history'].append(current_odds)
                        self.current_odds[horse_number]['timestamp'] = datetime.now()
                
                for callback in self.callbacks:
                    try:
                        callback(self.current_odds)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                time.sleep(5)
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def get_odds_movement(self, horse_number: str) -> Dict:
        """Get odds movement for a horse."""
        if horse_number not in self.current_odds:
            return {'status': 'Not tracking'}
        
        data = self.current_odds[horse_number]
        initial = data['initial_odds']
        current = data['current_odds']
        
        if initial > 0:
            movement_pct = ((current - initial) / initial) * 100
        else:
            movement_pct = 0
        
        return {
            'horse_number': horse_number,
            'initial_odds': initial,
            'current_odds': current,
            'movement_percentage': movement_pct,
            'trend': 'shortening' if movement_pct < 0 else 'lengthening',
            'history': data['history'][-10:],
            'timestamp': data['timestamp'].isoformat()
        }
    
    def get_all_odds_movements(self) -> List[Dict]:
        """Get movements for all tracked horses."""
        movements = []
        for horse_number in self.current_odds.keys():
            movements.append(self.get_odds_movement(horse_number))
        return movements
    
    def detect_smart_money(self, threshold_pct: float = 10.0) -> List[Dict]:
        """Detect smart money patterns."""
        smart_money = []
        
        for horse_number, data in self.current_odds.items():
            movement = self.get_odds_movement(horse_number)
            
            if abs(movement['movement_percentage']) > threshold_pct:
                smart_money.append({
                    'horse_number': horse_number,
                    'direction': 'backed' if movement['movement_percentage'] < 0 else 'laid',
                    'movement': movement['movement_percentage'],
                    'current_odds': movement['current_odds']
                })
        
        smart_money.sort(key=lambda x: abs(x['movement']), reverse=True)
        return smart_money
    
    def calculate_market_velocity(self, horse_number: str, window: int = 3) -> float:
        """Calculate rate of odds change."""
        if horse_number not in self.current_odds:
            return 0.0
        
        history = self.current_odds[horse_number]['history']
        
        if len(history) < window:
            return 0.0
        
        recent = history[-window:]
        velocity = (recent[-1] - recent[0]) / max(1, len(recent) - 1)
        
        return float(velocity)
