import tkinter as tk
from tkinter import messagebox
from math import floor
import warnings


class LEDIndexError(Exception):
    """Exception raised when LED index is out of range."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


class InvalidParameterError(Exception):
    """Exception raised when generally a parameter is invalid."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


class InvalidLineError(Exception):
    """Exception raised when a CSV line is invalid."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


LED_INDEX_LABEL = "LED index (1-6)"
FREQUENCY_LABEL = "Frequency (Hz)"
TOTAL_DURATION_LABEL = "Total Duration"
PULSE_DURATION_LABEL = "Pulse Duration"
POWER_LABEL = "Power (0-1000=0-100.0%)"
FREQUENCY_UNIT_LABEL = "Freq Unit"
TOTAL_DURATION_UNIT_LABEL = "TD Unit"
PULSE_DURATION_UNIT_LABEL = "PD Unit"

# TODO: add 6th column regarding us mode. Modify get_line (for writing to csv) and decode_line (for reading from csv) to handle this!


class ProtocolStep:
    def __init__(
        self,
        led_index: int,
        pulse_duration_us: int,
        time_between_pulses_us: int,
        n_pulses: int,
        brightness_value: int,
    ):
        """
        Docstring for __init__

        :param self: Description
        :param led_index: between 0 and 5, corresponding to the first to last (sixth) LED of the Chrolis.
        :type led_index: int
        :param pulse_duration_us: Description
        :type pulse_duration_us: int
        :param time_between_pulses_us: Description
        :type time_between_pulses_us: int
        :param n_pulses: Description
        :type n_pulses: int
        :param brightness_value: between (inclusive) 0 and 1000. A value of 123 corresponds to 12.3%, 1000 to 100.0%.
        :type brightness_value: int

        :raises InvalidParameterError: if one of the parameters is invalid.
        """
        self._is_int(led_index, "LED index")
        self._is_int(pulse_duration_us, "Pulse duration")
        self._is_int(time_between_pulses_us, "Time between pulses")
        self._is_int(n_pulses, "Number of pulses")
        self._is_int(brightness_value, "Brightness value")

        self._is_valid_led_index(led_index)
        self._is_valid_pulse_duration(pulse_duration_us)
        self._is_valid_time_between_pulses(time_between_pulses_us)
        self._is_valid_n_pulses(n_pulses)
        self._is_valid_brightness_value(brightness_value)

        self.led_index = led_index
        self.pulse_duration_us = pulse_duration_us
        self.time_between_pulses_us = time_between_pulses_us
        self.brightness_value = brightness_value
        self.n_pulses = (
            n_pulses if brightness_value > 0 else 1
        )  # for break, n_pulses is 1
        if self.n_pulses != n_pulses:
            warnings.warn(
                f"Number of pulses set to 1 for break (brightness value 0), received {n_pulses}"
            )

        if (
            self.pulse_duration_us % 1000 == 0
            and self.time_between_pulses_us % 1000 == 0
        ):
            self.us_mode = 0  # ms mode possible (relevant for printing)
        else:
            self.us_mode = 1  # us mode
        

    def _is_int(self, value, value_name: str):
        if not isinstance(value, int):
            raise InvalidParameterError(
                f"{value_name} should be int, received type {type(value)}, value {value}"
            )

    def _is_valid_led_index(self, led_index: int):
        if not (led_index >= 0 and led_index <= 5):
            raise InvalidParameterError(
                f"LED index should be in range [0, 5], received {led_index}"
            )

    def _is_valid_pulse_duration(self, pulse_duration_us: int):
        if not pulse_duration_us % 5 == 0:
            raise InvalidParameterError(
                f"Pulse duration value should be multiple of 5 us (Chrolis internal timer limitation), received {pulse_duration_us}"
            )

    def _is_valid_time_between_pulses(self, time_between_pulses_us: int):
        if not time_between_pulses_us % 5 == 0:
            raise InvalidParameterError(
                f"Time between pulses value should be multiple of 5 us (Chrolis internal timer limitation), received {time_between_pulses_us}"
            )

    def _is_valid_n_pulses(self, n_pulses: int):
        if not n_pulses > 0:
            raise InvalidParameterError(
                f"Number of pulses should be positive, received {n_pulses}"
            )

    def _is_valid_brightness_value(self, brightness_value: int):
        if not (brightness_value >= 0 and brightness_value <= 1000):
            raise InvalidParameterError(
                f"Brightness value should be in range [0, 1000], received {brightness_value}"
            )

    def get_frequency(self):
        """Get frequency in Hz."""
        cycle_duration_us = self.pulse_duration_us + self.time_between_pulses_us
        frequency_hz = 1_000_000.0 / cycle_duration_us
        return frequency_hz

    def get_total_duration(self):
        """Get total duration in seconds."""
        cycle_duration_us = self.pulse_duration_us + self.time_between_pulses_us
        total_duration_us = self.n_pulses * cycle_duration_us
        return total_duration_us / 1_000_000.0

    @classmethod
    def from_csv_line(cls, csv_line: str):
        """
        Create a ProtocolStep from a CSV line.

        :param csv_line: A line from a CSV file representing a protocol step. Should contain 5 (old format) or 6 (new format with us mode) comma-separated values.
        The values should be:
            - LED index (0-5)
            - Pulse duration (in ms if last column is absent or 0, else in us)
            - Time between pulses (in ms if last column is absent or 0, else in us)
            - Number of pulses (>0)
            - Brightness value (0-1000)
            - (optional) US mode (0 or 1)
        :type csv_line: str
        """
        # parse csv line
        entries = csv_line.strip().split(",")
        # check if contains 5 or 6 columns
        if len(entries) not in [5, 6]:
            raise InvalidLineError(
                f"CSV line should contain 5 or 6 comma-separated values, received {len(entries)}: {csv_line}"
            )
        led_index = int(entries[0])
        pulse_duration = int(entries[1])
        time_between_pulses = int(entries[2])
        n_pulses = int(entries[3])
        brightness_value = int(entries[4])
        us_mode = 0 if len(entries) == 5 else int(entries[5])
        # convert to us
        if us_mode == 0:
            pulse_duration *= 1000
            time_between_pulses *= 1000
        return cls(
            led_index, pulse_duration, time_between_pulses, n_pulses, brightness_value
        )

    def __str__(self):
        # Check if break = 0 brightness
        if self.brightness_value == 0:
            return f"Break duration: {self.time_between_pulses_us/1_000_000.} s"
        freq = self.get_frequency()
        total_duration = self.get_total_duration()
        power_str = str(self.brightness_value / 10.0)
        return f"LED {self.led_index + 1}, frequency: {freq:.1f} Hz, total duration: {total_duration:.1f} s, pulse duration: {self.pulse_duration_us} us, inter-pulse break duration: {self.time_between_pulses_us} us, number of pulses: {self.n_pulses}, power: {power_str} %"

    def to_csv_line(self):
        """Convert the ProtocolStep to a CSV-compatible line."""
        us_mode = (
            1
            if (
                self.pulse_duration_us % 1000 != 0
                or self.time_between_pulses_us % 1000 != 0
            )
            else 0
        )
        pulse_duration = (
            self.pulse_duration_us if us_mode == 1 else self.pulse_duration_us // 1000
        )
        time_between_pulses = (
            self.time_between_pulses_us
            if us_mode == 1
            else self.time_between_pulses_us // 1000
        )
        return f"{self.led_index},{pulse_duration},{time_between_pulses},{self.n_pulses},{self.brightness_value},{us_mode}"


class CSVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrolispp Planner")

        # Input fields
        self.entries = {}
        parameters = [
            LED_INDEX_LABEL,
            FREQUENCY_LABEL,
            FREQUENCY_UNIT_LABEL,
            TOTAL_DURATION_LABEL,
            TOTAL_DURATION_UNIT_LABEL,
            PULSE_DURATION_LABEL,
            PULSE_DURATION_UNIT_LABEL,
            POWER_LABEL,
        ]
        for i, label in enumerate(parameters):
            if label == TOTAL_DURATION_UNIT_LABEL:
                tk.Label(root, text="Unit").grid(row=0, column=i)
                self.duration_unit = tk.StringVar(value="s")
                tk.OptionMenu(root, self.duration_unit, "us", "ms", "s").grid(
                    row=1, column=i
                )
            elif label == PULSE_DURATION_UNIT_LABEL:
                tk.Label(root, text="Unit").grid(row=0, column=i)
                self.pulse_unit = tk.StringVar(value="ms")
                tk.OptionMenu(root, self.pulse_unit, "us", "ms", "s").grid(
                    row=1, column=i
                )
            elif label == FREQUENCY_UNIT_LABEL:
                tk.Label(root, text="Unit").grid(row=0, column=i)
                self.freq_unit = tk.StringVar(value="Hz")
                tk.OptionMenu(root, self.freq_unit, "mHz", "Hz").grid(row=1, column=i)
            else:
                tk.Label(root, text=label).grid(row=0, column=i)
                entry = tk.Entry(root, width=10)
                entry.grid(row=1, column=i)
                self.entries[label] = entry

        # self.duration_unit = tk.StringVar(value="s")
        # self.pulse_unit = tk.StringVar(value="ms")
        # tk.OptionMenu(root, self.duration_unit, "us", "ms", "s").grid(row=1, column=parameters.index(TOTAL_DURATION_LABEL)*2 + 1)
        # tk.OptionMenu(root, self.pulse_unit, "us", "ms", "s").grid(row=1, column=parameters.index(PULSE_DURATION_LABEL)*2 + 1)

        plus_button = tk.Button(root, text="+", command=self.add_line)
        plus_button.grid(row=1, column=len(parameters), padx=10)

        remove_button = tk.Button(root, text="-", command=self.remove_last_line)
        remove_button.grid(row=1, column=len(parameters) + 1, padx=10)

        self.output_title = tk.Label(root, text="Output").grid(
            row=2, column=0, columnspan=len(parameters)
        )
        self.output_text = tk.Text(root, height=10, width=50)
        self.output_text.grid(row=3, column=0, columnspan=len(parameters), pady=10)
        self.output_text.config(state=tk.DISABLED)

        self.input_title = tk.Label(root, text="Input").grid(
            row=4, column=0, columnspan=len(parameters)
        )
        self.input_text = tk.Text(root, height=10, width=50)
        self.input_text.grid(row=5, column=0, columnspan=len(parameters), pady=10)

        validate_button = tk.Button(root, text="Validate", command=self.validate_entry)
        validate_button.grid(row=5, column=len(parameters) + 1, padx=10)

        # Validation result output field
        self.validation_output = tk.Text(root, height=20, width=120)
        self.validation_output.grid(
            row=6, column=0, columnspan=len(parameters), pady=10
        )
        self.validation_output.config(state=tk.DISABLED)

        # Store lines
        self.csv_lines = []

    def convert_to_ms(self, value, unit):
        if unit == "us":
            return value / 1000.0
        elif unit == "ms":
            return value
        elif unit == "s":
            return value * 1000.0
        else:
            raise ValueError("Unknown time unit")

    def convert_to_us(self, value, unit):
        if unit == "us":
            return value
        elif unit == "ms":
            return value * 1000.0
        elif unit == "s":
            return value * 1_000_000.0
        else:
            raise ValueError("Unknown time unit")

    def convert_to_hz(self, value, unit):
        if unit == "mHz":
            return value / 1000.0
        elif unit == "Hz":
            return value
        else:
            raise ValueError("Unknown frequency unit")

    def get_line(self):
        """Read out the input fields and return a chrolispp-compatible csv line"""
        # Get and validate input values
        led_index = (
            int(self.entries[LED_INDEX_LABEL].get()) - 1
        )  # convert to 0-based index
        freq_raw = (
            None
            if self.entries[FREQUENCY_LABEL].get() == ""
            else float(self.entries[FREQUENCY_LABEL].get())
        )
        total_raw = float(self.entries[TOTAL_DURATION_LABEL].get())
        pulse_raw = float(self.entries[PULSE_DURATION_LABEL].get())
        power = int(self.entries[POWER_LABEL].get())
        total_duration_us = int(self.convert_to_us(total_raw, self.duration_unit.get()))
        pulse_duration_us = int(self.convert_to_us(pulse_raw, self.pulse_unit.get()))
        freq_hz = (
            None
            if freq_raw is None
            else self.convert_to_hz(freq_raw, self.freq_unit.get())
        )
        # calculate time between pulses and n_pulses
        if freq_hz is not None:
            cycle_duration_us = int(1_000_000.0 / freq_hz)
            time_between_pulses_us = int(cycle_duration_us - pulse_duration_us)
            # Round down to nearest multiple of 5 us
            time_between_pulses_us -= time_between_pulses_us % 5

            if time_between_pulses_us < 0:
                raise InvalidParameterError(
                    "Pulse duration is longer than cycle duration derived from frequency."
                )
            n_pulses = floor(total_duration_us / cycle_duration_us)
            if n_pulses <= 0:
                raise InvalidParameterError(
                    "Total duration is too short for the given frequency and pulse duration."
                )
        else:  # no frequency given, assume no repetition
            if power == 0:
                # for break, set time between pulses to total duration
                time_between_pulses_us = total_duration_us
                pulse_duration_us = 0
            else:
                time_between_pulses_us = total_duration_us - pulse_duration_us
                if time_between_pulses_us < 0:
                    raise InvalidParameterError(
                        "Pulse duration is longer than total duration."
                    )
            n_pulses = 1
        protocol_step = ProtocolStep(
            led_index=led_index,
            pulse_duration_us=pulse_duration_us,
            time_between_pulses_us=time_between_pulses_us,
            n_pulses=n_pulses,
            brightness_value=power,
        )
        return protocol_step.to_csv_line()

    def decode_line(self, line: str):
        """Take a csv line and decode it into a Chrolispp step"""
        protocol_step = ProtocolStep.from_csv_line(line)
        return str(protocol_step)

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
            messagebox.showerror(
                "Invalid input", "Please enter valid integers in all fields."
            )
        except InvalidParameterError as e:
            messagebox.showerror("Invalid parameter", str(e))

    def remove_last_line(self):
        if self.csv_lines:
            self.csv_lines.pop()
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "\n".join(self.csv_lines))
            self.output_text.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("No lines", "There are no lines to remove.")

    def validate_entry(self):
        user_input = self.input_text.get("1.0", tk.END).strip().split("\n")
        decoded_lines = []
        for i_line, line in enumerate(user_input):
            if len(line) == 0:
                continue
            decoded_line = self.decode_line(line)
            decoded_lines.append(f"Step {i_line+1}: {decoded_line}")
        self.validation_output.config(state=tk.NORMAL)
        self.validation_output.delete("1.0", tk.END)
        self.validation_output.insert(tk.END, "\n".join(decoded_lines))
        self.validation_output.config(state=tk.DISABLED)


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVApp(root)
    root.mainloop()
