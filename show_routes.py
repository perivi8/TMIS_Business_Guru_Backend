from app import app

# Print all registered routes
print("Registered routes:")
for rule in app.url_map.iter_rules():
    methods = rule.methods or []
    print(f"  {rule.rule} -> {rule.endpoint} ({', '.join(sorted(methods))})")