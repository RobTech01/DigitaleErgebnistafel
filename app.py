import os
import threading
import time
import logging
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from data_scraper import DLVResultsScraper

# ============================
# LOGGING CONFIGURATION
# ============================
# Set to True to enable detailed logging, False to show only errors
DEBUG_MODE = False

# Configure logging based on debug mode
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,  # Show all logs in debug mode
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Output to console
            logging.FileHandler('app.log')  # Also save to file
        ]
    )
else:
    logging.basicConfig(
        level=logging.CRITICAL,  # Only show errors in production mode
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Output to console only
        ]
    )

logger = logging.getLogger(__name__)
logger.info("Application starting...")

# Global variables
is_running = False
update_thread = None
thread_lock = threading.Lock()
current_data = {
    'data': [],
    'columns': [],
    'heat_name': '',
    'timestamp': '',
    'currentPage': 0
}

# Initialize Flask app
app = Flask(__name__)


# Routes
@app.route('/')
def control_panel():
    """Render the control panel template"""
    return render_template('control.html')

@app.route('/display')
def display():
    """Render the display template"""
    return render_template('display.html')

@app.route('/api/heats', methods=['GET'])
def get_heats():
    """Get available heats from the DLV website"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    try:
        scraper = DLVResultsScraper()
        heats = scraper.get_available_heats(url)
        return jsonify({'heats': heats})
    except Exception as e:
        logger.error(f"Error getting heats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring a specific heat"""
    global update_thread, is_running
    
    data = request.json
    url = data.get('url')
    heat_name = data.get('heat')
    interval = data.get('interval', 3)
    
    if not url or not heat_name:
        return jsonify({'error': 'URL and heat name required'}), 400
    
    # Stop existing thread if running
    stop_current_thread()
    
    # Reset current page
    with thread_lock:
        current_data['currentPage'] = 0
    
    # Start new monitoring thread
    logger.info(f"Starting monitoring thread for heat: {heat_name}")
    is_running = True
    update_thread = threading.Thread(
        target=update_data_thread, 
        args=(url, heat_name, interval)
    )
    update_thread.daemon = True
    update_thread.start()
    
    return jsonify({'success': True, 'message': f'Monitoring started for {heat_name}'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring thread"""
    global is_running
    
    result = stop_current_thread()
    return jsonify({'success': result})

@app.route('/api/data')
def get_data():
    """Get the current data"""
    with thread_lock:
        return jsonify(current_data)

@app.route('/api/change-page', methods=['POST'])
def change_page():
    """Change the current page being displayed"""
    global current_data
    
    data = request.json
    page = data.get('page', 0)
    
    with thread_lock:
        current_data['currentPage'] = page
    
    return jsonify({'success': True})

# Helper functions
def update_data_thread(url, heat_name, interval):
    """Thread function to periodically update data"""
    global current_data, is_running
    
    scraper = DLVResultsScraper()
    
    while is_running:
        try:
            logger.info(f"Fetching data for heat: {heat_name}")
            data = scraper.get_heat_results(url, heat_name)
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            with thread_lock:
                current_data['data'] = data['data']
                current_data['columns'] = data['columns']
                current_data['heat_name'] = heat_name
                current_data['timestamp'] = timestamp
                # Preserve the currentPage setting
                
            logger.info(f"Updated data with {len(data['data'])} results")
            
        except Exception as e:
            logger.error(f"Error updating data: {e}")
        
        # Sleep for the specified interval
        time.sleep(interval)

def stop_current_thread():
    """Stop the current update thread if running"""
    global update_thread, is_running
    
    if update_thread and update_thread.is_alive():
        logger.info("Stopping monitoring thread")
        is_running = False
        update_thread.join(timeout=2.0)
        update_thread = None
        return True
    
    return False

# Main entry point
if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=DEBUG_MODE)