# azure_container_check.py
import os
import sys
import django
from django.conf import settings
from azure.storage.blob import BlobServiceClient, BlobClient, PublicAccess

# Initialize Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HOA_tax.settings')
django.setup()

def check_and_fix_container():
    """Check container public access settings and fix if needed."""
    try:
        # Create a connection to the storage account
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        container_name = settings.AZURE_CONTAINER
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check container properties including public access level
        properties = container_client.get_container_properties()
        print(f"Container Name: {container_name}")
        print(f"Public Access Type: {properties.public_access}")
        
        # If container doesn't have public access, set it
        if properties.public_access != PublicAccess.Blob:
            print("Setting container public access to 'Blob'...")
            container_client.set_container_access_policy(signed_identifiers={}, public_access=PublicAccess.Blob)
            print("Container public access updated successfully")
        else:
            print("Container already has correct public access settings")
        
        # Upload a test blob with public cache settings
        test_content = b"This is a test file with public access settings."
        blob_name = "public_access_test.txt"
        
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(test_content, overwrite=True, content_settings={"cache_control": "public, max-age=86400", "content_type": "text/plain"})
        
        print(f"Test blob uploaded to: {blob_client.url}")
        print("Try accessing this URL in your browser to verify public access")
        
        # List a few blobs from the container
        print("\nListing some blobs in the container:")
        blobs = list(container_client.list_blobs(max_results=5))
        for blob in blobs:
            print(f" - {blob.name} (Last Modified: {blob.last_modified})")
            
            # Generate a URL for each blob
            blob_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob.name}"
            print(f"   URL: {blob_url}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_fix_container()