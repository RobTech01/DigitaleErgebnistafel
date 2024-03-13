import win32com.client
import pythoncom
from package.data_scraping import scrape_dlv_data
import time

def skip_to_page(presentation, slide_number):
    # Ensure there's an active presentation and slideshow
    try:
        slide_show_view = presentation.SlideShowWindow.View
        #slide_show_view.Next()
        slide_number = 3
        slide_show_view.GotoSlide(slide_number)
    except AttributeError:
        print("No active slideshow found.")

def scan_for_shapes(slide):
    placeholder_count = 0

    for shape in slide.Shapes:
        if hasattr(shape, 'PlaceholderFormat'):
            placeholder_count += 1
            print(f"Placeholder found: ID {shape.Id}, Name: {shape.Name}")

    print(f"Total placeholders on slide: {placeholder_count}")

    return placeholder_count

def collect_group_shapes(slide):
    group_shapes = []
    
    for shape in slide.Shapes:
        if "Group" in shape.Name:
            group_shapes.append(shape)
    
    return group_shapes

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
    print(f"Group found: ID {group_objects[0].Id}, Name: {group_objects[0].Name}")


    #update_powerpoint_with_data(dataframes, slide)

if __name__ == "__main__":
    main()
