"""
Author: Pierce Maloney
Feb 2024
"""

from pathlib import Path

import sys


def remove_comments_from_file(coq_file_path: str) -> list:
    with open(coq_file_path, 'r') as file:
        lines = file.readlines()

    cleaned_lines = []
    num_left = 0
    in_string = False
    current_line = []

    for line in lines:
        i = 0
        while i < len(line):
            if line[i] == '"':
                in_string = not in_string
            if not in_string and line[i:i+2] == "(*":
                num_left += 1
                i += 2
                continue  # Skip the rest of the loop and proceed with the next iteration
            elif not in_string and num_left > 0 and line[i:i+2] == "*)":
                num_left -= 1
                i += 2
                continue  # Skip the rest of the loop and proceed with the next iteration
            if num_left == 0:
                current_line.append(line[i])
            i += 1

        # At the end of processing each line, join the characters to form the cleaned line
        # and reset current_line for the next iteration
        if current_line and len(current_line) > 0:  # Only add non-empty lines
            cleaned_lines.append("".join(current_line))
            current_line = []  # Reset for the next line

    return cleaned_lines


def remove_proofs_from_text(lines):
    reversed_lines = lines[::-1]  # Reverse the list of lines to work from bottom to top

    proof_start_keywords = ['Theorem', 'Lemma', 'Corollary', 'Proposition', 'Fact', 'Global Instance', 'Definition', 'Remark', 'Let', "Goal", "Fixpoint"]
    proof_end_keywords = ['Qed.', 'Defined.', 'Admitted.']

    cleaned_lines_reversed = []  # This will store the cleaned lines in reverse order
    skip = False  # Flag to indicate whether we're skipping lines (inside a proof)

    for i, line in enumerate(reversed_lines):

        if not skip:
            if any(keyword in line for keyword in proof_end_keywords):
                skip = True  # Start skipping lines once we hit a proof end keyword  # Skip the proof end line itself
            else:
                cleaned_lines_reversed.append(line)
            continue

        # Check if the line contains any of the proof start keywords
        if any(keyword in line for keyword in proof_start_keywords):
            skip = False  # Stop skipping once we hit a proof start keyword
        else:
            continue  # Keep skipping lines until we find a proof start keyword

 
        # Handle possible multi-line statements by looking for the period
        statement_lines = []
        while i > 0 and '.' not in reversed_lines[i]:
            statement_lines.append(reversed_lines[i])
            i -= 1
        statement_lines.append(reversed_lines[i])
        
        cleaned_lines_reversed.extend(statement_lines[::-1])  # Add the statement in the correct (reversed) order

    # Since we've been working in reverse, reverse the cleaned lines to restore original order
    return cleaned_lines_reversed[::-1]

def remove_back_to_back_empty_lines(lines):
    cleaned_lines = []
    last_line_empty = False  # Flag to track if the last line was empty

    for line in lines:
        # Check if the current line is empty
        if not line.strip():
            if last_line_empty:  # If the last line was also empty, skip adding this line
                continue
            last_line_empty = True  # Mark this line as empty for the next iteration
        else:
            last_line_empty = False  # Current line is not empty, reset the flag

        cleaned_lines.append(line)

    return cleaned_lines

def write_to_txt_file(cleaned_text, output_path):
    with open(output_path, 'w') as file:
        file.writelines(cleaned_text)

def main():
    if len(sys.argv) != 3:
        print("Usage: context_file_builder.py <coq_file_path> <destination_dir>")
        sys.exit(1)

    coq_file_path = sys.argv[1]
    destination_dir = sys.argv[2]

    cleaned_text = remove_comments_from_file(coq_file_path)
    cleaned_text = remove_proofs_from_text(cleaned_text)
    cleaned_text = remove_back_to_back_empty_lines(cleaned_text)
    write_to_txt_file(cleaned_text, destination_dir)

if __name__ == "__main__":
    main()