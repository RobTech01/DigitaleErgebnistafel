import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import time
import logging

logging.basicConfig(level=logging.WARNING)

def skip_to_page(presentation, slide_number):

    num_slides = presentation.Slides.Count
    assert num_slides >= slide_number, f"you are trying to skip to slide {slide_number}, the highest page number is {num_slides}"

    try:
        slide_show_view = presentation.SlideShowWindow.View
        #slide_show_view.Next()
        slide_show_view.GotoSlide(slide_number)
    except AttributeError:
        logging.critical("No active slideshow found.")

def scan_for_shapes(slide, debug=False):
    placeholder_count = 0

    for shape in slide.Shapes:
        if hasattr(shape, 'PlaceholderFormat'):
            placeholder_count += 1
            logging.debug(f"scan_for_shapes found a Placeholder: ID {shape.Id}, Name: {shape.Name}")  

    logging.debug(f"scan_for_shapes found a total of: {placeholder_count} Placeholders")

    return placeholder_count

def collect_group_shapes(slide):
    group_shape_list = []
    
    for shape in slide.Shapes:
        if "Group" in shape.Name:
            group_shape_list.insert(0, shape)  #win32 detects from background layer to the front. we want the header at index 0
            logging.debug(f"collect_group_shapes found a Group: ID {shape.Id}, Name: {shape.Name}")
    
    return group_shape_list

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

def populate_group(group, contents):

    assert "Group" in group.Name, "you are trying to add text to a non group object"

    content_index = 0
    for placeholder_index in range(1, group.GroupItems.Count+1):  # PowerPoint collections are 1-indexed
        if content_index >= len(contents):
            logging.error("there are more group items than content")
            break
        content_placeholder = group.GroupItems.Item(placeholder_index)
        if not "TextBox" in content_placeholder.Name:
            logging.debug("skipped adding content to a rectangle")
            content_index -= 1
            pass

        content = contents[content_index]
        content_placeholder.TextFrame.TextRange.Text = content
        content_index += 1
    
    assert content_index == len(contents), "not all content has been distributed in populate_group()"


def add_content_to_group_shapes(group_shape_list, content_per_column):
    for group_shape in group_shape_list:

        assert len(content_per_column) == group_shape.GroupItems.Count, "content and group must have the same amount of elements"

        for i, content_placeholder in enumerate(group_shape.GroupItems):
            if "TextBox" in content_placeholder.Name:
                content_placeholder.TextFrame.TextRange.Text = content_per_column[i]
            # Additional logic can be added here to ignore rectangles or perform other checks


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


    for row_index in range(0, participant_count-1):
        row = df.iloc[row_index].tolist()
        populate_group(group_objects[row_index+1], row)

        time.sleep(1)
        group_objects[row_index+1].Copy()
                
        # Paste the copied group onto the same slide
        # The Paste method returns a ShapeRange object representing the pasted shapes
        pasted_group = slide.Shapes.Paste()
        pasted_group.ZOrder(1)
        pasted_group.Left = group_objects[row_index+1].Left + 0  # Offset by 20 points down
        pasted_group.Top = group_objects[row_index+1].Top + 44  # Offset by 20 points down


        group_objects = collect_group_shapes(slide)
    
    row = df.iloc[-1].tolist()
    populate_group(group_objects[-1], row)
    print("Group copied and pasted.")

    content_groups = group_objects[1:]

    assert participant_count == df.shape[0], "there seems to be a different amount of rows and data entires"

    entries_per_slide = 8
    initial_slide_index = 2 
    movement_per_entry = 44  
    slides_needed = -(-participant_count // entries_per_slide) -1
            
    for slide_num in range(slides_needed):
        content_slide = presentation.Slides(initial_slide_index + slide_num)
        duplicated_slide = content_slide.Duplicate().Item(1)
        
        group_objects = collect_group_shapes(duplicated_slide)
        
        content_groups = group_objects[1:]
        
        if slide_num == slides_needed - 1:  # If it's the last slide
            adjustment_factor = participant_count % entries_per_slide or entries_per_slide
        else:
            adjustment_factor = entries_per_slide

        for group in content_groups:
            group.Top -= movement_per_entry * adjustment_factor

        if presentation.SlideShowWindow:
            presentation.SlideShowWindow.View.Next()
            time.sleep(5)  # Adjust the sleep time as needed


if __name__ == "__main__":
    main()
