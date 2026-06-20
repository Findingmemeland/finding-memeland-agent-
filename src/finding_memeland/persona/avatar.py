"""Avatar generation via an image model (OpenAI gpt-image).

The image client is injected (like the Anthropic client for text), so this
module imports no SDK and stays easy to test. The Persona Generator produces an
`avatar_prompt`; this turns it into PNG bytes for the Persona Dresser to upload.

Safety: avatars must never depict a real person's likeness or contain text /
watermarks (text on an avatar reads as botty). We append style constraints to
every prompt to enforce that.
"""

from __future__ import annotations

import base64

# Appended to every avatar prompt.
AVATAR_STYLE_SUFFIX = (
    ", profile picture composition, no text, no watermark, no logos, "
    "not a real living person, no recognizable real-person likeness"
)


class AvatarGenerator:
    def __init__(self, client, *, model: str = "gpt-image-1", size: str = "1024x1024"):
        self._client = client
        self._model = model
        self._size = size

    def generate_png(self, avatar_prompt: str) -> bytes:
        """Generate the avatar and return PNG bytes."""
        prompt = avatar_prompt.strip() + AVATAR_STYLE_SUFFIX
        resp = self._client.images.generate(
            model=self._model, prompt=prompt, size=self._size, n=1
        )
        b64 = getattr(resp.data[0], "b64_json", None)
        if not b64:
            raise RuntimeError(
                "image API returned no b64_json — check the model id / response format"
            )
        return base64.b64decode(b64)


def save_png(data: bytes, path: str) -> str:
    """Write PNG bytes to a file; return the path."""
    with open(path, "wb") as fh:
        fh.write(data)
    return path
