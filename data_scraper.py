import requests
import logging
from bs4 import BeautifulSoup
import pandas as pd

# Get logger from parent
logger = logging.getLogger(__name__)

class DLVResultsScraper:
    """Class to scrape results from the DLV website"""
    
    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def extract_headers(self, block_header):
        """Extract headers from the block header"""
        headers = []
        for header_div in block_header.find_all("div", recursive=False):
            first_line_text = header_div.find_all("div")[0].get_text(strip=True)
            second_line = header_div.find("div", class_="secondline")
            
            if second_line:
                second_line_text = second_line.get_text(strip=True)
                headers.append((first_line_text, second_line_text))  # Tuple with first and second line
            else:
                headers.append((first_line_text,))  # Tuple with only first line
        
        return headers
    
    def get_available_heats(self, url):
        """Get the list of available heats from the DLV website"""
        try:
            logger.info(f"Fetching data from {url}")
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            heat_blocks = soup.find_all(class_=lambda x: x and (
                x.startswith("runblock heatblock") or 
                x.startswith("runblock roundblock") or 
                x.startswith("startlistblock")
            ))
            
            heats = []
            for heat in heat_blocks:
                blockname = heat.find(class_="blockname")
                leftname = blockname.find(class_="leftname") if blockname else None
                heat_name = leftname.get_text(strip=True) if leftname else None
                
                if heat_name:
                    heats.append(heat_name)
            
            return heats
            
        except Exception as e:
            logger.error(f"Error getting available heats: {e}")
            raise
    
    def get_heat_results(self, url, heat_name):
        """Get the results for a specific heat"""
        try:
            dataframes = self.scrape_dlv_data(url)
            
            if heat_name not in dataframes:
                logger.warning(f"Heat '{heat_name}' not found in scraped data")
                return {'data': [], 'columns': []}
            
            df = dataframes[heat_name]
            
            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')
            columns = df.columns.tolist()
            
            return {
                'data': data,
                'columns': columns,
                'heat_name': heat_name
            }
            
        except Exception as e:
            logger.error(f"Error getting heat results: {e}")
            raise
    
    def scrape_dlv_data(self, url):
        """
        Scrape data from the DLV website with improved error handling
        """
        try:
            logger.info(f"Fetching data from {url}")
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            
            logger.info("Parsing HTML content")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            dataframes = {}
            heat_blocks = soup.find_all(class_=lambda x: x and (
                x.startswith("runblock heatblock") or 
                x.startswith("runblock roundblock") or 
                x.startswith("startlistblock")
            ))
            
            if not heat_blocks:
                logger.warning("No heat blocks found on the page")
                return {}
            
            logger.info(f"Found {len(heat_blocks)} heat blocks")
            
            for heat in heat_blocks:
                try:
                    blockname = heat.find(class_="blockname")
                    leftname = blockname.find(class_="leftname") if blockname else None
                    heat_name = leftname.get_text(strip=True) if leftname else "Unknown Heat"
                    
                    logger.info(f"Processing heat: {heat_name}")
                    
                    result_blocks = heat.find_all(class_="resultblock")
                    
                    if not result_blocks:
                        logger.warning(f"No result blocks found in heat: {heat_name}")
                        continue
                    
                    for block in result_blocks:
                        block_table = block.find(class_="blocktable")
                        
                        if not block_table:
                            logger.warning(f"No block table found in result block for heat: {heat_name}")
                            continue
                        
                        block_header = block_table.find(class_="blockheader")
                        
                        if not block_header:
                            logger.warning(f"No block header found in block table for heat: {heat_name}")
                            continue
                        
                        headers = self.extract_headers(block_header)
                        
                        entries = block_table.find_all("div", recursive=False)[1:]  # Skipping the blockheader
                        heat_data = []
                        
                        for entry in entries:
                            entry_data = {}
                            columns = entry.find_all("div", recursive=False)
                            
                            for i, header_tuple in enumerate(headers):
                                if i >= len(columns):
                                    # Skip if column is missing
                                    continue
                                    
                                column_data = columns[i].find_all("div")
                                entry_data[header_tuple[0]] = column_data[0].get_text(" ", strip=True) if column_data else ""
                                
                                if len(header_tuple) == 2 and len(column_data) > 1:
                                    entry_data[header_tuple[1]] = column_data[1].get_text(" ", strip=True)
                            
                            heat_data.append(entry_data)
                        
                        if heat_data:
                            dataframes[heat_name] = pd.DataFrame(heat_data)
                            logger.info(f"Created DataFrame for heat: {heat_name} with {len(heat_data)} entries")
                        else:
                            logger.warning(f"No data entries found for heat: {heat_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing heat: {str(e)}")
                    continue
            
            return dataframes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to fetch data from URL: {str(e)}")
        
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            raise Exception(f"Error scraping data: {str(e)}")