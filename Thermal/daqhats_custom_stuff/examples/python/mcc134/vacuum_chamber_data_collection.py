from __future__ import print_function
from time import sleep
from sys import stdout
from daqhats import mcc134, HatIDs, HatError, TcTypes
from daqhats_utils import select_hat_device, tc_type_to_string
import csv
import datetime
import os
import subprocess
import sys
import select
import termios
import tty

# Constants
EXPORT_FOLDER = "data_exports"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CSV_FILENAME = os.path.join(EXPORT_FOLDER, f"temperature_data_{timestamp}.csv")

def is_key_pressed():
    """Returns the pressed key if available, else None (non-blocking)."""
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

def initialize_csv():
    """Creates a new CSV file for this run and writes the header."""
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    with open(CSV_FILENAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Trial", "Channel", "Temperature (C)"])

def append_trial_data(trial_number, data):
    """Appends trial data to the CSV file."""
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for channel, value in data:
            writer.writerow([timestamp, trial_number, channel, value])
    print(f"\nData appended to {CSV_FILENAME}")

def main():
    """
    This function is executed automatically when the module is run directly.
    """
    tc_type = TcTypes.TYPE_K   # change this to the desired thermocouple type
    delay_between_reads = 1  # Seconds
    channels = (0, 1, 2, 3)

    initialize_csv()
    
    #Keyboard  input handling
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    
    try:
        # Get an instance of the selected hat device object.
        address = select_hat_device(HatIDs.MCC_134)
        hat = mcc134(address)

        for channel in channels:
            hat.tc_type_write(channel, tc_type)

        print('\nMCC 134 single data value read example')
        print('    Function demonstrated: mcc134.t_in_read')
        print('    Channels: ' + ', '.join(str(channel) for channel in channels))
        print('    Thermocouple type: ' + tc_type_to_string(tc_type))
        try:
            input("\nPress 'Enter' to continue")
        except (NameError, SyntaxError):
            pass

        print('\nAcquiring data ... Power ON to the SMA')
        gpio_state = True
        # subprocess.run(["gpioset", "gpiochip0", "16=1"])
        print('\nPress "O" to toggle power. Press Ctrl-C to abort')

        # Display the header row for the data table.
        print('\n  Sample', end='')
        for channel in channels:
            print('     Channel', channel, end='')
        print('')

        try:
            samples_per_channel = 0
            while True:
                # Display the updated samples per channel count
                samples_per_channel += 1
                print('\r{:8d}'.format(samples_per_channel), end='')

                # Read a single value from each selected channel.
                trial_data = []
                for channel in channels:
                    value = hat.t_in_read(channel)
                    if value == mcc134.OPEN_TC_VALUE:
                        print('     Open     ', end='')
                        trial_data.append((channel, "Open"))
                    elif value == mcc134.OVERRANGE_TC_VALUE:
                        print('     OverRange', end='')
                        trial_data.append((channel, "OverRange"))
                    elif value == mcc134.COMMON_MODE_TC_VALUE:
                        print('   Common Mode', end='')
                        trial_data.append((channel, "Common Mode"))
                    else:
                        print('{:12.2f} C'.format(value), end='')
                        trial_data.append((channel, value))

                stdout.flush()
                append_trial_data(samples_per_channel, trial_data)

                # Check for 'O' key press to toggle GPIO
                key = is_key_pressed()
                if key and key.lower() == 'o':
                    gpio_state = not gpio_state
                    subprocess.run(["gpioset", "gpiochip0", f"16={int(gpio_state)}"])
                    print(f"\nGPIO 16 toggled to {'HIGH' if gpio_state else 'LOW'}")

                # Wait the specified interval between reads.
                sleep(delay_between_reads)

        except KeyboardInterrupt:
            print('\nData collection stopped by user.')
            subprocess.run(["gpioset", "gpiochip0", "16=0"])

    except (HatError, ValueError) as error:
        print('\n', error)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == '__main__':
    main()
