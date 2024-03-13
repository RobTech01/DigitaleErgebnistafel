import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import time
import logging

logging.basicConfig(level=logging.WARNING)

def skip_to_page(presentation, slide_number):

    num_slides = presentation.Slides.Count
    assert num_slides <= slide_number, f"you are trying to skip to slide {slide_number}, the highest page number is {num_slides}"

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

def process_group_shape(group_shape_list, content_per_column):
    for group_shape in group_shape_list:

        assert "Group" in group_shape.Name, "you are trying to add text to a non group object"
        assert len(content_per_column) == group_shape.GroupItems.Count, "content and group must have the same amount of elements"

        for i, content_placeholder in enumerate(group_shape.GroupItems):
            if "TextBox" in content_placeholder.Name:
                content_placeholder.TextFrame.TextRange.Text = content_per_column[i]
            # Additional logic can be added here to ignore rectangles or perform other checks


def update_powerpoint_with_data(dataframes, slide):

    title_placeholder = slide.Shapes.Title
    heat_name, df = next(iter(dataframes.items()))
    title_placeholder.TextFrame.TextRange.Text = heat_name


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
        time.sleep(5)

    
        

def main():
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617972/12005"
    dataframes = scrape_dlv_data(url)

    pythoncom.CoInitialize()  # Initialize the COM library

    already_open_powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    presentation = already_open_powerpoint.ActivePresentation

    active_slide = 1
    slide = presentation.Slides(active_slide)

    scan_for_shapes(slide)
    group_objects = collect_group_shapes(slide)


    #update_powerpoint_with_data(dataframes, slide)

if __name__ == "__main__":
    main()
