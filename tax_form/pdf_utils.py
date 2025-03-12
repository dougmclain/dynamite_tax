import os
import logging
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from io import BytesIO

logger = logging.getLogger(__name__)

def save_pdf_to_azure(file_content, file_path):
    """
    Save PDF content to Azure Storage
    
    Args:
        file_content: The PDF content as bytes
        file_path: The destination path in Azure Storage
        
    Returns:
        The URL of the saved file
    """
    try:
        # Save the file using Django's default_storage (which is Azure in production)
        path = default_storage.save(file_path, ContentFile(file_content))
        url = default_storage.url(path)
        logger.info(f"PDF saved to Azure at {path}")
        return url
    except Exception as e:
        logger.error(f"Error saving PDF to Azure: {str(e)}", exc_info=True)
        raise

def delete_file_from_azure(file_path):
    """
    Delete a file from Azure Storage
    
    Args:
        file_path: The path of the file to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info(f"File {file_path} deleted from Azure Storage")
            return True
        else:
            logger.warning(f"File {file_path} not found in Azure Storage")
            return False
    except Exception as e:
        logger.error(f"Error deleting file from Azure: {str(e)}", exc_info=True)
        return False

def read_pdf_from_azure(file_path):
    """
    Read a PDF file from Azure Storage
    
    Args:
        file_path: The path of the file in Azure Storage
        
    Returns:
        The file content as bytes
    """
    try:
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as f:
                content = f.read()
            logger.info(f"File {file_path} read from Azure Storage")
            return content
        else:
            logger.error(f"File {file_path} not found in Azure Storage")
            raise FileNotFoundError(f"File {file_path} not found in Azure Storage")
    except Exception as e:
        logger.error(f"Error reading file from Azure: {str(e)}", exc_info=True)
        raise

def check_file_exists(file_path):
    """
    Check if a file exists in storage
    
    Args:
        file_path: The path of the file to check
        
    Returns:
        True if the file exists, False otherwise
    """
    try:
        return default_storage.exists(file_path)
    except Exception as e:
        logger.error(f"Error checking if file exists in storage: {str(e)}", exc_info=True)
        return False

def ensure_storage_structure():
    """
    Ensure the storage structure exists
    
    This is a no-op for blob storage, but is included for consistency
    """
    if settings.USE_AZURE_STORAGE:
        logger.info("Using Azure Storage - no need to create directories")
        return True
    
    # For local storage, create the directories
    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'completed_tax_returns'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'extensions'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'engagement_letters'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'signed_engagement_letters'), exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating storage directories: {str(e)}", exc_info=True)
        return False

def get_file_url(file_path):
    """
    Get the URL for a file in storage
    
    Args:
        file_path: The path of the file
        
    Returns:
        The URL of the file
    """
    try:
        return default_storage.url(file_path)
    except Exception as e:
        logger.error(f"Error getting URL for file {file_path}: {str(e)}", exc_info=True)
        return None