
def read_config_file(filename):
    # Create an empty dictionary to store the variables
    config_vars = {}

    # Open the file and read each line
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Process each line
    for line in lines:
        # Ignore comments and empty lines
        if line.startswith('#') or line.strip() == '':
            continue

        # Split the line into variable and value
        var, val = line.split('=')

        # Store the variable and value in the dictionary
        val = val.strip()
        if val.isdigit():
            config_vars[var.strip()] = int(val)
        else:
            config_vars[var.strip()] = val

    return config_vars
