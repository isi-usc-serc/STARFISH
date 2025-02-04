#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
    MCC 134 Functions Demonstrated:
        mcc134.t_in_read

    Purpose:
        Read a single data value for each channel in a loop and save each trial to a unique file.

    Description:
        This example demonstrates acquiring data using a software timed loop
        to read a single value from each selected channel on each iteration
        of the loop and saving each trial to a uniquely named CSV file.
"""

from __future__ import print_function
from time import sleep
from sys import stdout
from daqhats import mcc134, HatIDs, HatError, TcTypes
from daqhats_utils import select_hat_device, tc_type_to_string
import csv
import datetime
import os

# Constants
CURSOR_BACK_2 = '\x1b[2D'
ERASE_TO_END_OF_LINE = '\x1b[0K'
EXPORT_FOLDER = "data_exports"

def generate_unique_filename():
    """Generates a unique filename with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    return os.path.join(EXPORT_FOLDER, f"trial_{timestamp}.csv")

def save_trial_data(trial_number, data):
    """Saves trial data to a uniquely named CSV file."""
    filename = generate_unique_filename()
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Trial", "Channel", "Temperature (C)"])
        for channel, value in data:
            writer.writerow([trial_number, channel, value])
    print(f"\nData saved to {filename}")

def main():
    """
    This function is executed automatically when the module is run directly.
    """
    tc_type = TcTypes.TYPE_K   # change this to the desired thermocouple type
    delay_between_reads = 1  # Seconds
    channels = (0, 1, 2, 3)

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

        print('\nAcquiring data ... Press Ctrl-C to abort')

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
                save_trial_data(samples_per_channel, trial_data)

                # Wait the specified interval between reads.
                sleep(delay_between_reads)

        except KeyboardInterrupt:
            # Clear the '^C' from the display.
            print(CURSOR_BACK_2, ERASE_TO_END_OF_LINE, '\n')

    except (HatError, ValueError) as error:
        print('\n', error)

if __name__ == '__main__':
    # This will only be run when the module is called directly.
    main()
