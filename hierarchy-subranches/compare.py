def find_unique_lines(file1_path, file2_path, output_file_path):
    """
    This function finds unique lines that are present in only one of the two given files.
    Used for debugging the output of hierarchy.py
    Args:
        file1_path (str): Path to the first input file.
        file2_path (str): Path to the second input file.
        output_file_path (str): Path to the output file where unique lines will be saved.
    Returns:
        str: A message indicating completion and the name of the output file.
    """
    # Read lines from the first file and remove newline characters
    with open(file1_path, 'r') as file:
        lines_file1 = set(file.read().splitlines())
    
    # Read lines from the second file and remove newline characters
    with open(file2_path, 'r') as file:
        lines_file2 = set(file.read().splitlines())
    
    # Find lines that are unique to each file (symmetric difference)
    unique_lines = lines_file1.symmetric_difference(lines_file2)
    
    # Write unique lines to the output file
    with open(output_file_path, 'w') as file:
        for line in unique_lines:
            file.write(f"{line}\n")
    
    return f"Unique lines written to {output_file_path}"
