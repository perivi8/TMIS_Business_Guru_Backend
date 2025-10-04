import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Connect to MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.tmis_business_guru
users_collection = db.users

print("=== Checking Users in Database ===")

# Get all users
users = list(users_collection.find({}, {'password': 0}))  # Exclude password
print(f"Total users found: {len(users)}")

for i, user in enumerate(users, 1):
    print(f"\n{i}. User:")
    print(f"   Email: {user.get('email', 'No email')}")
    print(f"   Username: {user.get('username', 'No username')}")
    print(f"   Status: {user.get('status', 'No status field')}")
    print(f"   Role: {user.get('role', 'No role')}")
    print(f"   Created: {user.get('created_at', 'No created_at')}")

# Check specifically for the test email
test_email = "perivihk@gmail.com"
print(f"\n=== Checking for specific email: {test_email} ===")
specific_user = users_collection.find_one({'email': test_email})
if specific_user:
    print("✅ User found!")
    print(f"   Username: {specific_user.get('username')}")
    print(f"   Status: {specific_user.get('status', 'No status field')}")
    print(f"   Role: {specific_user.get('role')}")
else:
    print("❌ User not found")

client.close()
