# Simple script to fix the indentation error in client_routes.py
with open('client_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the specific indentation error
lines[1817] = '        print(f"❌ Error in extract_gst_data: {str(e)}")\n'
lines[1818] = '        return jsonify({"error": str(e)}), 500\n'
lines[1819] = '\n'
lines[1820] = '    except Exception as e:\n'  # This should be at 4 spaces indentation
lines[1821] = '        print(f"❌ Download error: {str(e)}")\n'

# Write the fixed content back
with open('client_routes_fixed.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed the indentation error in client_routes.py")