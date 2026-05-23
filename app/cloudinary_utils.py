"""Cloudinary integration utilities for image upload and management."""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api


def init_cloudinary(app=None):
    """Initialize Cloudinary with credentials from environment variables.
    
    Expected env vars (set in Railway):
        CLOUDINARY_CLOUD_NAME
        CLOUDINARY_API_KEY
        CLOUDINARY_API_SECRET
    """
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
        api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET', ''),
        secure=True
    )


def upload_image(file_storage, folder='gdev-tutorial', public_id=None):
    """Upload an image to Cloudinary.

    Args:
        file_storage: A Werkzeug FileStorage object from a form upload.
        folder: The Cloudinary folder to upload to.
        public_id: Optional custom public_id for the image.

    Returns:
        dict with 'url' and 'public_id' on success, or None on failure.
    """
    try:
        options = {
            'folder': folder,
            'overwrite': True,
            'resource_type': 'image',
            'transformation': [
                {'width': 800, 'height': 450, 'crop': 'fill', 'gravity': 'auto'},
                {'quality': 'auto', 'fetch_format': 'auto'}
            ]
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
