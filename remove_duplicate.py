# Script to remove duplicate extract_gst_data_direct function
with open('client_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start and end of the duplicate function
start_line1 = None
start_line2 = None
end_line = None

for i, line in enumerate(lines):
    if '@client_bp.route(\'/clients/extract-gst-data\', methods=[\'POST\'])' in line:
        if start_line1 is None:
            start_line1 = i
        elif start_line2 is None:
            start_line2 = i
            break

# If we found both occurrences, remove the second one
if start_line1 is not None and start_line2 is not None:
    # Find the end of the second function (look for the next @client_bp.route or end of file)
    end_line = start_line2
    for i in range(start_line2 + 1, len(lines)):
        if '@client_bp.route(' in lines[i] or i == len(lines) - 1:
            end_line = i
            break
    
    # Remove the duplicate function (from start_line2 to end_line)
    del lines[start_line2:end_line]
    
    # Write the fixed content back
    with open('client_routes_fixed.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Removed duplicate extract_gst_data_direct function")
else:
    print("Could not find duplicate functions")