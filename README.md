# Track Results Display System

A real-time web application for displaying athletic competition results, designed for track and field events.

<img width="811" alt="Track+Results+Display+Demo" src="https://github.com/user-attachments/assets/9f847464-30a8-4196-8102-45a15c1db2cc" />

## Features

- **Real-time Updates**: Automatically fetches the latest results from DLV (German Athletics Federation) website
- **Dual Interface**: Admin control panel and clean display view for projection systems
- **Dynamic Content**: Adapts to different event types and result formats automatically
- **Visual Feedback**: Highlights changes and updates with smooth animations
- **Pagination Support**: Handles events with many participants through intuitive navigation
- **Responsive Design**: Works on various screen sizes and resolutions

## Quick Start

### Prerequisites

- Python 3.8+
- Pip (Python package manager)
- Modern web browser

### Installation

1. Clone this repository or download the files:
   ```bash
   git clone https://github.com/RobTech01/DigitaleErgebnistafel.git
   cd DigitaleErgebnistafel
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:
   ```bash
   python app.py
   ```

4. Access the application:
   - Control Panel: http://localhost:5000/
   - Display View: http://localhost:5000/display

## Usage Guide

1. **Set up the data source**:
   - Enter a valid DLV results URL in the control panel
   - Example: `https://ergebnisse.leichtathletik.de/Competitions/CurrentList/617972/12005`
   - Click "Load Heats"

2. **Select an event to display**:
   - Choose from the available heats in the list
   - Set update interval if needed (default is 3 seconds)

3. **Start the display**:
   - Click "Start Displaying"
   - Use "Open Display Window" to launch the display view
   - Position the display window on your presentation screen

4. **Control the presentation**:
   - Use page navigation buttons to cycle through results if needed
   - Monitor the preview panel to see what's currently displayed
   - Use "Stop" to pause updates when needed

## Configuration Options

The application can be configured by editing these files:

- **app.py**: Main application settings
  ```python
  # Set to True for detailed logging, False for production
  DEBUG_MODE = False
  
  # Port to run the application on
  port = int(os.environ.get('PORT', 5000))
  ```

- **display.html**: Display view configuration
  ```javascript
  // Maximum results shown per page
  const MAX_RESULTS_PER_PAGE = 8;
  
  // Update interval in milliseconds
  const UPDATE_INTERVAL = 3000;
  ```

## Styling Customization

The display view can be extensively customized to match event branding or specific requirements:

### Basic Color Scheme

Modify the CSS in `display.html` to change the look and feel:

```css
/* Header/title colors */
.header-row {
    background-color: #003366; /* Change to your primary brand color */
    color: white;
}

/* Result row styling */
.result-row {
    background-color: #f5f5f5; /* Light background for rows */
}
.result-row:nth-child(odd) {
    background-color: #e9e9e9; /* Alternate row color */
}

/* Highlight colors for updates */
.result-row.highlight {
    background-color: #fffacd; /* Highlighted row background */
}
.result-time.updated {
    color: #cc0000; /* Updated value text color */
}
```

### Layout Customization

Adjust the grid layout for different column emphasis:

```css
/* Change column width distribution */
.header-row {
    grid-template-columns: 0.5fr 2.5fr 1fr 1fr 1fr 0.5fr;
}
```

### Font and Typography

Customize the typography for better readability on large screens:

```css
/* Font selection */
body {
    font-family: 'Roboto Condensed', Arial, sans-serif;
}

/* Size adjustments */
.primary-value {
    font-size: 24px; /* Larger text for main values */
}
.event-title {
    font-size: 36px; /* Larger event title */
    letter-spacing: 1px; /* Spacing for emphasis */
}
```

### Animation Effects

Modify transition effects for different visual impact:

```css
/* Change transition speeds */
.page-container {
    transition: opacity 1.2s ease; /* Slower fade between pages */
}

/* Adjust highlight animation */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px); /* Slide from left instead of top */
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
```


## Advanced Use Cases

- **Multi-Screen Setup**: Run multiple instances on different ports to display various heats simultaneously
- **Video Integration**: Use the transparent background mode for integrating with video production systems
- **Kiosk Display**: Set up a dedicated machine in kiosk mode for continuous display

## Troubleshooting

- **No heats found**: Verify the URL is correct and accessible in a browser
- **Display not updating**: Check for network connectivity issues or try restarting the monitor
- **Data format issues**: The DLV website may have changed structure; check application logs

Enable debug logging by setting `DEBUG_MODE = True` in app.py for detailed diagnostics.

## Requirements

See `requirements.txt` for a complete list of dependencies.

Core components:
- Flask 2.3.2
- Requests 2.31.0
- BeautifulSoup4 4.12.2
- Pandas 2.0.3
