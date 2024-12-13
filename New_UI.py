import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import random

# Constants
MAX_FORCE = 10  # Maximum acceptable force (in Newtons)
CONNECTOR_TYPES = {
    "Type A": 4,  # 4 contact points
    "Type B": 6,  # 6 contact points
    "Type C": 8   # 8 contact points
}

# Global Variables
is_running = False
force_data = []
force_value_1 = 0
force_value_2 = 0
relative_resistance_1 = 0
relative_resistance_2 = 0
calibration_slope = 0
calibration_intercept = 0
time_data = []
connector_status = {}
current_connector_type = "Type A"
start_time = None
force_values = []  # Real-time force values for bar graph
sensor_id = ""  # Placeholder for SensorID
average_force = 0  # To store the calculated average force

# Helper function for placeholder behavior
def clear_placeholder(event, entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)

def add_placeholder(event, entry, placeholder):
    if not entry.get():
        entry.insert(0, placeholder)

# Function to simulate real-time data
def simulate_force_data(num_points):
    return [random.uniform(5, 15) for _ in range(num_points)]

# Update Force vs Time Graph
def update_force_time_graph():
    force_ax.clear()
    force_ax.plot(time_data, force_data, label="Force (N)", color="blue")
    force_ax.set_title("Force vs Time")
    force_ax.set_xlabel("Time (s)")
    force_ax.set_ylabel("Force (N)")
    force_ax.legend()
    force_canvas.draw()

# Update Contact Points Graph
def update_contact_points_graph():
    contact_ax.clear()
    contact_ax.bar(range(1, len(force_values) + 1), force_values, color=["green" if f <= MAX_FORCE else "red" for f in force_values])
    contact_ax.set_title("Contact Points Force")
    contact_ax.set_xlabel("Contact Points")
    contact_ax.set_ylabel("Force (N)")
    contact_canvas.draw()

# Update Force Table
def update_force_table(forces):
    global average_force
    for i, force in enumerate(forces):
        color = "green" if force <= MAX_FORCE else "red"
        connector_status[i].config(
            text=f"CP{i+1} – {force:.2f} N",
            background=color,
            foreground="white"
        )
    # Calculate average force
    average_force = sum(forces) / len(forces) if forces else 0
    # Display average force in the output label
    avg_force_label.config(text=f"Average Force: {average_force:.2f} N")

# Real-Time Monitoring Thread
def real_time_monitoring():
    global is_running, start_time

    num_contact_points = CONNECTOR_TYPES[current_connector_type]
    start_time = time.time()
    
    while is_running:
        elapsed_time = time.time() - start_time
        new_force_data = simulate_force_data(num_contact_points)
        
        # Update data
        force_values[:] = new_force_data  # Update global force values
        force_data.append(sum(new_force_data) / len(new_force_data))
        time_data.append(elapsed_time)
        
        update_force_table(new_force_data)
        update_force_time_graph()
        update_contact_points_graph()
        time.sleep(1)

# Control Functions
def start_monitoring():
    global is_running
    if is_running:
        return
    if validate_required_fields():
        is_running = True
        status_var.set("Monitoring Started")
        threading.Thread(target=real_time_monitoring, daemon=True).start()
        error_label.config(text="")  # Clear error message if everything is valid
    else:
        error_label.config(text="Error: Please fill in all required fields.")

def stop_monitoring():
    global is_running
    is_running = False
    status_var.set("Monitoring Stopped")
    error_label.config(text="")  # Clear error message

def reset_monitoring():
    global is_running, force_data, time_data, force_values, force_1_entry, force_2_entry, relative_resistance_1_entry, relative_resistance_2_entry, sensor_id_entry, outcome_label, average_force
    if validate_required_fields():
        is_running = False
        force_data.clear()
        time_data.clear()
        force_values.clear()
        force_1_entry.delete(0, tk.END)
        force_2_entry.delete(0, tk.END)
        relative_resistance_1_entry.delete(0, tk.END)
        relative_resistance_2_entry.delete(0, tk.END)
        sensor_id_entry.delete(0, tk.END)  # Clear SensorID entry field
        
        # Reset Outcome Label and Average Force
        outcome_label.config(text="Slope (m): --, Intercept (b): --")
        avg_force_label.config(text="Average Force: -- N")
        
        force_ax.clear()
        force_canvas.draw()
        contact_ax.clear()
        contact_canvas.draw()
        for lbl in connector_status.values():
            lbl.config(text="Not Measured", background="red")
        status_var.set("System Reset")

        initialize_contact_points()
        update_contact_points_graph()
        error_label.config(text="")  # Clear error message
    else:
        error_label.config(text="Error: Please fill in all required fields.")

def reset_on_connector_change(*args):
    global current_connector_type
    current_connector_type = selected_type_var.get()
    reset_monitoring()  # Reset everything when connector type is changed

def calibrate_values():
    global calibration_slope, calibration_intercept
    if validate_required_fields():
        try:
            f1 = float(force_1_entry.get())
            f2 = float(force_2_entry.get())
            r1 = float(relative_resistance_1_entry.get())
            r2 = float(relative_resistance_2_entry.get())
            
            calibration_slope = (f2 - f1) / (r2 - r1)
            calibration_intercept = f1 - calibration_slope * r1
            outcome_label.config(text=f"Slope (m): {calibration_slope:.2f}, Intercept (b): {calibration_intercept:.2f}")
            error_label.config(text="")  # Clear error message
        except ValueError:
            status_var.set("Error: Please enter valid calibration values.")
            error_label.config(text="Error: Invalid calibration values.")
    else:
        error_label.config(text="Error: Please fill in all required fields.")

