clear;
close all;
clc;

% Read CSV files data 
datafolder = pwd;
data = fullfile(datafolder, 'data_exports');
read_csv = dir(fullfile(data, '*.csv'));

% Arrays for time, timperature, and channel
all_times = [];
all_temps = [];
all_channels = [];

% Process CSV file data
for i = 1:length(read_csv)
    % Read table from CSV file
    file = fullfile(data, read_csv(i).name);
    table = readtable(file);

    % Convert timestamp to read datetime
    timestamps = datetime(table.Timestamp, 'InputFormat', 'M/d/yyyy HH:mm');

    % Convert timestamp to seconds 
    if i == 1
        start_time = min(timestamps);
    end
    time = seconds(timestamps - start_time);

    all_times = [all_times; time];
    all_temps = [all_temps; table.Temperature_C_];
    all_channels = [all_channels; table.Channel];
end

channel_numbers = unique(all_channels);

% Plot Temperature vs Time of all channels
figure;
hold on;
colors = lines(length(channel_numbers));

for i = 1:length(channel_numbers)
    specifchann = channel_numbers(i);
    % Select data for this specific channel
    specifdata = all_channels == specifchann;

    % Extract and sort data for this channel
    ch_times = all_times(specifdata);
    ch_temps = all_temps(specifdata);
    [ch_times, sort_data] = sort(ch_times);
    ch_temps = ch_temps(sort_data);

    % Plot of data for each channel (temp vs time)
    plot(ch_times, ch_temps, '-', 'Color', colors(i,:), 'LineWidth', 1.5, ...
         'DisplayName', ['Channel ' num2str(specifchann)]);
end

xlabel('Time (seconds)');
ylabel('Temperature (°C)');
title('Temperature vs Time of Thermocouple Data');
legend show;
grid on;
hold off;