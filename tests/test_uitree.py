from droidpilot import uitree

SCREEN = (1080, 2400)


def node(bounds, children="", **attrs):
    a = {"class": "android.view.View", "package": "com.example.app", "text": "", "content-desc": "",
         "resource-id": "", "clickable": "false", "scrollable": "false", "visible-to-user": "true"}
    a.update({k.replace("_", "-"): v for k, v in attrs.items()})
    attr_s = " ".join(f'{k}="{v}"' for k, v in a.items())
    return f'<node {attr_s} bounds="{bounds}">{children}</node>'


def hierarchy(*windows):
    return f'<hierarchy rotation="0">{"".join(windows)}</hierarchy>'


STATUS_BAR = node("[0,0][1080,136]", node(
    "[0,0][1080,136]", node("[40,30][130,100]", text="6:33", resource_id="com.android.systemui:id/clock",
                            package="com.android.systemui"),
    resource_id="com.android.systemui:id/status_bar_container", package="com.android.systemui"),
    package="com.android.systemui")


def test_main_window_is_package_and_status_bar_is_dropped():
    xml = hierarchy(STATUS_BAR, node("[0,0][1080,2400]", node("[0,200][1080,400]", text="Hello")))
    snap = uitree.parse(xml, SCREEN)
    assert snap.package == "com.example.app"
    assert [e.text for e in snap.elements.values()] == ["Hello"]


def test_keyboard_is_reported_and_flags_hidden_elements():
    keyboard = node("[0,1500][1080,2400]", node("[0,1600][100,1700]", text="q",
                                                  package="com.google.android.inputmethod.latin"),
                    package="com.google.android.inputmethod.latin")
    app = node("[0,0][1080,2400]",
               node("[0,200][1080,400]", text="Search", clickable="true")
               + node("[0,2000][1080,2200]", text="Footer", clickable="true"))
    snap = uitree.parse(hierarchy(app, keyboard), SCREEN)
    assert snap.keyboard_top == 1500
    by_text = {e.text: e for e in snap.elements.values()}
    assert "q" not in by_text  # keyboard keys are not listed
    assert "under-keyboard" not in by_text["Search"].flags
    assert "under-keyboard" in by_text["Footer"].flags
    assert "keyboard: shown" in snap.render()


def test_items_scrolled_under_toolbar_are_dropped():
    toolbar = node("[0,0][1080,600]", text="All apps")
    lst = node("[0,600][1080,2400]",
               node("[0,300][1080,560]", text="Fully under toolbar", clickable="true")
               + node("[0,800][1080,1000]", text="Visible", clickable="true"),
               scrollable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", toolbar + lst)), SCREEN)
    texts = [e.text for e in snap.elements.values()]
    assert "Visible" in texts
    assert "Fully under toolbar" not in texts


def test_slivers_are_dropped():
    lst = node("[0,283][1080,2400]",
               node("[0,283][1080,297]", clickable="true")
               + node("[0,400][1080,600]", text="Maps", clickable="true"),
               scrollable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", lst)), SCREEN)
    assert [e.text for e in snap.elements.values() if "click" in e.flags] == ["Maps"]


def test_clickable_container_takes_child_labels_once():
    row = node("[0,400][1080,600]",
               node("[40,420][800,480]", text="Wi-Fi") + node("[40,500][800,560]", text="Connected"),
               clickable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", row)), SCREEN)
    assert [e.text for e in snap.elements.values()] == ["Wi-Fi | Connected"]


def test_handles_are_sequential_and_lines_render():
    xml = hierarchy(node("[0,0][1080,2400]",
                         node("[0,200][540,400]", text="A", clickable="true", resource_id="com.example.app:id/a")
                         + node("[540,200][1080,400]", text="B", clickable="true")))
    snap = uitree.parse(xml, SCREEN)
    assert list(snap.elements) == ["e1", "e2"]
    assert snap.elements["e1"].line() == '[e1] View "A" #a @(270,300) 540x200 click'
