# Script to fix all indentation errors in client_routes.py
with open('client_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation error at line 1829 (0-indexed as 1828)
# The issue is that the block starting with "# Validate Cloudinary URL" is indented with 16 spaces instead of 8
# We need to fix all lines from 1829 to around 1950 that are over-indented by 8 spaces

start_fix_line = 1828  # Line with "# Validate Cloudinary URL"
end_fix_line = 1950    # Approximate end of the problematic block

for i in range(start_fix_line, min(end_fix_line, len(lines))):
    if lines[i].startswith('                '):  # 16 spaces
        lines[i] = lines[i][8:]  # Remove 8 spaces

# Write the fixed content back
with open('client_routes_fixed2.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed all indentation errors in client_routes.py")