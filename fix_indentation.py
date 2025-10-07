# Script to fix indentation error in client_routes.py
with open('client_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation error at line 1819 (0-indexed as 1818)
# The issue is that lines 1819-1820 are indented with 12 spaces instead of 8
if len(lines) > 1820:
    # Fix the error handling lines
    lines[1817] = '        print(f"❌ Error in extract_gst_data: {str(e)}")\n'
    lines[1818] = '        return jsonify({"error": str(e)}), 500\n'
    lines[1819] = '\n'
    lines[1820] = '\n'
    # Add the missing function definition
    lines[1821] = '@client_bp.route(\'/clients/<client_id>/download/<document_type>\')\n'
    lines[1822] = '@jwt_required()\n'
    lines[1823] = 'def download_document(client_id, document_type):\n'
    lines[1824] = '    try:\n'
    lines[1825] = '        from flask import redirect, Response\n'
    lines[1826] = '        import requests\n'
    lines[1827] = '        from io import BytesIO\n'
    lines[1828] = '        \n'
    lines[1829] = '        print(f"🔍 Download request: client_id={client_id}, document_type={document_type}")\n'

# Write the fixed content back
with open('client_routes_fixed.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed indentation error in client_routes.py")