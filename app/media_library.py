import os
import shutil
from pathlib import Path
from datetime import datetime
import mimetypes

class MediaLibraryManager:
    """Manage media file operations for the media library"""

    ALLOWED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png'}
    ALLOWED_VIDEO_TYPES = {'.mp4', '.avi', '.mov'}
    ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

    def __init__(self, media_dir="media"):
        self.media_dir = Path(media_dir)
        self._create_media_directory()

    def _create_media_directory(self):
        """Create media directory if it doesn't exist"""
        self.media_dir.mkdir(exist_ok=True)

    def validate_file(self, filename):
        """Validate file type and name"""
        file_ext = Path(filename).suffix.lower()

        if file_ext not in self.ALLOWED_TYPES:
            raise ValueError(f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(self.ALLOWED_TYPES)}")

        return True

    def get_file_type(self, filename):
        """Determine if file is image or video"""
        file_ext = Path(filename).suffix.lower()

        if file_ext in self.ALLOWED_IMAGE_TYPES:
            return "image"
        elif file_ext in self.ALLOWED_VIDEO_TYPES:
            return "video"
        else:
            raise ValueError(f"Unknown file type: {file_ext}")

    def save_file(self, uploaded_file):
        """
        Save uploaded file to media directory

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            tuple: (relative_file_path, file_type, file_size)
        """
        # Validate file
        self.validate_file(uploaded_file.name)

        # Generate unique filename with timestamp
        file_ext = Path(uploaded_file.name).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds precision
        unique_filename = f"{timestamp}{file_ext}"

        # Save file
        file_path = self.media_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Get file size
        file_size = file_path.stat().st_size

        # Determine file type
        file_type = self.get_file_type(uploaded_file.name)

        # Return relative path for database storage
        relative_path = str(file_path).replace('\\', '/')

        return relative_path, file_type, file_size

    def get_file_path(self, relative_path):
        """Convert relative path from database to actual file path"""
        return Path(relative_path)

    def delete_file(self, relative_path):
        """Delete file from disk"""
        try:
            file_path = self.get_file_path(relative_path)
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting file {relative_path}: {str(e)}")
            return False

    def get_file_size_mb(self, file_size_bytes):
        """Convert bytes to MB"""
        return round(file_size_bytes / (1024 * 1024), 2)

    def file_exists(self, relative_path):
        """Check if file exists"""
        return self.get_file_path(relative_path).exists()
