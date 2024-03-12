
import tkinter as tk
from tkinter import ttk

# Initialize main window
root = tk.Tk()
root.title("Athletics Results")
root.geometry("800x600")  # Window size

# Custom styling with ttk.Style
style = ttk.Style()
style.theme_use("clam")  # Using 'clam' theme for a nicer look

# Configure Treeview style for headings and rows
style.configure("Treeview.Heading", font=('Roboto', 10, 'bold'), background="#cccccc", foreground="#333333")
style.configure("Treeview", font=('Roboto', 10), background="#f5f5f5", foreground="#333333", rowheight=25)
# Highlight selection
style.map("Treeview", background=[('selected', '#0078d7')], foreground=[('selected', 'white')])

# Sample data for demonstration
heat_name = "10:20 Vorlauf 1"
headers = ["Rang", "Bib", "Name", "Verein", "LV", "JG", "Ergebnis", "Klasse", "Info"]
entries = [
    {"Rang": "1", "Bib": "342", "Name": "Menk Rene Pascal", "Verein": "LAZ Wuppertal", "LV": "NO", "JG": "1983", "Ergebnis": "7,45", "Klasse": "M40", "Info": ""},
    # Add more entries based on your data structure
]

# Function to create a block for each heat
def create_heat_block(parent, heat_name, headers, entries):
    heat_frame = tk.Frame(parent, bd=2, relief=tk.GROOVE, bg="#e0e0e0")  # Using a light grey background
    heat_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)

    # Heat name label
    tk.Label(heat_frame, text=heat_name, fg="white", bg="#455a64", font=('Roboto', 12, 'bold')).pack(fill=tk.X)

    # Creating a Treeview within each heat frame to display the entries
    tree = ttk.Treeview(heat_frame, columns=headers, show="headings")
    for header in headers:
        tree.heading(header, text=header)
        tree.column(header, anchor=tk.CENTER)
    
    # Inserting data into the Treeview
    for entry in entries:
        row = tuple(entry[h] for h in headers)
        tree.insert('', tk.END, values=row)
    
    tree.pack(expand=True, fill='both')

# Global header for the application
header_frame = tk.Frame(root, bg="#455a64")
header_frame.pack(fill=tk.X)
header_label = tk.Label(header_frame, text="Athletics Results Display", fg="white", bg="#455a64", font=('Roboto', 16, 'bold'))
header_label.pack(pady=10)

# Create a heat block (as an example, replicate as needed for each heat)
create_heat_block(root, heat_name, headers, entries)

# Start the GUI event loop
root.mainloop()
