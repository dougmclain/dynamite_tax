import os
import sys
import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from azure.storage.blob import BlobServiceClient

# Initialize Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HOA_tax.settings')
django.setup()

# Check if container exists and create if it doesn't
try:
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    container_name = settings.AZURE_CONTAINER
    container_exists = False
    
    # List existing containers and check if ours exists
    containers = blob_service_client.list_containers()
    for container in containers:
        if container.name == container_name:
            container_exists = True
            print(f"Container '{container_name}' already exists")
            break
    
    # Create container if it doesn't exist
    if not container_exists:
        print(f"Container '{container_name}' does not exist. Creating...")
        blob_service_client.create_container(container_name)
        print(f"Container '{container_name}' created successfully")
    
    # Now try to upload a test file
    test_content = b"This is a test file from Render to Azure Storage."
    test_filename = "test_upload.txt"
    
    # Save directly using Azure SDK
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=test_filename)
    blob_client.upload_blob(test_content, overwrite=True)
    print(f"Uploaded test file directly using Azure SDK: {test_filename}")
    
    # Now try with Django's default_storage
    saved_path = default_storage.save(test_filename, ContentFile(test_content))
    print(f"Saved file via Django's default_storage: {saved_path}")
    
    exists = default_storage.exists(saved_path)
    print(f"File exists check: {exists}")
    
    url = default_storage.url(saved_path)
    print(f"File URL: {url}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("Test completed.")