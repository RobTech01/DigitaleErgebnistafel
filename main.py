from package.presentation_actions import skip_to_page, collect_group_shapes, populate_group, scan_for_shapes, add_content_to_group_shapes, update_presentation
import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import time
import logging
import pandas as pd

logging.basicConfig(level=logging.WARNING)


def heat_selection(df_data : pd.DataFrame) -> str:
    heats = list(df_data.keys())
    print(f"Available heats: {heats}")

    if len(heats) > 1:
        while True:
            selected_key = input("Please enter the key of the heat you want to use: ")
            if selected_key in heats:
                break
            print("Invalid key. Please try again.")
    else:
        selected_key = heats[0]

    print(f"Selected heat: {selected_key}")
    return selected_key

def fetch_and_update_presentation(url : str, selected_heat : str, column_headers, presentation) -> None:
    entries_per_slide = 8  # Number of entries that fit in one slide

    old_df = pd.DataFrame()  # Start with an empty DataFrame
    update_count = 0

    dropped_row_count = 1

    while not dropped_row_count == 0:

        new_df = scrape_dlv_data(url)[selected_heat]

        if new_df.empty:
             logging.info("No data retreived. Checking again..")
             time.sleep(2)
             continue
        
        dnf_entries = new_df['Ergebnis'].isin(['n.a.', 'ab.', 'aufg.'])
        dnf_df = new_df[dnf_entries]
        new_df = new_df[~dnf_entries]

        if old_df.keys().empty:
             old_df = pd.DataFrame(columns=column_headers)
       
        if not new_df.equals(old_df):
            
            data_row_count = len(new_df)
            drop_unfinished_ranks = new_df['Rang'].ne('')
            dropped_row_count = len (new_df) - len(drop_unfinished_ranks)
            
            new_ranks = new_df[new_df['Rang'].ne('') & (~new_df['Rang'].isin(old_df['Rang'].dropna()))]

            if not new_ranks.empty:
                logging.info("New ranked entries found, updating presentation.")
                update_count_buffer = update_presentation(new_ranks, presentation, update_count, entries_per_slide)
                update_count = update_count_buffer
            
            old_df = new_df.copy()

        else:
            logging.info("No new ranked entries or changes detected. Checking again in 1 second.")
        
        print('athletes not finished: ', dropped_row_count, '/', data_row_count)
        time.sleep(2)
    
    #update by dnf_ranks if they exist
    if not dnf_df.empty:
        update_count_buffer = update_presentation(dnf_df, presentation, update_count, entries_per_slide)
        update_count = update_count_buffer
        logging.info("Adding DNF athletes: ", len(dnf_df))        

    assert presentation.SlideShowWindow, "no active slideshow"
    presentation.SlideShowWindow.View.Next()
    time.sleep(5)

    if update_count > entries_per_slide:
        index_last_slide = presentation.Slides.Count
        slide = presentation.Slides(index_last_slide)
        duplicated_slide = slide.Duplicate().Item(1)
        slide = duplicated_slide
        group_objects = collect_group_shapes(slide)

        for group in group_objects[1:]:
            group.Top += 44 * (update_count-entries_per_slide)
    
        assert presentation.SlideShowWindow, "no active slideshow"
        presentation.SlideShowWindow.View.Next()

    print("All athletes displayed")


def main():
    logging.basicConfig(level=logging.INFO)
    
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/509866/9812#h8"
    dataframes = scrape_dlv_data(url)

    pythoncom.CoInitialize()  # Initialize the COM library

    try:
        already_open_powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        presentation = already_open_powerpoint.ActivePresentation
    except AttributeError:
        logging.critical("No active presentation found.")
    
    active_slide = 2
    num_slides = presentation.Slides.Count
    assert num_slides >= active_slide, f"you are trying to skip to slide {active_slide}, the highest page number is {num_slides}"
    slide = presentation.Slides(active_slide)

    shape_count = scan_for_shapes(slide)
    group_objects = collect_group_shapes(slide)

    selected_heat = heat_selection(dataframes)
    df = dataframes[selected_heat]
    content_headers = df.columns.tolist()
    logging.debug(f"Content Headers: {content_headers}")


    title_placeholder = slide.Shapes.Title
    title_placeholder.TextFrame.TextRange.Text = selected_heat


    group_header = group_objects[0]

    print(content_headers)

    populate_group(group_header, content_headers)

    time.sleep(1)

    assert presentation.SlideShowWindow, "no active slideshow"
    presentation.SlideShowWindow.View.Next()

    time.sleep(2)

    fetch_and_update_presentation(url, selected_heat, content_headers, presentation)
    
    assert presentation.SlideShowWindow, "no active slideshow"
    time.sleep(15) 
    presentation.SlideShowWindow.View.First()  # Go to the first slide


if __name__ == "__main__":
    main()
