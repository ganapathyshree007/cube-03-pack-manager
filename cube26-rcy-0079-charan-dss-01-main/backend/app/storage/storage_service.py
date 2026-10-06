import os
import shutil
from pathlib import Path
from typing import Tuple
from app.config.settings import settings

try:
    import cloudinary
    import cloudinary.uploader
    HAS_CLOUDINARY = True
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
except Exception:
    HAS_CLOUDINARY = False

class StorageService:
    @staticmethod
    def save_file(file_content: bytes, filename: str, company_id: str, file_type: str) -> Tuple[str, str]:
        """
        Saves a file to Cloudinary if configured, otherwise stores in local tenant-isolated folder.
        Returns: (file_url, local_path)
        """
        # Tenant isolated path
        tenant_dir = Path(settings.LOCAL_STORAGE_DIR) / f"company_{company_id}" / file_type
        tenant_dir.mkdir(parents=True, exist_ok=True)
        local_path = tenant_dir / filename
        
        with open(local_path, "wb") as f:
            f.write(file_content)
            
        cloudinary_url = None
        if HAS_CLOUDINARY and settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
            try:
                folder_path = f"rcy_recovery/company/{company_id}/{file_type}"
                result = cloudinary.uploader.upload(
                    str(local_path),
                    folder=folder_path,
                    resource_type="auto",
                    use_filename=True,
                    unique_filename=True
                )
                cloudinary_url = result.get("secure_url")
            except Exception as e:
                print(f"[Cloudinary Warning] Upload failed, falling back to local storage: {e}")
                
        file_url = cloudinary_url or f"/api/v1/files/download/{company_id}/{file_type}/{filename}"
        return file_url, str(local_path)

storage_service = StorageService()
