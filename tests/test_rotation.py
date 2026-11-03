from types import SimpleNamespace

import pytest
from PIL import Image

from droidpilot import uitree
from droidpilot.emulator import Emulator, to_natural

NATURAL = (12, 20)  # small stand-in for a 1080x2400 portrait display


@pytest.mark.parametrize("rotation", [0, 1, 2, 3])
@pytest.mark.parametrize("point", [(0, 0), (11, 0), (0, 19), (11, 19), (3, 7)])
def test_to_natural_inverts_the_frame_rotation(rotation, point):
    # Mark one pixel in a natural-orientation frame, turn it the way Emulator.screenshot
    # does, find the pixel in display space, and map it back.
    frame = Image.new("L", NATURAL)
    frame.putpixel(point, 255)
    shown = frame.rotate(90 * rotation, expand=True) if rotation else frame
    (dx, dy), = [(x, y) for y in range(shown.height) for x in range(shown.width) if shown.getpixel((x, y))]
    assert to_natural(dx, dy, rotation, NATURAL) == point


class FakeStub:
    """Serves frames the way the emulator does: in the body's (skin's) orientation."""

    def __init__(self, upright: Image.Image, display: int, skin: int):
        # `upright` is what the user sees; the emulator hands it out turned to the skin.
        self.frame = upright.rotate(-90 * ((display - skin) % 4), expand=True)
        self.skin = skin

    def getScreenshot(self, fmt):
        frame = self.frame
        if fmt.width or fmt.height:
            frame = frame.resize((fmt.width, fmt.height))
        return SimpleNamespace(
            format=SimpleNamespace(width=frame.width, height=frame.height,
                                   rotation=SimpleNamespace(rotation=self.skin)),
            image=frame.convert("RGB").tobytes())


@pytest.mark.parametrize("display", [0, 1, 3])
@pytest.mark.parametrize("skin", [0, 1, 3])
def test_screenshot_comes_out_as_the_user_sees_it(display, skin):
    # A display-oriented picture with a marker in its top-left corner.
    w, h = (40, 20) if display % 2 else (20, 40)
    upright = Image.new("RGB", (w, h))
    upright.paste((255, 0, 0), (0, 0, 4, 4))
    emu = Emulator.__new__(Emulator)
    emu._stub = FakeStub(upright, display, skin)
    emu._natural, emu.skin_rotation, emu.rotation = None, None, display
    shot = emu.screenshot()
    assert shot.size == (w, h)
    assert shot.getpixel((1, 1))[0] > 200 and shot.getpixel((w - 2, h - 2))[0] < 50
    assert emu.natural_size == (20, 40)


def test_landscape_is_reported_in_the_header():
    xml = ('<hierarchy rotation="1"><node class="android.view.View" package="com.example.app" '
           'bounds="[0,0][2400,1080]" text="" content-desc="" resource-id="" clickable="false" '
           'scrollable="false" visible-to-user="true" /></hierarchy>')
    snap = uitree.parse(xml, (2400, 1080))
    assert snap.rotation == 1
    assert "orientation: landscape" in snap.render()
