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
            group_shape_list.append(shape)
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
        if not content_index < len(contents)+1:
            logging.error("there are more content items than items in the group")
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




def update_powerpoint_with_data(dataframes, slide):

    heat_name, df = next(iter(dataframes.items()))


    for i, content_titles in enumerate(df):
        content_title_placeholder = slide.Shapes(i+2)
        content_title_placeholder.TextFrame.TextRange.Text = content_titles
        
    data_flat = df.astype(str).values.flatten()

    placeholder_count = scan_for_shapes(slide)

    non_data_fields = 11
    content_for_slides = [data_flat[i:i + placeholder_count-11] for i in range(0, len(data_flat), placeholder_count-non_data_fields)]

    for content_packet_per_slide in content_for_slides:
        for i, content in enumerate(content_packet_per_slide):
            content_placeholder = slide.Shapes(i+2+10)
            content_placeholder.TextFrame.TextRange.Text = content



def main():
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617972/12005"
    dataframes = scrape_dlv_data(url)

    pythoncom.CoInitialize()  # Initialize the COM library

    try:
        already_open_powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        presentation = already_open_powerpoint.ActivePresentation
    except AttributeError:
        logging.critical("No active presentation found.")
    
    active_slide = 1
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

    populate_group(group_header, content_headers)



    available_rows = df.shape[0]
    entries_per_row = df.shape[1]


    for row_index in range(0, available_rows-1):
        row = df.iloc[row_index].tolist()
        populate_group(group_objects[row_index+1], row)

        time.sleep(1)
        group_objects[row_index+1].Copy()
                
        # Paste the copied group onto the same slide
        # The Paste method returns a ShapeRange object representing the pasted shapes
        pasted_group = slide.Shapes.Paste()
        pasted_group.Left = group_objects[row_index+1].Left + 0  # Offset by 20 points down
        pasted_group.Top = group_objects[row_index+1].Top + 44  # Offset by 20 points down

        group_objects = collect_group_shapes(slide)
    
    row = df.iloc[-1].tolist()
    populate_group(group_objects[-1], row)
    print("Group copied and pasted.")

    #for group in group_objects[1:]:
        #print(f"Selecting group: {group.Name}")
        #group.Select(True) 
        
    #print(f"Shapes selected: {already_open_powerpoint.ActiveWindow.Selection.ShapeRange.Count}")
            






    #for i in range(1,available_rows)


    #for index, content_per_row in df.iterrows():
        #print(content_per_row.tolist())


    

    #process_group_shape(group_objects, )


    #update_powerpoint_with_data(dataframes, slide)

if __name__ == "__main__":
    main()
