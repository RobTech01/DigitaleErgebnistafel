from package.presentation_actions import skip_to_page, collect_group_shapes, populate_group, scan_for_shapes, add_content_to_group_shapes, update_presentation
import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import logging
import pandas as pd
import threading

logging.basicConfig(level=logging.INFO)


def select_competition_heat(df_data : pd.DataFrame) -> str:
    heats = list(df_data.keys())
    for i, heat in enumerate(heats, 1):
        print(f"{i}. {heat}")
    print("Select a Number")

    user_input = input("> ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(heats):
        return heats[int(user_input) - 1]
    else:
        print("invalid input choose again")
        return select_competition_heat(df_data)
    

def prompt_for_data_url() -> str:
    print("Provide the url with the results: ")
    data_url = input("> ").strip()

    try:
        test_df = scrape_dlv_data(data_url)
    except AttributeError:
        logging.error("There seems to be an issue with the url.. try again")
        prompt_for_data_url()
    
    print("url scrape successful")
    print(test_df.keys())
    print("do you want to use that data?")

    user_input = input("(y/n)> ").split()
    print(user_input)
    if user_input[0] == 'y':
        print("yes")
        return data_url
    
    prompt_for_data_url()


def truncate_text_to_25_chars(text):
    return text[:25] + '..' if isinstance(text, str) and len(text) > 20 else text

def fetch_new_data(url : str, selected_heat : str) -> pd.DataFrame:
    new_df = scrape_dlv_data(url)[selected_heat]
    new_df = new_df.map(truncate_text_to_25_chars)
    return new_df

def filter_and_identify_new_entries(new_df: pd.DataFrame, old_df: pd.DataFrame) -> list[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dnf_entries = new_df['Ergebnis'].isin(['n.a.', 'ab.', 'aufg.', 'n.a.', 'disq.', 'DNS', 'DNF', 'DQ'])
    dnf_df = new_df[dnf_entries]
    new_df = new_df[~dnf_entries]
    new_df = new_df[new_df['Rang'].ne('')]  # Ensure rank is not empty
    if not old_df.empty:
        new_df = pd.concat([old_df, new_df]).drop_duplicates(keep=False)
    return new_df, dnf_df, old_df

def manage_last_slide_duplication_or_transition(presentation, update_count, entries_per_slide, vertical_movement_per_entry):
    if update_count % entries_per_slide != 0 and update_count > entries_per_slide:
        logging.info("Triggering slide duplication after adding entries.")
        last_content_slide_index = presentation.Slides.Count - 1
        slide = presentation.Slides(last_content_slide_index)
        duplicated_slide = slide.Duplicate().Item(1)
        slide = duplicated_slide
        group_objects = collect_group_shapes(slide)
        for group in group_objects[1:]:
            group.Top -= vertical_movement_per_entry * (update_count % entries_per_slide)
        return duplicated_slide
    return None



def update_presentation_with_live_data(url : str, selected_heat : str, column_headers, presentation, event) -> None:
    ENTRIES_PER_SLIDE = 8  # Number of entries that fit in one slide
    VERTICAL_MOVEMENT_PER_ENTRY = 44  # Vertical movement for each entry
    RECHECK_TIME = 3   # in s
    TRANSITION_IN_SECONDS = 3.5

    old_df = pd.DataFrame(columns=column_headers)
    update_count = 0

    dropped_row_count = 1

    while True:
        new_df = fetch_new_data(url, selected_heat)
        total_runners = len(new_df)

        if new_df.empty:
            logging.info("No data retrieved. Checking again...")
            event.wait(RECHECK_TIME)
            continue        

        new_df, dnf_df, old_df = filter_and_identify_new_entries(new_df, old_df)
       
        if not new_df.empty:
            logging.info("New ranked entries found, updating presentation.")
            update_count = update_presentation(new_df, presentation, update_count, ENTRIES_PER_SLIDE, VERTICAL_MOVEMENT_PER_ENTRY, event)
        
        old_df = pd.concat([old_df, new_df])
        captured_athletes = len(old_df) + len(dnf_df)
        logging.info('missing runners %s / %s', captured_athletes, total_runners)

        if len(old_df)+len(dnf_df) == total_runners:
            logging.info('All %s out of %s runners are finished or disqualified.', captured_athletes, total_runners)
            break

        if new_df.empty:
            logging.info("No new ranked entries or changes detected. Checking again in %s second.", RECHECK_TIME)
            event.wait(RECHECK_TIME)
            continue

    
    #update by dnf_ranks if they exist
    if not dnf_df.empty:
        logging.info("Adding DNF athletes: %s", len(dnf_df))        
        update_count = update_presentation(dnf_df, presentation, update_count, ENTRIES_PER_SLIDE, VERTICAL_MOVEMENT_PER_ENTRY, event)

    else: 
        event.wait(1)
    
    duplicated_slide = manage_last_slide_duplication_or_transition(presentation, update_count, ENTRIES_PER_SLIDE, VERTICAL_MOVEMENT_PER_ENTRY)
    event.wait(1)

    if duplicated_slide:
        logging.info('Going to the next slide, total slides %s', presentation.Slides.Count)
        assert presentation.SlideShowWindow, 'no active slideshow'
        presentation.SlideShowWindow.View.Next()
        event.wait(2*(update_count%ENTRIES_PER_SLIDE+ 2* TRANSITION_IN_SECONDS))


#    assert presentation.SlideShowWindow, "no active slideshow"
#    presentation.SlideShowWindow.view.Next()


    if update_count > ENTRIES_PER_SLIDE:
        last_content_slide_index = presentation.Slides.Count -1
        slide = presentation.Slides(last_content_slide_index)
        duplicated_slide = slide.Duplicate().Item(1)
        slide = duplicated_slide
        group_objects = collect_group_shapes(slide)

        for group in group_objects[1:]:
            group.Top += 44 * (update_count-ENTRIES_PER_SLIDE)
    
        assert presentation.SlideShowWindow, "no active slideshow"
        presentation.SlideShowWindow.View.Next()

    logging.info("All athletes displayed, remember to reset the Presentation")

    event.wait(3*ENTRIES_PER_SLIDE + 2*TRANSITION_IN_SECONDS)

    assert presentation.SlideShowWindow, "no active slideshow"
    presentation.SlideShowWindow.View.First()


def main():
    logging.basicConfig(level=logging.INFO)
    
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/509869/9812"

    url = prompt_for_data_url()

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

    selected_heat = select_competition_heat(dataframes)
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

    update_presentation_with_live_data(url, selected_heat, content_headers, presentation, event)
    

if __name__ == "__main__":
    main()
