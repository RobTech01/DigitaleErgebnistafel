import win32com.client
import pythoncom
from package.data_scraping import scrape_data
from package.powerpoint_decoder import get_placeholder_indexes, dataframe_to_slides_content
import time

def update_powerpoint_with_data(dataframes, slide):
    pythoncom.CoInitialize()  # Initialize the COM library
    
    title_placeholder = slide.Shapes.Title
    heat_name, df = next(iter(dataframes.items()))
    title_placeholder.TextFrame.TextRange.Text = heat_name

    placeholder_count = 0

    for shape in slide.Shapes:
        if hasattr(shape, 'PlaceholderFormat'):
            placeholder_count += 1
            #print(f"Placeholder found: ID {shape.Id}, Name: {shape.Name}")

    print(f"Total placeholders on slide: {placeholder_count}")

    for i, content_titles in enumerate(df):
        content_title_placeholder = slide.Shapes(i+2)
        content_title_placeholder.TextFrame.TextRange.Text = content_titles
        
    data_flat = df.astype(str).values.flatten()

    non_data_fields = 11
    content_for_slides = [data_flat[i:i + placeholder_count-11] for i in range(0, len(data_flat), placeholder_count-non_data_fields)]

    for content_packet_per_slide in content_for_slides:
        for i, content in enumerate(content_packet_per_slide):
            print(content)
            content_placeholder = slide.Shapes(i+2+10)
            content_placeholder.TextFrame.TextRange.Text = content
        time.sleep(5)

    

def main():
    url = "https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617972/12005"
    dataframes = scrape_data(url)

    already_open_powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    presentation = already_open_powerpoint.ActivePresentation

    first_slide = 1
    slide = presentation.Slides(first_slide)

    update_powerpoint_with_data(dataframes, slide)

if __name__ == "__main__":
    main()
