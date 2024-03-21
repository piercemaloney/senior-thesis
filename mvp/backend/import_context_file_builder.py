"""
Author: Pierce Maloney
Feb 2024
"""

from pathlib import Path

import sys

def remove_comments_from_text(coq_file_path):
    with open(coq_file_path, 'r') as file:
        lines = file.readlines()

    cleaned_text = []
    in_comment = False
    for line in lines:
        original_line = line  # Keep the original line for appending later if needed
        if in_comment:
            if '*)' in line:
                in_comment = False
                line = line.split('*)', 1)[1]  # Keep the text after the closing comment
        else:
            if '(*' in line:
                in_comment = True
                line, _, following = line.partition('(*')
                # Check if the comment ends on the same line
                if '*)' in following:
                    in_comment = False
                    line += following.split('*)', 1)[1]
        
        # Append non-comment or outside-comment text, unless it's empty
        if not in_comment and line.strip():
            cleaned_text.append(line)

    return cleaned_text

def remove_proofs_from_text(lines):
    cleaned_lines = []
    in_proof = False
    capture_statement = False
    proof_start_keywords = ['Theorem', 'Lemma', 'Corollary', 'Proposition']
    proof_end_keywords = ['Qed.', 'Defined.', 'Admitted.']

    for line in lines:
        if any(keyword in line for keyword in proof_start_keywords):
            in_proof = True
            cleaned_lines.append(line)
            if '.' not in line: 
                capture_statement = True # Start capturing the multi-line statement
            continue

        if capture_statement:
            cleaned_lines.append(line)  # Continue adding lines as part of the statement
            if '.' in line:  # Check if the line contains a period, indicating the end of the statement
                capture_statement = False  # Stop capturing the statement
            continue  # Skip the rest of the loop to avoid adding lines twice

        if in_proof and any(keyword in line for keyword in proof_end_keywords):
            in_proof = False  # End of proof found, stop skipping lines
            continue

        if not in_proof and not capture_statement:
            cleaned_lines.append(line)  # Add lines outside of proofs

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

    cleaned_text = remove_comments_from_text(coq_file_path)
    cleaned_text = remove_proofs_from_text(cleaned_text)
    write_to_txt_file(cleaned_text, destination_dir)

if __name__ == "__main__":
    main()