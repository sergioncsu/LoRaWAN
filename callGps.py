from readGpsLogs import monitor_folder
import time

folder_to_watch = '/root/Results'
folder_monitor = monitor_folder(folder_to_watch)


while True:
    time.sleep(0.1)
    last_line = next(folder_monitor, None)
    if last_line is not None:
        components = last_line.split(',')
        first_number = float(components[0])
        lat_int = int(abs(float(components[1]) * 1e8))
        lon_int = int(abs(float(components[2]) * 1e6))
        merged_coordinates = str(lat_int) + str(lon_int)
        print(merged_coordinates)
