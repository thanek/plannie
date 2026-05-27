import io
import base64

import qrcode


def qr_code_base64(url: str) -> str:
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
