from readGpsLogs import monitor_folder

folder_to_watch = '/root/Results'
folder_monitor = monitor_folder(folder_to_watch)

# Continuously get the latest line from the generator
for last_line in folder_monitor:
    # Split the last line into individual components
    components = last_line.split(',')
    
    # Extract the first and second numbers
    first_number = float(components[0])
    second_number = float(components[2])

    # Calculate the sum
    sum_of_numbers = first_number + second_number

    # Print or use the result as needed
    print(f"Sum of the first and second numbers: {first_number}")
