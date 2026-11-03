from droidpilot import uitree

SCREEN = (1080, 2400)


def node(bounds, children="", **attrs):
    a = {"class": "android.view.View", "package": "com.example.app", "text": "", "content-desc": "",
         "resource-id": "", "clickable": "false", "scrollable": "false", "visible-to-user": "true"}
    a.update({k.rstrip("_").replace("_", "-"): v for k, v in attrs.items()})
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


def test_keyboard_action_key_is_the_only_key_listed():
    ime_pkg = "com.google.android.inputmethod.latin"
    keys = "".join(node(b, content_desc=label, clickable="true", package=ime_pkg) for label, b in [
        ("q", "[5,1654][112,1808]"), ("Space", "[379,2118][807,2274]"),
        ("Search", "[914,2118][1075,2274]"), ("Switch input method", "[829,2274][1012,2400]")])
    keyboard = node("[0,1517][1080,2400]", keys, package=ime_pkg)
    app = node("[0,0][1080,2400]", node("[0,200][1080,400]", class_="android.widget.EditText",
                                        text="weather", clickable="true", focused="true"))
    snap = uitree.parse(hierarchy(app, keyboard), SCREEN)
    assert snap.ime_action is not None and snap.ime_action.text == "Search"
    assert snap.ime_action.center == (994, 2196)
    assert [e.text for e in snap.elements.values()] == ["weather", "Search"]
    assert "ime-action" in snap.ime_action.flags


def test_repeated_child_labels_are_merged():
    row = node("[0,400][1080,600]", node("[40,420][800,480]", text="0") + node("[900,420][1000,480]", content_desc="0"),
               clickable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", row)), SCREEN)
    assert [e.text for e in snap.elements.values()] == ["0"]


def test_progress_bars_mark_loading_only_when_indeterminate():
    page_bar = node("[0,278][1080,283]", class_="android.widget.ProgressBar")
    gauge = node("[63,830][1038,872]", class_="android.widget.ProgressBar", text="40.0")
    loading = uitree.parse(hierarchy(node("[0,0][1080,2400]", page_bar + gauge)), SCREEN)
    assert loading.loading and "loading" in loading.render()
    static = uitree.parse(hierarchy(node("[0,0][1080,2400]", gauge)), SCREEN)
    assert not static.loading and static.partial_progress()


def test_page_sized_click_targets_do_not_swallow_their_content():
    page = node("[0,280][1080,2400]",
                node("[40,400][300,460]", text="China", clickable="true")
                + node("[40,500][1000,560]", text="Some paragraph"),
                clickable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", page)), SCREEN)
    assert [e.text for e in snap.elements.values()] == ["China", "Some paragraph"]


def test_nested_wrappers_with_same_label_and_box_are_listed_once():
    inner = node("[960,700][1070,830]", content_desc="Download PDF", clickable="true")
    outer = node("[960,700][1070,830]", inner, content_desc="Download PDF", clickable="true")
    snap = uitree.parse(hierarchy(node("[0,0][1080,2400]", outer)), SCREEN)
    assert [e.text for e in snap.elements.values()] == ["Download PDF"]


def test_handles_are_sequential_and_lines_render():
    xml = hierarchy(node("[0,0][1080,2400]",
                         node("[0,200][540,400]", text="A", clickable="true", resource_id="com.example.app:id/a")
                         + node("[540,200][1080,400]", text="B", clickable="true")))
    snap = uitree.parse(xml, SCREEN)
    assert list(snap.elements) == ["e1", "e2"]
    assert snap.elements["e1"].line() == '[e1] View "A" #a @(270,300) 540x200 click'
