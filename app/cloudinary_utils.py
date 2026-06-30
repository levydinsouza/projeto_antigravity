"""Cloudinary integration utilities for image upload and management."""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api


def init_cloudinary(app=None):
    """Initialize Cloudinary with credentials from environment variables.
    
    Supports:
        - CLOUDINARY_URL (Connection string format, default on Railway integration)
        - Individual credentials (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
    """
    cloudinary_url = os.environ.get('CLOUDINARY_URL')
    if cloudinary_url:
        # Explicitly configure using the provided URL to avoid detection failure on some platforms
        cloudinary.config(
            cloudinary_url=cloudinary_url,
            secure=True
        )
        print("[GDev] Cloudinary initialized successfully using CLOUDINARY_URL.")
    else:
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        
        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            print("[GDev] Cloudinary initialized successfully using individual credentials.")
        else:
            print("[GDev] Warning: Cloudinary environment variables (CLOUDINARY_URL or individual keys) not set.")


def upload_image(file_storage, folder='gdev-tutorial', public_id=None, is_profile=False):
    """Upload an image to Cloudinary.

    Args:
        file_storage: A Werkzeug FileStorage object from a form upload.
        folder: The Cloudinary folder to upload to.
        public_id: Optional custom public_id for the image.
        is_profile: If True, uses a square crop centered on the face.

    Returns:
        dict with 'url' and 'public_id' on success, or None on failure.
    """
    try:
        if is_profile:
            # Profile pictures are square with face centering
            transformation = [
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
                {'quality': 'auto', 'fetch_format': 'auto'}
            ]
        else:
            # Module thumbnails are 16:9 landscape
            transformation = [
                {'width': 800, 'height': 450, 'crop': 'fill', 'gravity': 'auto'},
                {'quality': 'auto', 'fetch_format': 'auto'}
            ]

        options = {
            'folder': folder,
            'overwrite': True,
            'resource_type': 'image',
            'transformation': transformation
        }
        if public_id:
            options['public_id'] = public_id

        result = cloudinary.uploader.upload(file_storage, **options)
        return {
            'url': result.get('secure_url', result.get('url')),
            'public_id': result.get('public_id')
        }
    except Exception as e:
        print(f'[GDev] Cloudinary upload error: {e}')
        return None


def delete_image(public_id):
    """Delete an image from Cloudinary by its public_id.

    Args:
        public_id: The Cloudinary public_id of the image to delete.

    Returns:
        True on success, False on failure.
    """
    if not public_id:
        return False
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f'[GDev] Cloudinary delete error: {e}')
        return False


def upload_raw_file(file_storage, folder='gdev-tutorial/materials', public_id=None):
    """Upload a raw file (PDF, HTML) to Cloudinary.

    Args:
        file_storage: A Werkzeug FileStorage object.
        folder: Cloudinary folder.
        public_id: Optional custom public_id.

    Returns:
        dict with 'url' and 'public_id' on success, or None on failure.
    """
    try:
        options = {
            'folder': folder,
            'overwrite': True,
            'resource_type': 'raw'
        }
        if public_id:
            options['public_id'] = public_id

        result = cloudinary.uploader.upload(file_storage, **options)
        return {
            'url': result.get('secure_url', result.get('url')),
            'public_id': result.get('public_id')
        }
    except Exception as e:
        print(f'[GDev] Cloudinary raw upload error: {e}')
        return None


def delete_raw_file(public_id):
    """Delete a raw file from Cloudinary by its public_id.

    Args:
        public_id: The Cloudinary public_id of the raw file to delete.

    Returns:
        True on success, False on failure.
    """
    if not public_id:
        return False
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type='raw')
        return result.get('result') == 'ok'
    except Exception as e:
        print(f'[GDev] Cloudinary raw delete error: {e}')
        return False


def upload_pdf_file(file_storage, folder='gdev-tutorial/lessons', public_id=None):
    """Upload a PDF file to Cloudinary as an image resource.

    This allows generating thumbnails from page 1.

    Args:
        file_storage: A Werkzeug FileStorage object.
        folder: Cloudinary folder.
        public_id: Optional custom public_id.

    Returns:
        dict with 'url' and 'public_id' on success, or None on failure.
    """
    try:
        options = {
            'folder': folder,
            'overwrite': True,
            'resource_type': 'image'
        }
        if public_id:
            options['public_id'] = public_id

        result = cloudinary.uploader.upload(file_storage, **options)
        return {
            'url': result.get('secure_url', result.get('url')),
            'public_id': result.get('public_id')
        }
    except Exception as e:
        print(f'[GDev] Cloudinary PDF upload error: {e}')
        return None
