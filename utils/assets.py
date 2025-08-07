import os
from functools import lru_cache
import pygame


def _assets_root_dir() -> str:
    # utils/ -> project_root/utils; assets lives at project_root/assets
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "assets"))


def _candidate_filenames(name: str):
    # Try common filename variants
    base = name
    yield f"{base}.png"
    base = name.replace(" ", "_")
    yield f"{base}.png"
    base = name.lower()
    yield f"{base}.png"
    yield f"{base.replace(' ', '_')}.png"


@lru_cache(maxsize=256)
def load_sprite_for(category: str, name: str):
    """Load a sprite Surface for the given name from assets/<category>/.
    Returns a pygame.Surface or None if not found.
    """
    assets_dir = os.path.join(_assets_root_dir(), category)
    for cand in _candidate_filenames(name):
        path = os.path.join(assets_dir, cand)
        if os.path.isfile(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception:
                # If load fails, try next candidate
                continue
    # Fallback: look for a default.png in the category
    default_path = os.path.join(assets_dir, "default.png")
    if os.path.isfile(default_path):
        try:
            return pygame.image.load(default_path).convert_alpha()
        except Exception:
            pass
    return None


def scale_to_fit(surface: pygame.Surface, target_w: int, target_h: int) -> pygame.Surface:
    """Scale a surface to fit within target box preserving aspect ratio."""
    if surface is None:
        return None
    sw, sh = surface.get_width(), surface.get_height()
    if sw == 0 or sh == 0:
        return surface
    scale = min(target_w / sw, target_h / sh)
    new_size = (max(1, int(sw * scale)), max(1, int(sh * scale)))
    return pygame.transform.smoothscale(surface, new_size)


