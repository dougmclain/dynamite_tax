import os
import sys
import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Initialize Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HOA_tax.settings')
django.setup()

# Create test content
test_content = b"This is a test file from Render to Azure Storage."
test_filename = "test_upload.txt"

# Try different paths
paths_to_try = [
    test_filename,                      # Root of container
    f"test/{test_filename}",            # In test folder
    f"completed_tax_returns/{test_filename}", # In completed_tax_returns folder
    f"extensions/{test_filename}"       # In extensions folder
]

# Attempt to save files to different paths
for path in paths_to_try:
    try:
        # Save the file
        saved_path = default_storage.save(path, ContentFile(test_content))
        print(f"Successfully saved file to: {saved_path}")
        
        # Check if file exists
        exists = default_storage.exists(saved_path)
        print(f"File exists check: {exists}")
        
        # Try to get URL
        url = default_storage.url(saved_path)
        print(f"File URL: {url}")
        
        # Try to read file content back
        content = default_storage.open(saved_path).read()
        print(f"Retrieved content: {content}")
        
        print(f"Test successful for path: {path}")
        print("-" * 50)
    except Exception as e:
        print(f"Error with path {path}: {str(e)}")
        print("-" * 50)

print("Test completed.")