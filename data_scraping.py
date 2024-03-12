import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL to the web page you want to scrape (adjust as needed)
url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617972/12005"

# Send a GET request to the webpage
response = requests.get(url)
# Parse the HTML content of the page
soup = BeautifulSoup(response.text, 'html.parser')

data = []  # List to hold all entries as dictionaries



# Helper function to extract headers, considering secondline
def extract_headers(block_header):
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




# Find all heat blocks
heat_blocks = soup.find_all(class_=lambda x: x and x.startswith("runblock heatblock"))

dataframes = {}  # Dictionary to hold a DataFrame for each heat

for heat in heat_blocks:
    heat_name = heat['class'][-1]  # Extract heat name/number
    result_blocks = heat.find_all(class_="resultblock")
    
    heat_data = []  # List to hold data for this specific heat
    
    for block in result_blocks:
        block_table = block.find(class_="blocktable")
        block_header = block_table.find(class_="blockheader")
        headers = extract_headers(block_header)
        
        entries = block_table.find_all("div", recursive=False)[1:]  # Skipping the blockheader
        
        for entry in entries:
            entry_data = {}
            columns = entry.find_all("div", recursive=False)
            
            for i, header_tuple in enumerate(headers):
                column_data = columns[i].find_all("div")
                
                # Assign first line data directly using header_tuple[0]
                entry_data[header_tuple[0]] = column_data[0].get_text(" ", strip=True)
                
                # If there's a second line in the header, assign second line data
                if len(header_tuple) == 2 and len(column_data) > 1:
                    entry_data[header_tuple[1]] = column_data[1].get_text(" ", strip=True)
            
            heat_data.append(entry_data)
    
    # Convert the list of dictionaries to a DataFrame for this specific heat
    dataframes[heat_name] = pd.DataFrame(heat_data)


# Example: Access the DataFrame for heat 'h-1'
h1_df = dataframes['h-1']
print(h1_df.head())  # Replace 'h-1' with the actual key if it's different

# Similarly, to access the DataFrame for heat 'h-2'
h2_df = dataframes['h-2']
print(h2_df.head())  # Adjust the key as necessary
