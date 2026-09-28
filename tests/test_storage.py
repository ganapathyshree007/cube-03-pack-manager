from io import BytesIO
import pytest
from PIL import Image
from backend.storage import normalize, MAX_BYTES, local_path


def test_decode_and_normalize_strips_exif():
    image = Image.new("RGB", (100, 100), "white")
    exif = Image.Exif()
    exif[270] = "Test-only metadata"
    stream = BytesIO()
    image.save(stream, format="JPEG", exif=exif)
    clean, size, original_hash = normalize(stream.getvalue())
    assert size == (100, 100)
    assert not Image.open(BytesIO(clean)).getexif()
    assert len(original_hash) == 64


@pytest.mark.parametrize(
    "data", [b"", b"not an image", b"x" * (MAX_BYTES + 1)], ids=["empty", "corrupt", "oversized"]
)
def test_invalid_upload(data):
    with pytest.raises(ValueError):
        normalize(data)


def test_path_escape_rejected():
    with pytest.raises(ValueError):
        local_path("../../outside.jpg")
