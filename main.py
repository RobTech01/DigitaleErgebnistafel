from package.presentation_actions import skip_to_page, collect_group_shapes, populate_group, scan_for_shapes, add_content_to_group_shapes, update_presentation
import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import logging
import pandas as pd
import threading

logging.basicConfig(level=logging.INFO)


def heat_selection(df_data : pd.DataFrame) -> str:
    heats = list(df_data.keys())
    for i, heat in enumerate(heats, 1):
        print(f"{i}. {heat}")
    print("Select a Number")

    user_input = input("> ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(heats):
        return heats[int(user_input) - 1]
    else:
        print("invalid input choose again")
        return heat_selection(df_data)
    

def truncate_text(text):
    return text[:20] + '..' if isinstance(text, str) and len(text) > 25 else text


def fetch_and_update_presentation(url : str, selected_heat : str, column_headers, presentation, event) -> None:
    entries_per_slide = 8  # Number of entries that fit in one slide
    vertical_movement_per_entry = 44  # Vertical movement for each entry
    recheck_time = 3   # in s

    old_df = pd.DataFrame(columns=column_headers)
    update_count = 0

    dropped_row_count = 1

    while True:
        new_df = scrape_dlv_data(url)[selected_heat]
        new_df = new_df.map(truncate_text)

        if new_df.empty:
            logging.info("No data retrieved. Checking again...")
            continue
        
        total_runners = len(new_df)

        # Filter to identify only new or updated rows
        if not old_df.empty:
            new_df = pd.concat([old_df, new_df]).drop_duplicates(keep=False)

        # Filter out DNF and similar entries
        dnf_entries = new_df['Ergebnis'].isin(['n.a.', 'ab.', 'aufg.', 'n.a.', 'disq.', 'DNS', 'DNF', 'DQ'])
        dnf_df = new_df[dnf_entries]
        new_df = new_df[~dnf_entries]
       
        # Filter out entries without a completed rank (unfinished athletes)
        new_df = new_df[new_df['Rang'].ne('')]
        
        if not new_df.empty:
            logging.info("New ranked entries found, updating presentation.")
            update_count = update_presentation(new_df, presentation, update_count, entries_per_slide, vertical_movement_per_entry, event)
        
        old_df = pd.concat([old_df, new_df])
        captured_athletes = len(old_df) + len(dnf_df)
        logging.info('missing runners %s / %s', captured_athletes, total_runners)

        if len(old_df)+len(dnf_df) == total_runners:
            logging.info('All %s out of %s runners are finished or disqualified.', captured_athletes, total_runners)
            break

        if new_df.empty:
            logging.info("No new ranked entries or changes detected. Checking again in %s second.", recheck_time)
            event.wait(recheck_time)
            continue

    event.wait(recheck_time)

    
    #update by dnf_ranks if they exist
    if not dnf_df.empty:
        logging.info("Adding DNF athletes: %s", len(dnf_df))        
        update_count = update_presentation(dnf_df, presentation, update_count, entries_per_slide, vertical_movement_per_entry, event)

    if update_count % entries_per_slide != 0:
        last_slide_index = presentation.Slides.Count
        slide = presentation.Slides(last_slide_index)
        logging.info('Adding another slide after %s participants', update_count)
        duplicated_slide = slide.Duplicate().Item(1)
        slide = duplicated_slide
        group_objects = collect_group_shapes(slide)
        for group in group_objects[1:]:
            group.Top -= vertical_movement_per_entry * (update_count % entries_per_slide)

        logging.info('Going to the next slide, total slides %s', presentation.Slides.Count)
        assert presentation.SlideShowWindow, 'no active slideshow'
        presentation.SlideShowWindow.View.Next()
        event.wait(recheck_time* (update_count % entries_per_slide))

#    assert presentation.SlideShowWindow, "no active slideshow"
#    presentation.SlideShowWindow.view.Next()

    else: 
        event.wait(10)

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

    logging.info("All athletes displayed")

    event.wait(15)

    assert presentation.SlideShowWindow, "no active slideshow"
    presentation.SlideShowWindow.View.First()


def main():
    logging.basicConfig(level=logging.INFO)
    
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/509869/9812"
    dataframes = scrape_dlv_data(url)

    event = threading.Event()

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

    event.wait(1)

    assert presentation.SlideShowWindow, "no active slideshow"
    presentation.SlideShowWindow.View.Next()

    event.wait(3.6)

    active_slide = 3
    slide = presentation.Slides(active_slide)
    group_objects = collect_group_shapes(slide)

    title_placeholder = slide.Shapes.Title
    title_placeholder.TextFrame.TextRange.Text = selected_heat
    group_header = group_objects[0]
    populate_group(group_header, content_headers)

    presentation.SlideShowWindow.View.Next()

    event.wait(0.5)

    fetch_and_update_presentation(url, selected_heat, content_headers, presentation, event)
    

if __name__ == "__main__":
    main()
