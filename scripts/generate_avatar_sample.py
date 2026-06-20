"""Generate one persona AND its avatar, then save the PNG to look at.

End-to-end check of the identity+image pipeline (no X writes). Needs both keys
in .env: ANTHROPIC_API_KEY and OPENAI_API_KEY.

    python scripts/generate_avatar_sample.py [accessible|medium|cerebral]

Saves avatar_sample.png in the current folder; open it with:  open avatar_sample.png
"""

from __future__ import annotations

import sys

from anthropic import Anthropic
from openai import OpenAI

from finding_memeland.config import get_settings
from finding_memeland.persona.avatar import AvatarGenerator, save_png
from finding_memeland.persona.generator import PersonaGenerator

OUT_PATH = "avatar_sample.png"


def main() -> int:
    register = sys.argv[1] if len(sys.argv) > 1 else "accessible"
    s = get_settings()
    if not s.anthropic_api_key or s.anthropic_api_key.startswith("sk-ant-xxx"):
        print("FAIL — set a real ANTHROPIC_API_KEY in .env first.")
        return 2
    if not s.openai_api_key or s.openai_api_key.startswith("sk-proj-xxx"):
        print("FAIL — set a real OPENAI_API_KEY in .env first.")
        return 2

    persona = PersonaGenerator(
        Anthropic(api_key=s.anthropic_api_key), s.anthropic_model
    ).generate(register=register)

    print(f"register  : {register}")
    print(f"archetype : {persona.archetype}")
    print(f"name      : {persona.display_name}")
    print(f"bio       : {persona.bio}")
    print(f"avatar    : {persona.avatar_prompt}")

    avatars = AvatarGenerator(
        OpenAI(api_key=s.openai_api_key),
        model=s.openai_image_model,
        size=s.openai_image_size,
    )
    try:
        png = avatars.generate_png(persona.avatar_prompt)
    except Exception as e:  # noqa: BLE001
        print(f"\nFAIL — avatar generation error: {e!r}")
        print("       If it's an invalid-model error, set OPENAI_IMAGE_MODEL in .env.")
        return 1

    path = save_png(png, OUT_PATH)
    print(f"\nPASS — avatar saved ({len(png) // 1024} KB) -> {path}")
    print(f"open it with:  open {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
