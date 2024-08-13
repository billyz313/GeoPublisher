import os
import re


def rename_file(filepath, input_pattern, output_pattern):
    """
    Renames a single file based on the input and output patterns.

    Args:
    filepath (str): The full path to the file to rename.
    input_pattern (str): A regex pattern with named groups (year, month, day) for the input filename.
    output_pattern (str): The output filename pattern using {year}, {month}, {day} placeholders.

    Returns:
    str: The new filename, or None if the pattern didn't match.
    """
    filename = os.path.basename(filepath)
    match = re.match(input_pattern, filename)

    if match:
        date_components = match.groupdict()

        # Fill in missing components with defaults (e.g., '01' for month/day if not provided)
        date_components.setdefault('month', '01')
        date_components.setdefault('day', '01')

        # Generate the new filename
        new_filename = output_pattern.format(**date_components)

        # Full path to the new file
        new_filepath = os.path.join(os.path.dirname(filepath), new_filename)

        # Rename the file
        os.rename(filepath, new_filepath)
        print(f"Renamed: {filename} -> {new_filename}")

        return new_filename

    print(f"No match found for: {filename}")
    return None


def rename_files(directory, input_pattern, output_pattern):
    """
    Renames all files in a directory based on the input and output patterns.

    Args:
    directory (str): The directory containing the files to rename.
    input_pattern (str): A regex pattern with named groups (year, month, day) for the input filenames.
    output_pattern (str): The output filename pattern using {year}, {month}, {day} placeholders.
    """
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            rename_file(filepath, input_pattern, output_pattern)

    print("Renaming complete.")