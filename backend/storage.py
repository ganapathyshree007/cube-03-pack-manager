import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import settings

MAX_BYTES = 10 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


def normalize(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Image must be between 1 byte and 10 MiB")
    try:
        with Image.open(BytesIO(raw)) as original:
            if original.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Use a JPEG, PNG or WebP image")
            if original.width * original.height > 20_000_000 or min(original.size) < 64:
                raise ValueError("Image must be at least 64 pixels per side and at most 20 megapixels")
            original.load()
            clean = ImageOps.exif_transpose(original).convert("RGB")
            clean.thumbnail((2048, 2048))
            output = BytesIO()
            clean.save(output, "JPEG", quality=92)
            return output.getvalue(), clean.size, hashlib.sha256(raw).hexdigest()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Image cannot be safely decoded") from exc


def blob_client(key):
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient(
        settings().azure_storage_account_url, credential=DefaultAzureCredential()
    ).get_blob_client(settings().azure_storage_container, key)


def local_path(key):
    root = Path(settings().storage_root).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid storage key")
    return path


def save(key, data):
    if settings().storage_mode == "azure":
        blob_client(key).upload_blob(data, overwrite=False)
    else:
        path = local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)


def read(key):
    if settings().storage_mode == "azure":
        return blob_client(key).download_blob().readall()
    return local_path(key).read_bytes()


def delete(key):
    if settings().storage_mode == "azure":
        from azure.core.exceptions import ResourceNotFoundError

        try:
            blob_client(key).delete_blob()
        except ResourceNotFoundError:
            pass
    else:
        local_path(key).unlink(missing_ok=True)
