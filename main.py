from package.data_scraping import scrape_data
from package.window import display_results

def main():
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617855/12005"
    dataframes = scrape_data(url)
    display_results(dataframes)

if __name__ == "__main__":
    main()