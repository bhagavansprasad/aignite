#!/bin/bash
set -e

# Define the input file containing filenames
FILE_LIST="tests/utils/context-files.txt"
OUTPUT_FILE="context.txt"

# Clear the output file before appending
> "$OUTPUT_FILE"

# Read each filename from the file and append its content
make clean
echo "Here is the context of the source tree and the files:" >> "$OUTPUT_FILE"
echo "Store the context.  Based the context I will be asking questions Later" >> "$OUTPUT_FILE"
echo "# Source Tree" >> "$OUTPUT_FILE"
tree >> "$OUTPUT_FILE"
while IFS= read -r file; do
    echo "" >> "$OUTPUT_FILE"
    echo "# $file" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
done < "$FILE_LIST"

echo "Context file generated: $OUTPUT_FILE"

