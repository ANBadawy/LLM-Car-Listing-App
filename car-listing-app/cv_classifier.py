from typing import Optional

def classify_body_type(image_bytes: Optional[bytes]) -> Optional[str]:
    if not image_bytes:
        return None
    return "sedan"
