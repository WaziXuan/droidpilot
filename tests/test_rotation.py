import pytest
from PIL import Image

from droidpilot import uitree
from droidpilot.emulator import to_natural

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


def test_landscape_is_reported_in_the_header():
    xml = ('<hierarchy rotation="1"><node class="android.view.View" package="com.example.app" '
           'bounds="[0,0][2400,1080]" text="" content-desc="" resource-id="" clickable="false" '
           'scrollable="false" visible-to-user="true" /></hierarchy>')
    snap = uitree.parse(xml, (2400, 1080))
    assert snap.rotation == 1
    assert "orientation: landscape" in snap.render()
