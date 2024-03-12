import tkinter as tk
from tkinter import ttk

def display_results(dataframes):
    root = tk.Tk()
    root.title("Athletics Results")
    root.geometry("800x600")
    
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=('Roboto', 10, 'bold'), background="#cccccc", foreground="#333333")
    style.configure("Treeview", font=('Roboto', 10), background="#f5f5f5", foreground="#333333", rowheight=25)
    style.map("Treeview", background=[('selected', '#0078d7')], foreground=[('selected', 'white')])
    
    for heat_name, df in dataframes.items():
        headers = df.columns.tolist()
        entries = df.to_dict('records')
        
        heat_frame = tk.Frame(root, bd=2, relief=tk.GROOVE, bg="#e0e0e0")
        heat_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        tk.Label(heat_frame, text=heat_name, fg="white", bg="#455a64", font=('Roboto', 12, 'bold')).pack(fill=tk.X)
        
        tree = ttk.Treeview(heat_frame, columns=headers, show="headings")
        for header in headers:
            tree.heading(header, text=header)
            tree.column(header, anchor=tk.CENTER, width=120)
        
        for entry in entries:
            row = tuple(entry[h] for h in headers)
            tree.insert('', tk.END, values=row)
        
        tree.pack(expand=True, fill='both')
    
    root.mainloop()
