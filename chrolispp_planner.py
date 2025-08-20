import tkinter as tk
from tkinter import messagebox
from math import floor

class LEDIndexError(Exception):
    """Exception raised when LED index is out of range."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.message}"

class InvalidParameterError(Exception):
    """Exception raised when generally a parameter is invalid."""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.message}"

LED_INDEX_LABEL = "LED index (1-6)"
FREQUENCY_LABEL = "Frequency (Hz)"
TOTAL_DURATION_LABEL = "Total Duration (s)"
PULSE_DURATION_LABEL = "Pulse Duration (ms)"
POWER_LABEL = "Power (0-1000=0-100.0%)"

class CSVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrolispp Planner")

        # Input fields
        self.entries = {}
        parameters = [LED_INDEX_LABEL, FREQUENCY_LABEL, TOTAL_DURATION_LABEL, PULSE_DURATION_LABEL, POWER_LABEL]
        for i, label in enumerate(parameters):
            tk.Label(root, text=label).grid(row=0, column=i)
            entry = tk.Entry(root, width=10)
            entry.grid(row=1, column=i)
            self.entries[label] = entry

        plus_button = tk.Button(root, text="+", command=self.add_line)
        plus_button.grid(row=1, column=len(parameters), padx=10)

        remove_button = tk.Button(root, text="-", command=self.remove_last_line)
        remove_button.grid(row=1, column=len(parameters)+1, padx=10)

        self.output_text = tk.Text(root, height=10, width=50)
        self.output_text.grid(row=2, column=0, columnspan=4, pady=10)
        self.output_text.config(state=tk.DISABLED)

        # Store lines
        self.csv_lines = []

    def get_line(self):
            # Get and validate input values
            led_index = int(self.entries[LED_INDEX_LABEL].get())
            if led_index < 1 or led_index > 6:
                raise LEDIndexError(f"Invalid LED index: {led_index}.")
            led_index -= 1  # convert to 0-5
            freq = float(self.entries[FREQUENCY_LABEL].get())
            total = float(self.entries[TOTAL_DURATION_LABEL].get())
            pulse_duration_ms = int(self.entries[PULSE_DURATION_LABEL].get())
            power = int(self.entries[POWER_LABEL].get())
            total_duration_ms = int(floor(total*1000.0))
            # detect break:
            #   power should be 0
            if power == 0:
                line = f"{led_index},0,{total_duration_ms},1,0"
                return line
            # check pulse duration is not too short or too long
            #   too short when < 1 ms (0 ms)
            cycle_duration_ms = int(floor(1000.0/freq))  # in milliseconds
            if pulse_duration_ms < 1 or pulse_duration_ms > cycle_duration_ms:
                raise InvalidParameterError(f"Pulse duration invalid: should be 0 < {pulse_duration_ms} <= {cycle_duration_ms} ms")
            if power < 0 or power > 1000:
                raise InvalidParameterError(f"Power invalid: should be 0 <= {power} <= 1000")
            if freq == 0:
                raise InvalidParameterError(f"Frequency invalid: 0 Hz for non-break (power != 0) segment.")
            # Calculate parameters
            break_duration_ms = cycle_duration_ms - pulse_duration_ms
            assert break_duration_ms >= 0 
            n_cycles = int(total_duration_ms//cycle_duration_ms) 

            # Create CSV-compatible line
            line = f"{led_index},{pulse_duration_ms},{break_duration_ms},{n_cycles},{power}"
            return line
    
    def add_line(self):
        try:
            line = self.get_line()
            self.csv_lines.append(line)
            # Update output field
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "\n".join(self.csv_lines))
            self.output_text.config(state=tk.DISABLED)
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter valid integers in all fields.")
    def remove_last_line(self):
        if self.csv_lines:
            self.csv_lines.pop()
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "\n".join(self.csv_lines))
            self.output_text.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("No lines", "There are no lines to remove.")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVApp(root)
    root.mainloop()
