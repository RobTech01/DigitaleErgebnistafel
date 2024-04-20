from package.presentation_actions import skip_to_page, collect_group_shapes, populate_group, scan_for_shapes, add_content_to_group_shapes
import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import time
import logging

logging.basicConfig(level=logging.WARNING)


def heat_selection(df_data):
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


def main():
    url = "https://ergebnisse.leichtathletik.de/Competitions/StartList/509875/9812"
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

    participant_count = df.shape[0]
    entries_per_row = df.shape[1]


    participant_count = df.shape[0]  # Total number of participants
    entries_per_row = df.shape[1]  # Assuming this is used somewhere in populate_group
    initial_slide_index = 2  # The slide to start duplicating from
    vertical_movement_per_entry = 44  # Movement for each entry
    horizontal_movement_per_entry = -905  # Movement for each entry
    entries_per_slide = 8  # Number ofentries that fit in one slide

    slide = presentation.Slides(initial_slide_index)
    group_objects = collect_group_shapes(slide)
    row = df.iloc[0].tolist()
    time.sleep(.75)

    for row_index in range(participant_count-1):
        if row_index != 0 and row_index != entries_per_slide and row_index % entries_per_slide == 0:
            duplicated_slide = slide.Duplicate().Item(1)
            slide = duplicated_slide  
            group_objects = collect_group_shapes(slide)  
            
            for group in group_objects[1:]:
                group.Top -= vertical_movement_per_entry * entries_per_slide

            if presentation.SlideShowWindow:
                presentation.SlideShowWindow.View.Next()
                time.sleep(5)  

        group_objects[1].Copy()
        pasted_group = slide.Shapes.Paste()
        pasted_group.ZOrder(1)
        vertical_adjustment = vertical_movement_per_entry * row_index
        horizontal_adjustment = horizontal_movement_per_entry

        # Populate the new group
        row = df.iloc[row_index].tolist()
        populate_group(pasted_group, row)
        time.sleep(.75)

        pasted_group.Top = group_objects[1].Top + vertical_adjustment
        pasted_group.Left = group_objects[1].Left + horizontal_adjustment


    # Ensure group_objects is updated for the final operations
    group_objects = collect_group_shapes(slide)

    duplicated_slide = slide.Duplicate().Item(1)
    slide = duplicated_slide  
    group_objects = collect_group_shapes(slide) 

    participants_on_last_slide = participant_count % entries_per_slide if participant_count % entries_per_slide != 0 else entries_per_slide

    for group in group_objects[1:]:
        group.Top -= vertical_movement_per_entry * participants_on_last_slide

    if presentation.SlideShowWindow:
                presentation.SlideShowWindow.View.Next()
                time.sleep(5)  
    


if __name__ == "__main__":
    main()
