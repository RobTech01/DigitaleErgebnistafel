
# Digitale Ergebnistafel für Leichtathletik-Wettkämpfe

## Description
**Digitale Ergebnistafel für Leichtathletik-Wettkämpfe** is a Python-based automation tool designed to create dynamic digital result boards for track events. Leveraging HTML web scraping, it extracts essential information from the official DLV results page for most national events, facilitating its incorporation into live streams with minimal manual intervention. Utilizing PowerPoint for its ease of design, the tool streamlines the process of updating live-stream displays with real-time event results.

## Motivation
The project was initiated to digitize results and graphically display lane occupations for track events, enhancing the presentation of live-streamed track events by automating the update process with real-time data.

## Installation
- **Requirements**: Python 3.x is required.
- **Dependencies**: Install all necessary dependencies using the provided `requirements.txt` file with the command:  
  `pip install -r requirements.txt`.
- **PowerPoint Template**: Ensure the PowerPoint template is in the same folder as `main.py`.

## Usage
Note: The URL for the results page is currently hardcoded into the Python code. Future updates will allow specifying the URL directly via a CLI command.

### PowerPoint Design Requirements
- Colors and elements within the PowerPoint slides are customizable.
- Elements can be added but should not be grouped.
- The structure of Slide 2 must remain consistent to ensure proper functionality.

## Features and Benefits
- **Ease of Redesign and Adjustment**: Utilizes PowerPoint for straightforward customization.
- **Autonomous Operation**: Once initiated, it runs autonomously to scrape data and populate the presentation template.
- **Iterative Updates**: Designed to iteratively update presentations with new data as it becomes available.

## Roadmap and Future Plans
- Introduce a CLI command for specifying the URL of the results page.
- Improve the duplication process to eliminate visual glitches by cloning data fields outside the viewport.

## License
This project is licensed under the **GNU General Public License v3.0**. A copy of the license can be found in the LICENSE file within the project repository.

## Contact Information
For support, questions, or collaboration opportunities, please contact via GitHub.
