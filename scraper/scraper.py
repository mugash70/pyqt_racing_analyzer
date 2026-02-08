import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import re
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class HKJCResultsScraper:
    """Scraper for HKJC racing information."""
    
    BASE_URL = "https://racing.hkjc.com/zh-hk/local/information"
    INFO_URL = "https://racing.hkjc.com/zh-hk/local/info"
    PAGE_URL = "https://racing.hkjc.com/zh-hk/local/page"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None

    def _get_driver(self):
        """Initialize headless Chrome driver."""
        if self.driver:
            return self.driver
            
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Use webdriver-manager to handle driver versions automatically
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
                
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {e}")
            # Fallback to default initialization if webdriver-manager fails
            try:
                self.driver = webdriver.Chrome(options=options)
                return self.driver
            except Exception as e2:
                logger.error(f"Fallback Selenium initialization failed: {e2}")
                return None

    def close(self):
        """Close the Selenium driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_available_dates(self) -> List[datetime]:
        """Fetch available race dates."""
        url = f"{self.BASE_URL}/localresults"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Logic to parse dates from dropdown or links
            return []
        except Exception as e:
            logger.error(f"Error fetching available dates: {e}")
            return []

    def scrape_trainer_king_odds(self, race_date: str) -> List[Dict]:
        """Scrape Trainer King Odds Chart using Selenium for JavaScript-rendered content."""
        url = f"{self.PAGE_URL}/tnc-odds-chart"
        odds_data = []
        
        try:
            driver = self._get_driver()
            if not driver:
                logger.error("Failed to initialize Selenium driver")
                return []
            
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            
            # Get the rendered HTML
            html = driver.page_source
            
            # Look for WinnerList JSON in the HTML
            # The data is embedded in Next.js script chunks with escaped JSON
            winner_list = None
            
            def extract_winner_list(text):
                """Extract WinnerList array from text using bracket counting."""
                start = text.find('"WinnerList":')
                if start < 0:
                    return None
                
                # Find the opening bracket
                bracket_start = text.find('[', start)
                if bracket_start < 0:
                    return None
                
                # Count brackets to find the matching closing bracket
                count = 1
                i = bracket_start + 1
                while i < len(text) and count > 0:
                    if text[i] == '[':
                        count += 1
                    elif text[i] == ']':
                        count -= 1
                    i += 1
                
                if count == 0:
                    json_str = text[bracket_start:i]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                return None
            
            # First, try to find directly in HTML
            winner_list = extract_winner_list(html)
            
            # If not found, try extracting from Next.js script chunks
            if not winner_list:
                # Find all script chunks that might contain the data
                script_pattern = r'self\.__next_f\.push\(\[\d+,\s*"([\s\S]*?)"\s*\]\)'
                scripts = re.findall(script_pattern, html, re.DOTALL)
                
                for script_content in scripts:
                    # Unescape the JSON string
                    try:
                        # Replace escaped quotes and newlines
                        unescaped = script_content.replace('\\"', '"').replace('\\n', '\n').replace('\\r', '').replace('\\\\', '\\')
                        winner_list = extract_winner_list(unescaped)
                        if winner_list:
                            break
                    except Exception:
                        continue
            
            if winner_list:
                try:
                    for winner in winner_list:
                        trainer_info = winner.get('Winner', {})
                        if trainer_info:
                            trainer_name = trainer_info.get('Name', '')
                            # Get the latest valid odds from OddsTrend
                            odds_trend = winner.get('OddsTrend', [])
                            latest_odds = None
                            for odd in reversed(odds_trend):
                                if odd and odd.get('Odds', -1) > 0:
                                    latest_odds = odd['Odds']
                                    break
                            
                            if trainer_name and latest_odds:
                                odds_data.append({
                                    'trainer': trainer_name,
                                    'odds': float(latest_odds),
                                    'trend': winner.get('Venue', ''),
                                    'meeting_date': winner.get('MeetingDate', ''),
                                    'points': winner.get('Point', 0)
                                })
                    logger.info(f"Successfully scraped {len(odds_data)} trainer king odds records")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Error parsing TNC JSON data: {e}")
            else:
                logger.warning("WinnerList JSON not found in HTML")
                
        except Exception as e:
            logger.error(f"Error scraping trainer king odds: {e}")
        
        return odds_data

    def scrape_race_day_changes(self, race_date: str) -> List[Dict]:
        """Scrape Changes & Information (更易事項) using Selenium."""
        url = f"{self.INFO_URL}/changes"
        changes = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            import time
            time.sleep(3)  # Wait for dynamic content
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        race_text = cols[0].text.strip()
                        details = cols[1].text.strip()
                        race_no = re.search(r'\d+', race_text)
                        
                        if details and details != '--':
                            changes.append({
                                'race_number': int(race_no.group()) if race_no else None,
                                'details': details
                            })
            
            return changes
        except Exception as e:
            logger.error(f"Error scraping race day changes: {e}")
            return []

    def scrape_track_selection(self, race_date: str) -> Dict:
        """Scrape Track Selection Data."""
        url = f"{self.PAGE_URL}/racing-course-select?RaceDate={race_date.replace('-', '')}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract track type and setting
            title = soup.find('div', {'class': 'race_course_title'})
            track_info = title.text.strip() if title else ""
            
            return {
                'racecourse': 'ST' if '沙田' in track_info else 'HV',
                'track_type': 'Turf' if '草地' in track_info else 'AWT',
                'course_setting': re.search(r'([A-C]\+?\d?)', track_info).group(0) if re.search(r'([A-C]\+?\d?)', track_info) else "",
                'stats': track_info
            }
        except Exception as e:
            logger.error(f"Error scraping track selection: {e}")
            return {}

    def _normalize_date_format(self, race_date: str) -> str:
        """Normalize date to YYYY/MM/DD format used by HKJC URLs."""
        try:
            # Handle YYYY-MM-DD or other common formats
            dt = datetime.strptime(race_date.replace('/', '-'), '%Y-%m-%d')
            return dt.strftime('%Y/%m/%d')
        except ValueError:
            return race_date

    def scrape_race_card(self, race_date: str, race_number: int = 1, racecourse: str = "ST", max_retries: int = 2) -> List[Dict]:
        """Scrape Race Card trying requests first, then Selenium if needed."""
        norm_date = self._normalize_date_format(race_date)
        url = f"{self.BASE_URL}/racecard?racedate={norm_date}&Racecourse={racecourse}&RaceNo={race_number}"
        logger.info(f"Scraping race card from {url}")
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try multiple strategies to find the race card table
                table = self._find_race_card_table(soup)
                
                if table:
                    data = self._parse_race_card_soup(soup, race_date, race_number, racecourse, table)
                    if data:
                        logger.info(f"Successfully scraped race card with {len(data)} horses using requests")
                        return data
                
                logger.info(f"Table not found or empty with requests (attempt {attempt + 1}), trying Selenium fallback")
                data = self._scrape_race_card_selenium(url, race_date, race_number, racecourse)
                if data:
                    return data
                    
            except Exception as e:
                logger.error(f"Error scraping race card with requests (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        # Final fallback to Selenium
        return self._scrape_race_card_selenium(url, race_date, race_number, racecourse)
    
    def _find_race_card_table(self, soup: BeautifulSoup) -> Optional[Any]:
        """Find the race card table using multiple strategies."""
        # Strategy 1: Look for tables with specific headers
        header_keywords = ['馬名', 'Horse', '馬匹', '馬號', 'No.', 'Number']
        for t in soup.find_all('table'):
            header_row = t.find('tr')
            if header_row:
                header_text = header_row.get_text()
                if any(h in header_text for h in header_keywords):
                    return t
        
        # Strategy 2: Look for tables with horse number patterns in cells
        for t in soup.find_all('table'):
            rows = t.find_all('tr')
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 3:
                    first_col_text = cols[0].text.strip()
                    # Check if first column looks like a horse number
                    if re.match(r'^\d+$', first_col_text):
                        second_col_text = cols[1].text.strip()
                        # Check if second column looks like a horse name
                        if len(second_col_text) > 1 and not second_col_text.isdigit():
                            return t
        
        # Strategy 3: Look for table with specific CSS classes
        for class_name in ['table_bd', 'racecard', 'starter', 'table', 'race_table']:
            table = soup.find('table', {'class': re.compile(class_name, re.I)})
            if table:
                return table
        
        # Strategy 4: Find the largest table (race cards are usually large)
        tables = soup.find_all('table')
        if tables:
            largest_table = max(tables, key=lambda t: len(t.find_all('tr')))
            if len(largest_table.find_all('tr')) > 3:  # Must have more than just header
                return largest_table
        
        return None

    def _scrape_race_card_selenium(self, url: str, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Fallback Selenium scraper for race card."""
        driver = self._get_driver()
        if not driver:
            return []
        try:
            driver.get(url)
            # Increased timeout and wait for common race card element
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table, div.race_tab")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            table = None
            for t in soup.find_all('table'):
                if any(h in t.text for h in ['馬名', 'Horse', '馬匹']):
                    table = t
                    break
                    
            return self._parse_race_card_soup(soup, race_date, race_number, racecourse, table)
        except Exception as e:
            logger.error(f"Selenium fallback failed for race card: {e}")
            return []

    def _parse_race_card_soup(self, soup: BeautifulSoup, race_date: str, race_number: int, racecourse: str = "ST", table=None) -> List[Dict]:
        """Common parser for race card BeautifulSoup object with dynamic index detection."""
        # Extract race info
        race_info_text = ""
        # Try different possible containers for race info
        info_containers = [
            soup.find('div', {'class': 'race_tab'}),
            soup.find('div', {'class': 'race_info'}),
            soup.find('div', {'class': 'f_fs13'}),
            soup.find('div', {'class': 'margin_top10'})
        ]
        for container in info_containers:
            if container and ('米' in container.text or 'M' in container.text):
                race_info_text += " " + container.get_text()
        
        if not race_info_text:
            # Try finding by general structure
            info_divs = soup.find_all('div', class_=re.compile(r'race_info|race_tab|f_fs13'))
            for div in info_divs:
                if '米' in div.text or 'M' in div.text:
                    race_info_text += " " + div.get_text()

        distance_match = re.search(r'(\d+米|\d+M)', race_info_text)
        distance = distance_match.group(1) if distance_match else ""
        
        class_match = re.search(r'(第[一二三四五]班|Class [1-5]|新馬|G[1-3]|讓賽)', race_info_text)
        race_class = class_match.group(1) if class_match else ""

        going_match = re.search(r'(好地|快地|稍慢|黏地|軟地|爛地|GOOD|FIRM|YIELDING|SOFT|HEAVY|AWT)', race_info_text.upper())
        going = going_match.group(1) if going_match else ""
        
        horse_data = []
        if not table:
            table = soup.find('table', {'class': 'table_bd'}) or soup.find('table', class_=re.compile(r'starter|racecard'))
            
        if not table:
            return []

        rows = table.find_all('tr')
        if not rows:
            return []

        # Find header row and map indices
        header_idx = {}
        for row in rows:
            cols = row.find_all(['th', 'td'])
            text_cols = [c.text.strip() for c in cols]
            if any(h in text_cols for h in ['馬匹編號', '馬名', 'Horse', 'No.', '馬號']):
                for i, text in enumerate(text_cols):
                    if any(h in text for h in ['編號', 'No.', '馬號']): header_idx['number'] = i
                    elif any(h in text for h in ['馬名', 'Horse']): header_idx['name'] = i
                    elif any(h in text for h in ['騎師', 'Jockey']): header_idx['jockey'] = i
                    elif any(h in text for h in ['練馬師', 'Trainer']): header_idx['trainer'] = i
                    elif any(h in text for h in ['負磅', 'Weight']): header_idx['weight'] = i
                    elif any(h in text for h in ['檔位', 'Draw']): header_idx['draw'] = i
                break
        
        # Default indices if header not found or incomplete
        if 'number' not in header_idx: header_idx['number'] = 0
        if 'name' not in header_idx: 
            # Heuristic for name column
            for i, row in enumerate(rows):
                cols = row.find_all('td')
                if len(cols) > 2:
                    # Check if col 1 or 2 looks like a horse name (contains Chinese characters or letters)
                    for idx in [1, 2, 3]:
                        if idx < len(cols) and re.search(r'[\u4e00-\u9fff]|[a-zA-Z]', cols[idx].text):
                            header_idx['name'] = idx
                            break
                    if 'name' in header_idx: break
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 3:
                continue
            
            try:
                horse_num_text = cols[header_idx.get('number', 0)].text.strip()
                # Remove non-digits for number
                horse_num_text = re.sub(r'\D', '', horse_num_text)
                if not horse_num_text:
                    continue
                
                horse_name = cols[header_idx.get('name', 2)].text.strip()
                # Skip if name looks like a header or is empty
                if horse_name in ['馬名', 'Horse', ''] or len(horse_name) < 2:
                    continue
                
                horse_data.append({
                    'race_date': race_date,
                    'race_number': race_number,
                    'racecourse': racecourse,
                    'horse_number': int(horse_num_text),
                    'horse_name': horse_name,
                    'jockey': cols[header_idx.get('jockey', 3)].text.strip() if 'jockey' in header_idx and header_idx['jockey'] < len(cols) else "",
                    'trainer': cols[header_idx.get('trainer', 4)].text.strip() if 'trainer' in header_idx and header_idx['trainer'] < len(cols) else "",
                    'weight': cols[header_idx.get('weight', 5)].text.strip() if 'weight' in header_idx and header_idx['weight'] < len(cols) else "",
                    'draw': int(re.sub(r'\D', '', cols[header_idx['draw']].text.strip())) if 'draw' in header_idx and header_idx['draw'] < len(cols) and re.sub(r'\D', '', cols[header_idx['draw']].text.strip()) else 0,
                    'race_distance': distance,
                    'race_class': race_class,
                    'track_going': going,
                    'scraped_at': datetime.now().isoformat()
                })
            except (ValueError, IndexError, KeyError):
                continue
                
        return horse_data

    def scrape_results(self, race_date: str, race_number: int = 1, racecourse: str = "ST") -> List[Dict]:
        """Scrape Local Results."""
        norm_date = self._normalize_date_format(race_date)
        url = f"{self.BASE_URL}/localresults?racedate={norm_date}&Racecourse={racecourse}&RaceNo={race_number}"
        logger.info(f"Scraping results from {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the correct table by looking for headers
            table = None
            for t in soup.find_all('table'):
                header_row = t.find('tr')
                if header_row and any(h in header_row.text for h in ['名次', 'Pos', 'Pos.']):
                    table = t
                    break
            return self._parse_results_soup(soup, race_date, race_number, racecourse, table)
        except Exception as e:
            logger.error(f"Error scraping results: {e}")
            return []

    def _parse_results_soup(self, soup: BeautifulSoup, race_date: str, race_number: int, racecourse: str, table=None) -> List[Dict]:
        """Parse results page with robust detection."""
        results = []
        if not table:
            table = soup.find('table', {'class': 'table_bd'})
            
        if not table:
            return []
            
        rows = table.find_all('tr')
        header_idx = {}
        for row in rows:
            cols = row.find_all(['th', 'td'])
            text_cols = [c.text.strip() for c in cols]
            if any(h in text_cols for h in ['名次', 'Pos', '馬匹', 'Horse']):
                for i, text in enumerate(text_cols):
                    if any(h in text for h in ['名次', 'Pos']): header_idx['pos'] = i
                    elif any(h in text for h in ['馬號', 'No.']): header_idx['number'] = i
                    elif any(h in text for h in ['馬匹', 'Horse']): header_idx['name'] = i
                    elif any(h in text for h in ['騎師', 'Jockey']): header_idx['jockey'] = i
                    elif any(h in text for h in ['練馬師', 'Trainer']): header_idx['trainer'] = i
                    elif any(h in text for h in ['完成時間', 'Finish Time', 'Time']): header_idx['time'] = i
                break

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue
            
            try:
                pos = cols[header_idx.get('pos', 0)].text.strip()
                if not pos or pos in ['名次', 'Pos']: continue
                
                horse_num = cols[header_idx.get('number', 1)].text.strip()
                horse_name = cols[header_idx.get('name', 2)].text.strip()
                
                # Try to extract weight if available
                actual_weight = ""
                if 'weight' in header_idx and header_idx['weight'] < len(cols):
                    actual_weight = cols[header_idx['weight']].text.strip()
                
                # Try to extract draw if available
                draw = 0
                if 'draw' in header_idx and header_idx['draw'] < len(cols):
                    draw_text = re.sub(r'\D', '', cols[header_idx['draw']].text.strip())
                    draw = int(draw_text) if draw_text else 0
                
                results.append({
                    'race_date': race_date,
                    'race_number': race_number,
                    'racecourse': racecourse,
                    'position': pos,
                    'horse_number': int(re.sub(r'\D', '', horse_num)) if re.sub(r'\D', '', horse_num) else 0,
                    'horse_name': horse_name,
                    'jockey': cols[header_idx['jockey']].text.strip() if 'jockey' in header_idx else "",
                    'trainer': cols[header_idx['trainer']].text.strip() if 'trainer' in header_idx else "",
                    'actual_weight': actual_weight,
                    'draw': draw,
                    'finish_time': cols[header_idx['time']].text.strip() if 'time' in header_idx else "",
                    'win_odds': 0.0,
                    'scraped_at': datetime.now().isoformat()
                })
            except Exception:
                continue
        return results

    def scrape_morning_trackwork(self, race_date: str) -> List[Dict]:
        """Scrape Morning Exercise Data."""
        norm_date = self._normalize_date_format(race_date)
        url = f"{self.BASE_URL}/localtrackwork?racedate={norm_date}"
        logger.info(f"Scraping morning trackwork from {url}")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            trackwork = []
            table = soup.find('table', {'class': 'table_bd'})
            if table:
                rows = table.find_all('tr')[1:] # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        trackwork.append({
                            'race_date': race_date,
                            'horse_name': cols[0].text.strip(),
                            'date': cols[1].text.strip(),
                            'track': cols[2].text.strip(),
                            'work': cols[3].text.strip(),
                            'time': cols[4].text.strip(),
                            'scraped_at': datetime.now().isoformat()
                        })
            return trackwork
        except Exception as e:
            logger.error(f"Error scraping morning trackwork: {e}")
            return []

    def scrape_race_reports(self, race_date: str) -> List[Dict]:
        """Scrape Race Reports."""
        norm_date = self._normalize_date_format(race_date)
        url = f"{self.BASE_URL}/racereportfull?racedate={norm_date}"
        logger.info(f"Scraping race reports from {url}")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            reports = []
            # Race reports are often in divs or tables per race
            report_sections = soup.find_all('div', {'class': 'race_report'}) or soup.find_all('table', {'class': 'table_bd'})
            for idx, section in enumerate(report_sections, 1):
                reports.append({
                    'race_date': race_date,
                    'race_number': idx,
                    'report_text': section.get_text(strip=True),
                    'scraped_at': datetime.now().isoformat()
                })
            return reports
        except Exception as e:
            logger.error(f"Error scraping race reports: {e}")
            return []

    def scrape_professional_schedules(self, pro_type: str, race_date: str) -> List[Dict]:
        """Scrape Jockey or Trainer schedules."""
        norm_date = self._normalize_date_format(race_date)
        if pro_type == 'jockey':
            url = f"{self.INFO_URL}/jockeys-rides?racedate={norm_date}"
        else:
            url = f"{self.INFO_URL}/trainers-entries?racedate={norm_date}"

        logger.info(f"Scraping {pro_type} schedules from {url}")
        schedules = []

        try:
            # 使用Selenium确保页面动态内容加载
            driver = self._get_driver()
            if not driver:
                return []
            driver.get(url)
            time.sleep(3)  # 等待页面加载

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 针对不同页面类型使用不同的表格选择器
            if pro_type == 'jockey':
                # 骑师页面使用不同的表格ID和类
                table = soup.find('table', class_='table_bd')
                if not table:
                    table = soup.find('table', {'style': 'width: 100%; line-height: 120%; border: 1px solid black;'})
            else:
                # 练马师页面使用不同的表格ID
                table = soup.find('table', {'id': 'trainersInfo'})
                if not table:
                    table = soup.find('table', class_='col_12')

            if not table:
                logger.warning(f"Could not find {pro_type} schedule table on page")
                return schedules

            # 提取表头，确定比赛场次
            thead = table.find('thead')
            if not thead:
                return schedules

            # 从表头行提取比赛场次
            header_rows = thead.find_all('tr')
            if len(header_rows) < 2:
                return schedules

            # 第二行通常包含比赛场次信息（第一行是标题）
            race_header_row = header_rows[0]
            race_headers = race_header_row.find_all(['th', 'td'])
            
            # 过滤出包含比赛场次的列
            race_numbers = []
            for header in race_headers:
                text = header.text.strip()
                # 检查是否包含比赛相关的关键词
                if any(keyword in text for keyword in ['比賽', 'Match', 'Game', '賽事']):
                    race_numbers.append(text)
                elif text and text.replace(' ', '').isdigit():
                    race_numbers.append(f"Race {text}")
                elif 'R' in text and text.replace('R', '').isdigit():
                    # 处理 "R1", "R2" 等格式
                    race_numbers.append(f"Race {text.replace('R', '')}")

            # 如果没有提取到，根据列数推断
            if not race_numbers:
                # 计算除了前两列（姓名和统计数据）之外的列数
                first_data_row = table.find('tbody').find('tr') if table.find('tbody') else None
                if first_data_row:
                    cols = first_data_row.find_all(['td', 'th'])
                    if len(cols) > 2:
                        race_numbers = [f"Race {i+1}" for i in range(len(cols) - 2)]

            # 提取数据行
            tbody = table.find('tbody')
            if not tbody:
                return schedules

            rows = tbody.find_all('tr')

            for row in rows:
                # 跳过标题行或统计行
                if 'tdBgYellow' in str(row) or 'bg_h' in str(row) or 'tdAlignC' not in str(row):
                    continue

                # 提取专业人员姓名
                name_cell = row.find('td')
                if not name_cell:
                    continue

                name_link = name_cell.find('a')
                if name_link:
                    professional_name = name_link.text.strip()
                else:
                    # 如果没有链接，直接取文本
                    professional_name = name_cell.text.strip()

                if not professional_name:
                    continue

                # 提取本赛季数据
                stats_cell = name_cell.find_next_sibling('td')
                stats = []
                if stats_cell:
                    # 查找包含统计数字的div
                    stats_divs = stats_cell.find_all('div', class_='tdAlignVC')
                    if stats_divs:
                        stats = [div.text.strip() for div in stats_divs if div.text.strip()]
                    else:
                        # 如果没有特定的div，尝试从文本中提取数字
                        text = stats_cell.get_text(separator=' ', strip=True)
                        # 使用正则表达式提取数字
                        import re
                        numbers = re.findall(r'\d+', text)
                        stats = numbers[:4]  # 取前4个数字

                # 提取每个比赛场次的马匹信息
                # 跳过前两个td(姓名和统计)
                race_cells = row.find_all('td')[2:]

                for i, race_cell in enumerate(race_cells):
                    # 如果已经超出比赛场次数，则停止
                    if i >= len(race_numbers):
                        break

                    race_num = race_numbers[i] if i < len(race_numbers) else f"Race {i+1}"

                    # 检查单元格是否有内容
                    cell_text = race_cell.text.strip()
                    if not cell_text:
                        continue

                    # 查找所有div（可能一个单元格中有多匹马）
                    horse_divs = race_cell.find_all('div')
                    
                    if not horse_divs:
                        # 如果没有div，尝试直接解析文本
                        if '退出' in cell_text or 'Exit' in cell_text or '退賽' in cell_text:
                            continue
                        
                        # 简单的文本格式，可能是赔率和马名在同一行
                        horse_name = cell_text
                        odds = ""
                        
                        # 创建记录
                        schedule_record = {
                            'race_date': race_date,
                            'professional_name': professional_name,
                            'professional_type': pro_type,
                            'race_number': str(i+1),
                            'race_display': race_num,
                            'horse_name': horse_name,
                            'odds': odds,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        schedules.append(schedule_record)
                    else:
                        # 处理每个div（可能有多匹马）
                        for horse_div in horse_divs:
                            # 提取赔率
                            odds_span = horse_div.find('span', class_='color_red5')
                            odds = odds_span.text.strip() if odds_span else ""
                            
                            # 提取马匹名称
                            horse_link = horse_div.find('a')
                            if horse_link:
                                horse_name = horse_link.text.strip()
                            else:
                                # 如果没有链接，尝试从整个div文本中提取
                                all_text = horse_div.get_text(separator=' ', strip=True)
                                if odds:
                                    # 移除赔率部分
                                    horse_name = all_text.replace(odds, '').strip()
                                else:
                                    horse_name = all_text
                            
                            # 清理马名中的特殊字符
                            horse_name = horse_name.replace('+', '').replace('*', '').replace('2', '').replace('3', '').replace('4', '').strip()
                            
                            # 跳过空马名或退赛马匹
                            if not horse_name or '退出' in horse_name or 'Exit' in horse_name:
                                continue
                            
                            # 创建记录
                            schedule_record = {
                                'race_date': race_date,
                                'professional_name': professional_name,
                                'professional_type': pro_type,
                                'race_number': str(i+1),
                                'race_display': race_num,
                                'horse_name': horse_name,
                                'odds': odds,
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            # 如果有统计信息，加入记录
                            if stats:
                                stat_labels = ['wins', 'seconds', 'thirds', 'total_starts']
                                for j, stat in enumerate(stats[:4]):
                                    if j < len(stat_labels):
                                        schedule_record[stat_labels[j]] = stat
                            
                            schedules.append(schedule_record)

            logger.info(f"Successfully scraped {len(schedules)} {pro_type} schedule records")
            return schedules

        except Exception as e:
            logger.error(f"Error scraping {pro_type} schedules: {e}", exc_info=True)
            return []
    def scrape_jkc_stats(self) -> List[Dict]:
        """Scrape JKC (Jockey King) Statistics."""
        url = "https://racing.hkjc.com/racing/information/Chinese/Racing/JKCstat.aspx"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = []
            table = soup.find('table', {'class': 'table_bd'})
            if table:
                rows = table.find_all('tr')[2:]  # Skip header rows
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 13:
                        jockey_link = cols[0].find('a')
                        jockey_name = jockey_link.text.strip() if jockey_link else cols[0].text.strip()
                        
                        if jockey_name and '騎師' not in jockey_name:
                            points = []
                            for i in range(1, 11):
                                points.append(int(cols[i].text.strip()) if cols[i].text.strip().isdigit() else 0)
                            
                            avg_points = float(cols[11].text.strip()) if cols[11].text.strip() else 0.0
                            season_avg = float(cols[13].text.strip()) if len(cols) > 13 and cols[13].text.strip() else 0.0
                            
                            stats.append({
                                'race_date': datetime.now().strftime('%Y-%m-%d'),
                                'jockey': jockey_name,
                                'points': sum(points),
                                'rank': len(stats) + 1,
                                'scraped_at': datetime.now().isoformat()
                            })
            return stats
        except Exception as e:
            logger.error(f"Error scraping JKC stats: {e}")
            return []

    def scrape_jkc_odds_chart(self, season: str = "2025/26") -> List[Dict]:
        """Scrape JKC Odds Chart."""
        url = f"{self.PAGE_URL}/jkc-odds-chart?season={season}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            odds_data = []
            # Try to find chart container or table
            chart_div = soup.find('div', {'id': 'chartContainer'}) or soup.find('div', {'class': 'chart'})
            if chart_div:
                # Extract data from chart div if present
                return odds_data
            
            # Fallback: look for any table with odds data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            odds_data.append({
                                'jockey_name': cols[0].text.strip(),
                                'odds': cols[1].text.strip(),
                                'season': season,
                                'scraped_at': datetime.now().isoformat()
                            })
            
            return odds_data
        except Exception as e:
            logger.error(f"Error scraping JKC odds chart: {e}")
            return []

    def scrape_conghua_movement(self) -> List[Dict]:
        """Scrape Conghua Movement Records - Data is in PDF format."""
        url = f"{self.PAGE_URL}/conghua-movement-records"
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find PDF link
            pdf_link = soup.find('a', href=re.compile(r'\.pdf', re.I))
            if pdf_link:
                pdf_url = pdf_link.get('href', '')
                if pdf_url.startswith('/'):
                    pdf_url = f"https://racing.hkjc.com{pdf_url}"
                
                return [{
                    'source_type': 'pdf',
                    'pdf_url': pdf_url,
                    'description': 'Conghua movement records available as PDF',
                    'scraped_at': datetime.now().isoformat()
                }]
            
            return []
        except Exception as e:
            logger.error(f"Error scraping Conghua movement: {e}")
            return []

    def scrape_horse_ratings(self) -> List[Dict]:
        """Scrape Horse Ratings using Selenium."""
        # Try the ratings page with class view
        url = f"{self.BASE_URL}/latestonhorse"
        ratings = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all tables and look for one with horse data
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        # Check if first column looks like a horse name
                        first_col = cols[0].text.strip()
                        if first_col and len(first_col) > 1 and not first_col.startswith('馬'):
                            # Extract rating info
                            rating_data = {
                                'horse_name': first_col,
                                'details': cols[1].text.strip() if len(cols) > 1 else '',
                                'scraped_at': datetime.now().isoformat()
                            }
                            if len(cols) > 2:
                                rating_data['additional_info'] = cols[2].text.strip()
                            ratings.append(rating_data)
            
            return ratings
        except Exception as e:
            logger.error(f"Error scraping horse ratings: {e}")
            return []

    def scrape_detailed_trackwork(self, race_date: str, racecourse: str = "ST") -> List[Dict]:
        """Scrape detailed trackwork for all races (1-11)."""
        all_trackwork = []
        
        for race_no in range(1, 12):
            url = f"{self.BASE_URL}/localtrackwork?racedate={race_date}&racecourse={racecourse}&RaceNo={race_no}"
            try:
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', {'class': 'table_bd'})
                if table:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 6:
                            all_trackwork.append({
                                'race_date': race_date,
                                'racecourse': racecourse,
                                'race_number': race_no,
                                'horse_name': cols[0].text.strip(),
                                'horse_number': cols[1].text.strip(),
                                'trackwork_time': cols[2].text.strip(),
                                'distance': cols[3].text.strip(),
                                'track_condition': cols[4].text.strip(),
                                'remarks': cols[5].text.strip() if len(cols) > 5 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            except Exception as e:
                logger.error(f"Error scraping trackwork for race {race_no}: {e}")
                continue
                
        return all_trackwork

    def scrape_tnc_stats(self) -> List[Dict]:
        """Scrape TNC (Trainer King) Statistics."""
        url = "https://racing.hkjc.com/racing/information/Chinese/Racing/TNCstat.aspx"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = []
            table = soup.find('table', {'class': 'table_bd'})
            if table:
                rows = table.find_all('tr')[2:]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 13:
                        trainer_link = cols[0].find('a')
                        trainer_name = trainer_link.text.strip() if trainer_link else cols[0].text.strip()
                        
                        if trainer_name and '練馬師' not in trainer_name:
                            points = []
                            for i in range(1, 11):
                                points.append(int(cols[i].text.strip()) if cols[i].text.strip().isdigit() else 0)
                            
                            avg_points = float(cols[11].text.strip()) if cols[11].text.strip() else 0.0
                            season_avg = float(cols[13].text.strip()) if len(cols) > 13 and cols[13].text.strip() else 0.0
                            
                            stats.append({
                                'race_date': datetime.now().strftime('%Y-%m-%d'),
                                'trainer': trainer_name,
                                'points': sum(points),
                                'rank': len(stats) + 1,
                                'scraped_at': datetime.now().isoformat()
                            })
            return stats
        except Exception as e:
            logger.error(f"Error scraping TNC stats: {e}")
            return []

    def scrape_jockey_favourites(self) -> List[Dict]:
        """Scrape Jockey Favourites Statistics."""
        url = "https://racing.hkjc.com/racing/information/Chinese/Racing/JockeyFavourite.aspx"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = []
            table = soup.find('table', {'class': 'table_bd'}) or soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        jockey_link = cols[0].find('a')
                        jockey_name = jockey_link.text.strip() if jockey_link else cols[0].text.strip()
                        
                        if jockey_name and jockey_name not in ['騎師', 'Jockey', '位置', ''] and len(jockey_name) > 1:
                            def safe_int(text):
                                try:
                                    return int(text.strip())
                                except (ValueError, AttributeError):
                                    return 0
                                    
                            def safe_float(text):
                                try:
                                    return float(text.strip().replace('%', ''))
                                except (ValueError, AttributeError):
                                    return 0.0
                            
                            stats.append({
                                'jockey_name': jockey_name,
                                'fav_rides': safe_int(cols[1].text),
                                'fav_wins': safe_int(cols[2].text),
                                'fav_win_rate': safe_float(cols[3].text),
                                'fav_places': safe_int(cols[4].text),
                                'fav_place_rate': safe_float(cols[5].text),
                                'scraped_at': datetime.now().isoformat()
                            })
            return stats
        except Exception as e:
            logger.error(f"Error scraping jockey favourites: {e}")
            return []

    def scrape_trainer_favourites(self) -> List[Dict]:
        """Scrape Trainer Favourites Statistics."""
        url = "https://racing.hkjc.com/racing/information/Chinese/Racing/TrainerFavourite.aspx"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = []
            table = soup.find('table', {'class': 'table_bd'}) or soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        trainer_link = cols[0].find('a')
                        trainer_name = trainer_link.text.strip() if trainer_link else cols[0].text.strip()
                        
                        if trainer_name and trainer_name not in ['練馬師', 'Trainer', '位置', ''] and len(trainer_name) > 1:
                            def safe_int(text):
                                try:
                                    return int(text.strip())
                                except (ValueError, AttributeError):
                                    return 0
                                    
                            def safe_float(text):
                                try:
                                    return float(text.strip().replace('%', ''))
                                except (ValueError, AttributeError):
                                    return 0.0
                            
                            stats.append({
                                'trainer_name': trainer_name,
                                'fav_runs': safe_int(cols[1].text),
                                'fav_wins': safe_int(cols[2].text),
                                'fav_win_rate': safe_float(cols[3].text),
                                'fav_places': safe_int(cols[4].text),
                                'fav_place_rate': safe_float(cols[5].text),
                                'scraped_at': datetime.now().isoformat()
                            })
            return stats
        except Exception as e:
            logger.error(f"Error scraping trainer favourites: {e}")
            return []

    def scrape_standard_times(self) -> List[Dict]:
        """Scrape Standard Times using Selenium."""
        url = f"{self.PAGE_URL}/racing-course-time"
        times = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        first_col = cols[0].text.strip()
                        if first_col and first_col not in ['距離', 'Distance', '路程', '']:
                            times.append({
                                'distance': first_col,
                                'track_type': cols[1].text.strip() if len(cols) > 1 else '',
                                'standard_time': cols[2].text.strip() if len(cols) > 2 else '',
                                'record_time': cols[3].text.strip() if len(cols) > 3 else '',
                                'record_holder': cols[4].text.strip() if len(cols) > 4 else '',
                                'record_date': cols[5].text.strip() if len(cols) > 5 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            return times
        except Exception as e:
            logger.error(f"Error scraping standard times: {e}")
            return []

    def scrape_jockey_rankings(self) -> List[Dict]:
        """Scrape Jockey Rankings using Selenium."""
        url = f"{self.INFO_URL}/jockey-ranking"
        rankings = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        jockey_name = cols[0].text.strip()
                        if jockey_name and jockey_name not in ['騎師', 'Jockey', '']:
                            def safe_int(text):
                                try:
                                    return int(text.strip())
                                except (ValueError, AttributeError):
                                    return 0
                            
                            rankings.append({
                                'rank': len(rankings) + 1,
                                'jockey_name': jockey_name,
                                'wins': safe_int(cols[1].text),
                                'seconds': safe_int(cols[2].text),
                                'thirds': safe_int(cols[3].text),
                                'scraped_at': datetime.now().isoformat()
                            })
            return rankings
        except Exception as e:
            logger.error(f"Error scraping jockey rankings: {e}")
            return []

    def scrape_live_odds(self, race_date: str, race_number: int, racecourse: str, max_retries: int = 3) -> List[Dict]:
        """Scrape live odds for a specific race from HKJC betting site using Selenium with retries."""
        # Normalize date format to YYYY-MM-DD
        norm_date_dash = race_date.replace('/', '-')
        url = f"https://bet.hkjc.com/ch/racing/wp/{norm_date_dash}/{racecourse}/{race_number}"
        logger.info(f"Scraping live odds from {url}")
        
        driver = self._get_driver()
        if not driver:
            logger.error("Failed to initialize Selenium driver")
            return []
            
        odds_data = []
        
        for attempt in range(max_retries):
            try:
                driver.get(url)
                
                # Wait for page to load with proper conditions
                wait = WebDriverWait(driver, 20)
                
                # Try multiple selectors for odds table/container
                selectors = [
                    (By.CSS_SELECTOR, "table[class*='odds']"),
                    (By.CSS_SELECTOR, "table[class*='table']"),
                    (By.CSS_SELECTOR, "[class*='odds']"),
                    (By.CSS_SELECTOR, "[class*='race']"),
                    (By.TAG_NAME, "table"),
                ]
                
                loaded = False
                for by, selector in selectors:
                    try:
                        wait.until(EC.presence_of_element_located((by, selector)))
                        loaded = True
                        logger.debug(f"Page loaded with selector: {selector}")
                        break
                    except Exception:
                        continue
                
                if not loaded:
                    logger.warning(f"Could not find expected elements, attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                # Additional wait for dynamic content
                time.sleep(2)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                odds_data = self._parse_live_odds(soup, race_date, race_number, racecourse)
                
                if odds_data:
                    logger.info(f"Successfully scraped {len(odds_data)} live odds records on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"No odds data found on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        
            except Exception as e:
                logger.error(f"Error scraping live odds on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                
        return odds_data
    
    def _parse_live_odds(self, soup: BeautifulSoup, race_date: str, race_number: int, racecourse: str) -> List[Dict]:
        """Parse live odds from BeautifulSoup object with multiple fallback strategies."""
        odds_data = []
        
        # Strategy 1: Look for table rows with odds data
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3:
                continue
            
            text_cols = [c.text.strip() for c in cols]
            
            # Check if first column is a horse number
            if not text_cols or not re.match(r'^\d+$', text_cols[0]):
                continue
            
            try:
                horse_number = int(text_cols[0])
                horse_name = text_cols[1] if len(text_cols) > 1 else ""
                
                if not horse_name or horse_name in ['馬名', 'Horse', '']:
                    continue
                
                # Extract odds from remaining columns
                win_odds = 0.0
                place_odds = 0.0
                
                odds_found = []
                for tc in text_cols[2:]:
                    # Look for decimal numbers (odds format)
                    matches = re.findall(r'(\d+\.?\d*)', tc)
                    for match in matches:
                        try:
                            val = float(match)
                            if val > 1.0:  # Valid odds are > 1.0
                                odds_found.append(val)
                        except ValueError:
                            continue
                
                if odds_found:
                    win_odds = odds_found[0]
                    place_odds = odds_found[1] if len(odds_found) > 1 else 0.0
                
                if win_odds > 0:
                    odds_data.append({
                        'race_date': race_date,
                        'race_number': race_number,
                        'racecourse': racecourse,
                        'horse_number': horse_number,
                        'horse_name': horse_name,
                        'win_odds': win_odds,
                        'place_odds': place_odds,
                        'scraped_at': datetime.now().isoformat()
                    })
            except (ValueError, IndexError) as e:
                continue
        
        # Strategy 2: Look for div-based layouts (alternative HKJC layouts)
        if not odds_data:
            logger.debug("Trying alternative parsing strategy for div-based layouts")
            horse_rows = soup.find_all('div', class_=re.compile(r'horse|row|runner', re.I))
            
            for hr in horse_rows:
                text = hr.get_text(strip=True)
                # Pattern: number, name, odds
                match = re.search(r'^(\d+)\s+([\u4e00-\u9fff\w\s]+?)\s+(\d+\.\d+)', text)
                if match:
                    try:
                        h_num = int(match.group(1))
                        h_name = match.group(2).strip()
                        w_odds = float(match.group(3))
                        
                        # Look for place odds in the same text
                        p_match = re.search(r'\d+\.\d+.*?\d+\.\d+', text)
                        p_odds = 0.0
                        if p_match:
                            odds_vals = re.findall(r'\d+\.\d+', text)
                            if len(odds_vals) >= 2:
                                p_odds = float(odds_vals[1])
                        
                        odds_data.append({
                            'race_date': race_date,
                            'race_number': race_number,
                            'racecourse': racecourse,
                            'horse_number': h_num,
                            'horse_name': h_name,
                            'win_odds': w_odds,
                            'place_odds': p_odds,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except (ValueError, IndexError):
                        continue
        
        # Strategy 3: Generic pattern matching on all text
        if not odds_data:
            logger.debug("Trying generic text pattern matching")
            all_text = soup.get_text()
            # Look for patterns like "1 HorseName 3.5 1.8"
            pattern = r'(\d+)\s+([\u4e00-\u9fff][\u4e00-\u9fff\s]+|[A-Za-z][A-Za-z\s]+)\s+(\d+\.\d+)\s+(\d+\.\d+)?'
            matches = re.findall(pattern, all_text)
            
            for match in matches:
                try:
                    h_num = int(match[0])
                    h_name = match[1].strip()
                    w_odds = float(match[2])
                    p_odds = float(match[3]) if match[3] else 0.0
                    
                    if h_num > 0 and w_odds > 1.0:
                        odds_data.append({
                            'race_date': race_date,
                            'race_number': race_number,
                            'racecourse': racecourse,
                            'horse_number': h_num,
                            'horse_name': h_name,
                            'win_odds': w_odds,
                            'place_odds': p_odds,
                            'scraped_at': datetime.now().isoformat()
                        })
                except (ValueError, IndexError):
                    continue
        
        return odds_data

    def scrape_injury_records(self) -> List[Dict]:
        """Scrape injury/veterinary records from HKJC using Selenium."""
        url = f"{self.BASE_URL}/veterinaryrecord"
        injuries = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        horse_name = cols[0].text.strip()
                        if horse_name and horse_name not in ['馬名', 'Horse', '']:
                            injuries.append({
                                'horse_name': horse_name,
                                'injury_date': cols[1].text.strip() if len(cols) > 1 else '',
                                'condition': cols[2].text.strip() if len(cols) > 2 else '',
                                'status': cols[3].text.strip() if len(cols) > 3 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            return injuries
        except Exception as e:
            logger.error(f"Error scraping injury records: {e}")
            return []

    # def scrape_fixtures(self) -> List[Dict]:
    #     """Scrape race fixtures using Selenium."""
    #     url = f"{self.BASE_URL}/fixture"
    #     fixtures = []
        
    #     try:
    #         driver = self._get_driver()
    #         if not driver:
    #             return []
            
    #         driver.get(url)
    #         time.sleep(3)
            
    #         soup = BeautifulSoup(driver.page_source, 'html.parser')
    #         tables = soup.find_all('table')
            
    #         for table in tables:
    #             rows = table.find_all('tr')
    #             for row in rows[1:]:
    #                 cols = row.find_all('td')
    #                 if len(cols) >= 3:
    #                     date_text = cols[0].text.strip()
    #                     race_date = None
    #                     for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d']:
    #                         try:
    #                             race_date = datetime.strptime(date_text, fmt).strftime('%Y-%m-%d')
    #                             break
    #                         except ValueError:
    #                             continue
                        
    #                     if race_date:
    #                         fixtures.append({
    #                             'race_date': race_date,
    #                             'racecourse': cols[1].text.strip() if len(cols) > 1 else '',
    #                             'day': cols[2].text.strip() if len(cols) > 2 else '',
    #                             'details': cols[3].text.strip() if len(cols) > 3 else '',
    #                             'scraped_at': datetime.now().isoformat()
    #                         })
    #         return fixtures
    #     except Exception as e:
    #         logger.error(f"Error scraping fixtures: {e}")
    #         return []



    def scrape_fixtures(self) -> List[Dict]:
        """Scrape race fixtures using Selenium."""
        url = f"{self.BASE_URL}/fixture"
        fixtures = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(5)  # Increased wait time
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Get the month and year from the table header
            month_year_header = soup.find('div', class_='fixture_tab').find('td', colspan='7')
            month_year_text = month_year_header.text.strip() if month_year_header else ""
            # Extract year and month (e.g., "February 2026")
            month_year_parts = month_year_text.split()
            month_name = month_year_parts[0] if len(month_year_parts) > 0 else ""
            year = month_year_parts[1] if len(month_year_parts) > 1 else "2026"
            
            # Find the main fixture table
            fixture_table = soup.find('table', class_='table_bd')
            if not fixture_table:
                return fixtures
            
            # Find all calendar cells (td elements with class 'calendar')
            calendar_cells = fixture_table.find_all('td', class_='calendar')
            
            for cell in calendar_cells:
                # Extract date
                date_span = cell.find('span', class_='f_fl f_fs14')
                if not date_span:
                    continue
                
                day = date_span.text.strip()
                
                # Construct full date (need to map month name to month number)
                month_map = {
                    'January': '01', 'February': '02', 'March': '03', 'April': '04',
                    'May': '05', 'June': '06', 'July': '07', 'August': '08',
                    'September': '09', 'October': '10', 'November': '11', 'December': '12'
                }
                
                month_num = month_map.get(month_name, '01')
                race_date = f"{year}-{month_num}-{day.zfill(2)}"
                
                # Extract racecourse and time from images
                racecourse = ""
                day_night = ""
                track_type = ""
                
                img_spans = cell.find('span', class_='f_fr')
                if img_spans:
                    images = img_spans.find_all('img')
                    for img in images:
                        alt_text = img.get('alt', '').upper()
                        if alt_text in ['HV', 'ST']:
                            racecourse = "Happy Valley" if alt_text == 'HV' else "Sha Tin"
                        elif alt_text in ['D', 'N']:
                            day_night = "Day" if alt_text == 'D' else "Night"
                        elif alt_text in ['TURF', 'MIXED']:
                            track_type = alt_text
                
                # Extract race details
                race_details = []
                race_paragraphs = cell.find_all('p')[1:]  # Skip the first p which contains date
                
                for p in race_paragraphs:
                    # Extract class
                    class_img = p.find('img')
                    race_class = class_img.get('alt', '') if class_img else ''
                    
                    # Extract distance and other info
                    span = p.find('span', style='display: -webkit-box;')
                    if span:
                        distance_text = span.text.strip()
                        
                        # Clean up the text
                        distance_text = ' '.join(distance_text.split())
                        
                        race_details.append({
                            'class': race_class,
                            'details': distance_text
                        })
                
                # Create fixture entry
                fixture_data = {
                    'race_date': race_date,
                    'racecourse': racecourse,
                    'day_night': day_night,
                    'track_type': track_type,
                    'race_count': len(race_details),
                    'races': race_details,
                    'scraped_at': datetime.now().isoformat()
                }
                
                fixtures.append(fixture_data)
            
            return fixtures
            
        except Exception as e:
            logger.error(f"Error scraping fixtures: {e}")
            return []
    def scrape_barrier_tests(self, race_date: str = None) -> List[Dict]:
        """Scrape barrier test results using Selenium."""
        url = f"{self.BASE_URL}/btresult"
        tests = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        horse_name = cols[0].text.strip()
                        if horse_name and horse_name not in ['馬名', 'Horse', '']:
                            tests.append({
                                'horse_name': horse_name,
                                'test_date': cols[1].text.strip() if len(cols) > 1 else '',
                                'barrier': cols[2].text.strip() if len(cols) > 2 else '',
                                'time': cols[3].text.strip() if len(cols) > 3 else '',
                                'remarks': cols[4].text.strip() if len(cols) > 4 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            return tests
        except Exception as e:
            logger.error(f"Error scraping barrier tests: {e}")
            return []

    def scrape_weather(self, race_date: str, racecourse: str) -> List[Dict]:
        """Scrape weather data."""
        # This often comes from race info on race card
        return []

    def scrape_last_race_summaries(self, race_date: str) -> List[Dict]:
        """Scrape last race summaries using Selenium."""
        norm_date = self._normalize_date_format(race_date)
        url = f"{self.BASE_URL}/racereportext?racedate={norm_date}"
        summaries = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for idx, table in enumerate(tables, 1):
                text = table.get_text(strip=True)
                if text and len(text) > 50:
                    summaries.append({
                        'race_date': race_date,
                        'race_number': idx,
                        'summary_text': text[:500],
                        'scraped_at': datetime.now().isoformat()
                    })
            return summaries
        except Exception as e:
            logger.error(f"Error scraping last race summaries: {e}")
            return []

    # def scrape_wind_tracker(self, race_date: str) -> List[Dict]:
    #     """Scrape wind and weather data using Selenium."""
    #     url = f"{self.INFO_URL}/windtracker"
    #     wind_data = []
        
    #     try:
    #         driver = self._get_driver()
    #         if not driver:
    #             return []
            
    #         driver.get(url)
    #         time.sleep(3)
            
    #         soup = BeautifulSoup(driver.page_source, 'html.parser')
    #         tables = soup.find_all('table')
            
    #         for table in tables:
    #             rows = table.find_all('tr')
    #             for row in rows[1:]:
    #                 cols = row.find_all('td')
    #                 if len(cols) >= 2:
    #                     wind_data.append({
    #                         'race_date': race_date,
    #                         'time': cols[0].text.strip(),
    #                         'wind_speed': cols[1].text.strip() if len(cols) > 1 else '',
    #                         'wind_direction': cols[2].text.strip() if len(cols) > 2 else '',
    #                         'track_condition': cols[3].text.strip() if len(cols) > 3 else '',
    #                         'scraped_at': datetime.now().isoformat()
    #                     })
    #         return wind_data
    #     except Exception as e:
    #         logger.error(f"Error scraping wind tracker: {e}")
    #         return []



    def scrape_wind_tracker(self, race_date: str) -> List[Dict]:
        """Scrape wind and weather data using Selenium."""
        url = f"{self.INFO_URL}/windtracker"
        wind_data = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(5)
            
            # 等待页面基本内容加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "m_Container"))
                )
            except:
                pass  # 即使超时也继续执行
            
            # 获取整个页面的文本内容进行解析
            page_text = driver.page_source
            
            # 使用正则表达式提取风力数据
            wind_pattern = r'([东南西北北偏]+)\s*(\d+(?:\.\d+)?)\s*公里/小時\s*(\d+(?:\.\d+)?)\s*公里/小時'
            wind_matches = re.findall(wind_pattern, page_text)
            
            # 提取其他天气数据
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', page_text)
            track_match = re.search(r'(沙田|跑馬地)', page_text)
            temp_match = re.search(r'氣溫\s*(\d+(?:\.\d+)?)°C', page_text)
            humidity_match = re.search(r'相對濕度\s*(\d+(?:\.\d+)?)%', page_text)
            rainfall_match = re.search(r'總雨量\s*(\d+(?:\.\d+)?)\s*毫米', page_text)
            
            # 提取更新时间
            update_match = re.search(r'最後更新:\s*(\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2})', page_text)
            
            # 获取当前显示的赛道（通过检查UI状态）
            current_track = "Unknown"
            try:
                # 检查哪个赛道的元素是可见的
                sha_tin_element = driver.find_element(By.CLASS_NAME, "trackTab_labelOn__FV_8L")
                if "沙田" in sha_tin_element.text:
                    current_track = "Sha Tin"
                else:
                    # 尝试查找Happy Valley的激活状态
                    track_switch = driver.find_element(By.CLASS_NAME, "trackTab_switch__n34RU")
                    if "trackTab_switchOff__mFt5r" in track_switch.get_attribute("class"):
                        # 检查文字判断当前赛道
                        if "跑馬地" in page_text and "跑馬地" in track_switch.text:
                            current_track = "Happy Valley"
            except:
                # 如果无法通过UI判断，从页面文本推断
                if "沙田" in page_text and "跑馬地" not in page_text:
                    current_track = "Sha Tin"
                elif "跑馬地" in page_text:
                    current_track = "Happy Valley"
            
            # 如果没有找到匹配的风力数据，尝试备用方法
            if not wind_matches:
                wind_matches = self._extract_wind_data_fallback(driver)
            
            # 创建数据记录
            for i, match in enumerate(wind_matches):
                wind_direction = match[0] if len(match) > 0 else "--"
                wind_speed = match[1] if len(match) > 1 else "--"
                gust_speed = match[2] if len(match) > 2 else "--"
                
                wind_data.append({
                    'race_date': race_date,
                    'track': current_track,
                    'position': f"Position {i+1}",
                    'wind_direction': wind_direction,
                    'wind_speed': f"{wind_speed} km/h",
                    'gust_speed': f"{gust_speed} km/h" if gust_speed != "--" else "",
                    'update_time': update_match.group(1) if update_match else "",
                    'temperature': f"{temp_match.group(1)}°C" if temp_match else "--",
                    'humidity': f"{humidity_match.group(1)}%" if humidity_match else "--",
                    'rainfall': f"{rainfall_match.group(1)} mm" if rainfall_match else "--",
                    'date_on_page': date_match.group(1) if date_match else "",
                    'scraped_at': datetime.now().isoformat()
                })
            
            # 如果没有提取到任何风力数据，创建一个基础记录
            if not wind_data:
                wind_data.append({
                    'race_date': race_date,
                    'track': current_track,
                    'position': "General",
                    'wind_direction': "--",
                    'wind_speed': "--",
                    'gust_speed': "--",
                    'update_time': update_match.group(1) if update_match else "",
                    'temperature': f"{temp_match.group(1)}°C" if temp_match else "--",
                    'humidity': f"{humidity_match.group(1)}%" if humidity_match else "--",
                    'rainfall': f"{rainfall_match.group(1)} mm" if rainfall_match else "--",
                    'date_on_page': date_match.group(1) if date_match else "",
                    'scraped_at': datetime.now().isoformat()
                })
            
            logger.info(f"Extracted {len(wind_data)} wind records for {race_date}")
            return wind_data
            
        except Exception as e:
            logger.error(f"Error scraping wind tracker: {e}")
            # 即使出错也返回一个基础记录
            return [{
                'race_date': race_date,
                'track': "Unknown",
                'position': "Error",
                'wind_direction': "--",
                'wind_speed': "--",
                'gust_speed': "--",
                'update_time': "",
                'temperature': "--",
                'humidity': "--",
                'rainfall': "--",
                'date_on_page': "",
                'scraped_at': datetime.now().isoformat(),
                'error': str(e)
            }]

    def _extract_wind_data_fallback(self, driver):
        """备用的风力数据提取方法"""
        wind_matches = []
        try:
            # 方法1: 尝试从特定的div结构中提取
            wind_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'windValue') or contains(@class, 'm_wind')]")
            
            for element in wind_elements:
                text = element.text.strip()
                if text and any(keyword in text for keyword in ['公里/小時', 'km/h', '東', '南', '西', '北']):
                    # 尝试从文本中解析
                    import re
                    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*公里/小時', text)
                    direction_match = re.search(r'([东南西北]+)', text)
                    
                    if speed_match:
                        wind_matches.append([
                            direction_match.group(1) if direction_match else "--",
                            speed_match.group(1),
                            speed_match.group(1)  # 假设阵风速度相同
                        ])
            
            # 方法2: 如果上述方法失败，尝试从页面文本中直接搜索
            if not wind_matches:
                page_text = driver.page_source
                # 寻找风力数据的特定模式
                pattern = r'([东南西北北偏]+)[^0-9]*(\d+(?:\.\d+)?)[^0-9]*(\d+(?:\.\d+)?)[^公里/小時]*公里/小時'
                matches = re.findall(pattern, page_text)
                wind_matches = list(matches)
                
        except Exception as e:
            logger.warning(f"Fallback wind extraction failed: {e}")
        
        return wind_matches

    def scrape_battle_memorandum(self) -> List[Dict]:
        """Scrape battle memorandum - Last Run Reminder using Selenium."""
        url = f"{self.PAGE_URL}/last-run-reminder"
        memoranda = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        horse_name = cols[0].text.strip()
                        if horse_name and horse_name not in ['馬名', 'Horse', '']:
                            memoranda.append({
                                'horse_name': horse_name,
                                'last_race_date': cols[1].text.strip() if len(cols) > 1 else '',
                                'memo': cols[2].text.strip() if len(cols) > 2 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            return memoranda
        except Exception as e:
            logger.error(f"Error scraping battle memorandum: {e}")
            return []

    def scrape_new_horse_introductions(self) -> List[Dict]:
        """Scrape new horse introductions using Selenium."""
        url = f"{self.PAGE_URL}/new-horse"
        horses = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        horse_name = cols[0].text.strip()
                        if horse_name and horse_name not in ['馬名', 'Horse', '']:
                            horses.append({
                                'horse_name': horse_name,
                                'origin': cols[1].text.strip() if len(cols) > 1 else '',
                                'trainer': cols[2].text.strip() if len(cols) > 2 else '',
                                'age': cols[3].text.strip() if len(cols) > 3 else '',
                                'sex': cols[4].text.strip() if len(cols) > 4 else '',
                                'scraped_at': datetime.now().isoformat()
                            })
            return horses
        except Exception as e:
            logger.error(f"Error scraping new horse introductions: {e}")
            return []

    def scrape_trainer_rankings(self) -> List[Dict]:
        """Scrape Trainer Rankings using Selenium."""
        url = f"{self.INFO_URL}/trainer-ranking"
        rankings = []
        
        try:
            driver = self._get_driver()
            if not driver:
                return []
            
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        trainer_name = cols[0].text.strip()
                        if trainer_name and trainer_name not in ['練馬師', 'Trainer', '']:
                            def safe_int(text):
                                try:
                                    return int(text.strip())
                                except (ValueError, AttributeError):
                                    return 0
                            
                            rankings.append({
                                'rank': len(rankings) + 1,
                                'trainer_name': trainer_name,
                                'wins': safe_int(cols[1].text),
                                'seconds': safe_int(cols[2].text),
                                'thirds': safe_int(cols[3].text),
                                'scraped_at': datetime.now().isoformat()
                            })
            return rankings
        except Exception as e:
            logger.error(f"Error scraping trainer rankings: {e}")
            return []
