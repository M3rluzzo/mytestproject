import os
import sys

def merge_files_by_extension(extensions, start_dirs, specific_files=[]):
    temp_output = []
    for start_dir in start_dirs:
        for root, _, filenames in os.walk(start_dir):
            for filename in filenames:
                if any(filename.endswith(f".{ext}") for ext in extensions):
                    filepath = os.path.join(root, filename)
                    write_file_content(filepath, filename, temp_output)

    for filepath in specific_files:
        filename = os.path.basename(filepath)
        write_file_content(filepath, filename, temp_output)

    with open("output.txt", "w") as output_file:
        output_file.writelines([line for line in temp_output if line.strip()])

def write_file_content(filepath, filename, temp_output):
    with open(filepath, "r") as input_file:
        lines = input_file.readlines()
        if lines:
            temp_output.append(f"--- {filename} ---\n")
            temp_output.extend(lines)
            temp_output.append("\n")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        extensions = sys.argv[1].split(',')
        start_dirs = [arg for arg in sys.argv[2:] if os.path.isdir(arg)]
        specific_files = [arg for arg in sys.argv[2:] if os.path.isfile(arg)]
        merge_files_by_extension(extensions, start_dirs, specific_files)
    else:
        print("Estensioni o cartelle di partenza non fornite.")