# Validate required fields
def validate_required_fields():
    if sensor_id_entry.get() == "Enter Sensor ID" or not force_1_entry.get() or not force_2_entry.get() or not relative_resistance_1_entry.get() or not relative_resistance_2_entry.get():
        return False
    return True

# Initialize Contact Points Display
def initialize_contact_points():
    for widget in force_frame.winfo_children():
        widget.destroy()
    connector_status.clear()
    num_points = CONNECTOR_TYPES[current_connector_type]
    for i in range(num_points):
        lbl = ttk.Label(force_frame, text=f"CP{i+1} – Not Measured", background="red", foreground="white")
        lbl.grid(row=i // 4, column=i % 4, padx=10, pady=5)
        connector_status[i] = lbl

# GUI Setup
root = tk.Tk()
root.title("Codecrafters Project: Real-Time Monitoring")
root.geometry("1200x800")

# Create a canvas and a scrollbar for scrolling
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas for all the content
content_frame = ttk.Frame(canvas)

# Pack the scrollbar and canvas
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Create a window inside the canvas to be scrollable
canvas.create_window((0, 0), window=content_frame, anchor="nw")

# Update the scroll region to the size of the content frame
content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Status Display
status_var = tk.StringVar(value="System Ready")
ttk.Label(content_frame, textvariable=status_var, font=("Arial", 12, "bold")).pack(pady=5)

# Connector Type Selection and Sensor ID
type_frame = ttk.LabelFrame(content_frame, text="Connector Type")
type_frame.pack(pady=5, padx=10, fill="x")

selected_type_var = tk.StringVar(value=current_connector_type)
ttk.OptionMenu(type_frame, selected_type_var, current_connector_type, *CONNECTOR_TYPES.keys(), command=reset_on_connector_change).pack(side="left")

# Sensor ID input
ttk.Label(type_frame, text="Sensor ID:").pack(side="left", padx=(20, 5))
sensor_id_entry = ttk.Entry(type_frame, width=20)
sensor_id_entry.pack(side="left")
sensor_id_entry.insert(0, "Enter Sensor ID")  # Placeholder text
sensor_id_entry.bind("<FocusIn>", lambda event: clear_placeholder(event, sensor_id_entry, "Enter Sensor ID"))
sensor_id_entry.bind("<FocusOut>", lambda event: add_placeholder(event, sensor_id_entry, "Enter Sensor ID"))

# Calibration Input
calibration_frame = ttk.LabelFrame(content_frame, text="Calibration Inputs")
calibration_frame.pack(pady=10, padx=10, fill="x")

def add_input_field(label, row, column):
    ttk.Label(calibration_frame, text=label).grid(row=row, column=column, padx=10)
    entry = ttk.Entry(calibration_frame)
    entry.grid(row=row, column=column + 1)
    return entry

force_1_entry = add_input_field("Force Value 1:", 0, 0)
force_2_entry = add_input_field("Force Value 2:", 0, 2)
relative_resistance_1_entry = add_input_field("Relative Resistance 1:", 1, 0)
relative_resistance_2_entry = add_input_field("Relative Resistance 2:", 1, 2)

# Calibrate button
ttk.Button(calibration_frame, text="Calibrate", command=calibrate_values).grid(row=2, column=1, pady=5, columnspan=2)

# Outcome Section inside Calibration Frame
ttk.Label(calibration_frame, text="Output Outcome", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, pady=5)
outcome_label = ttk.Label(calibration_frame, text="Slope (m): --, Intercept (b): --", font=("Arial", 10))
outcome_label.grid(row=4, column=0, columnspan=2, pady=5)

# Force Table and Average Force inside Force Frame
force_frame = ttk.LabelFrame(content_frame, text="Force Table")
force_frame.pack(pady=10, padx=10, fill="x")

# Initialize Force Table (contact points)
initialize_contact_points()

# Average Force Output
avg_force_label = ttk.Label(force_frame, text="Average Force: -- N", font=("Arial", 10))
avg_force_label.grid(row=1, column=0, columnspan=4, pady=5)

# Graph Display
graph_frame = ttk.Frame(content_frame)
graph_frame.pack(fill="both", expand=True)

# Force vs Time Graph
force_fig = Figure(figsize=(4, 4), dpi=100)
force_ax = force_fig.add_subplot(111)
force_canvas = FigureCanvasTkAgg(force_fig, master=graph_frame)
force_canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

# Contact Points Graph
contact_fig = Figure(figsize=(4, 4), dpi=100)
contact_ax = contact_fig.add_subplot(111)
contact_canvas = FigureCanvasTkAgg(contact_fig, master=graph_frame)
contact_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

# Control Buttons (Outside the scrollable area)
control_frame = ttk.LabelFrame(root, text="Controls")
control_frame.pack(pady=10)

ttk.Button(control_frame, text="Start", command=start_monitoring).pack(side="left", padx=10)
ttk.Button(control_frame, text="Stop", command=stop_monitoring).pack(side="left", padx=10)
ttk.Button(control_frame, text="Reset", command=reset_monitoring).pack(side="left", padx=10)

# Error Message Box
error_label = ttk.Label(root, text="", foreground="red", font=("Arial", 10))
error_label.pack(pady=10)

# Run GUI
root.mainloop()
