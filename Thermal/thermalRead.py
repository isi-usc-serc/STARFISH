49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
def main():
    """Main function to read temperature data and store it in a CSV file."""
    tc_type = TcTypes.TYPE_K  # Change to desired thermocouple type
    delay_between_reads = 1   # Seconds
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

        print('\nAcquiring data ... Press Ctrl-C to stop')

        # Generate a unique CSV file name for this run
        csv_filename = generate_filename()

        # Display the header row for the console output
        print('\n  Sample', end='')
        for channel in channels:
            print('     Channel', channel, end='')
        print('')
        
        samples_per_channel = 0

        try:
            while True:
                samples_per_channel += 1
                print('\r{:8d}'.format(samples_per_channel), end='')

                # Read a single value from each selected channel
                data = {}
                for channel in channels:
                    value = hat.t_in_read(channel)
                    if value == mcc134.OPEN_TC_VALUE:
                        print('     Open     ', end='')
                        data[channel] = "Open"
                    elif value == mcc134.OVERRANGE_TC_VALUE:
                        print('     OverRange', end='')
                        data[channel] = "OverRange"
                    elif value == mcc134.COMMON_MODE_TC_VALUE:
                        print('   Common Mode', end='')
                        data[channel] = "Common Mode"
                    else:
                        print('{:12.2f} C'.format(value), end='')
                        data[channel] = round(value, 2)

                stdout.flush()

                # Save data to CSV
                save_data_to_csv(csv_filename, samples_per_channel, data)

                # Wait the specified interval between reads
                sleep(delay_between_reads)

        except KeyboardInterrupt:
            # Clear the '^C' from the display.
            print(CURSOR_BACK_2, ERASE_TO_END_OF_LINE, '\n')

    except (HatError, ValueError) as error:
        print('\n', error)

if __name__ == '__main__':
    main()