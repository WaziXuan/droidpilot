# droidpilot

An MCP server for driving an Android emulator from an LLM agent, built to be
fast and to not mislead the agent about what is on screen.

- **UI tree** from [uiautomator2](https://github.com/openatx/uiautomator2) (on-device server, ~30 ms per dump),
  compressed into a short numbered element list (~20x smaller than the raw XML).
- **Frames and touch** through the Android Emulator's own gRPC endpoint: a 108 px frame in ~2 ms,
  a 540 px screenshot in ~8 ms, and multi-touch gestures (pinch, drag).
- **Waits like a person**: every action waits until the screen has responded and stopped changing
  (and until page-load bars are gone), then returns the new element list. One round trip per step.

Real devices work too (everything falls back to uiautomator2); the gRPC fast paths are emulator-only.

## Setup

```bash
git clone https://github.com/WaziXuan/droidpilot && cd droidpilot
python -m venv .venv && .venv/bin/pip install -e .      # Windows: .venv\Scripts\pip install -e .
```

Start the emulator with the gRPC endpoint enabled:

```bash
emulator -avd <your_avd> -grpc 8554
```

Register the server with your MCP client, e.g. Claude Code:

```bash
claude mcp add droidpilot -- /path/to/droidpilot/.venv/bin/python -m droidpilot
```

Options (flags or environment variables):

| Flag | Env | Default | |
|---|---|---|---|
| `--serial` | `DROIDPILOT_SERIAL` | only connected device | adb serial |
| `--grpc` | `DROIDPILOT_GRPC` | `127.0.0.1:8554` | emulator gRPC address, `''` to disable |
| `--min-interval-ms` | `DROIDPILOT_MIN_INTERVAL_MS` | `300` | minimum gap between actions |
| `--transport` / `--port` | | `stdio` / `8765` | `streamable-http` keeps one server (and its handles) alive across clients |

## What the agent sees

```
package: com.android.settings  elements: 12  keyboard: shown (covers y>=1517)
[e1] ImageButton "Back" @(63,219) 126x147 click
[e2] EditText "dark" #open_search_view_edit_text @(529,220) 807x126 click,long,edit,focused
[e5] LinearLayout "Dark theme | Display" @(540,414) 1080x214 click
[e6] Switch #switch_widget @(944,414) 188x214 click,unchecked
[e11] LinearLayout "Bedtime mode" @(540,1549) 1080x214 click,under-keyboard
[e12] Key "Search" @(994,2196) 161x156 click,ime-action
```

`[handle] Class "label" #resource-id @(center) WxH flags`. Handles are valid for the latest list only.
The list leaves out status-bar icons, keyboard keys (except the action key), items scrolled under a
toolbar or out of their container, slivers too thin to tap, page-sized click targets, and wrappers that
repeat their child. The header adds `loading` while a spinner or page-load bar is visible.

## Tools

| Tool | |
|---|---|
| `observe(screenshot=False)` | element list, optionally with a screenshot |
| `screenshot(width=540)` | JPEG of the screen |
| `tap(target)` / `long_press(target)` | target is a handle (`e7`) or `x,y` device pixels |
| `tap_text(text, exact=False)` | tap the best element whose label matches |
| `swipe(start, end, duration_ms, hold_ms)` | `hold_ms > 0` makes it a drag |
| `scroll(direction, target, distance=0.6, fling=False)` | pages overlap by default |
| `pinch(zoom, target)` | two-finger zoom in/out (gRPC) |
| `type_text(text, clear=False)` | into the focused field; any Unicode |
| `press_key(key)` | `back`, `home`, `recent`, ...; `enter` taps the keyboard's action key |
| `wait_for(text, resource_id)` / `wait_idle()` | wait for an element / for loading to finish |
| `app_launch`, `app_stop`, `app_current`, `app_list` | app management |
| `status()` | backends in use |

Action tools return the settled element list (`observe_after=True`), with how long settling took.

## Design notes

Measured on an x86_64 Android 14 emulator (software rendering) on a Ryzen 7 7800X3D:

| Operation | Median |
|---|---|
| gRPC frame, 540 px wide | 8 ms |
| gRPC frame, full size | 32 ms |
| uiautomator2 hierarchy dump | 30 ms |
| `adb exec-out uiautomator dump` | 136 ms |
| `adb exec-out screencap` | 238 ms |
| `type_text` (accessibility set-text) | ~300 ms |
| uiautomator2 `send_keys` (clipboard paste) | ~2.8 s |
| uiautomator2 `app_current()` vs `dumpsys` | 5.1 s vs 35 ms |

- **Settling.** Dumping the hierarchy blocks while an app animates (~0.5 s per dump mid-transition),
  so settling polls tiny frames and dumps once at the end. A tap's ripple happens inside the tapped
  element and is not the response: a cold-started screen can sit still for ~0.4 s between ripple and
  transition, so only changes outside the touched element count. Settling continues while a progress
  bar is indeterminate or advancing (browser page loads), and stops for static gauges.
- **Typing** uses the accessibility set-text action: no clipboard (which raises the Android 13+
  clipboard overlay), no switching the user's input method, and the app's text watchers still fire.
- **Submitting.** Search boxes often ignore `KEYCODE_ENTER`; `press_key enter` taps the keyboard's
  action key, found in the keyboard's accessibility tree. `KEYCODE_SEARCH` is not used: it opens the
  Google app.
- **Scrolling** pauses the finger before lifting so lists move by the requested distance instead of
  flinging past items.
- **Rotation.** uiautomator reports coordinates for the current rotation, while gRPC frames and touch
  events stay in the display's natural orientation. The rotation is read from every hierarchy dump
  (no extra call); frames are turned upright before they are compared or returned, and every touch
  point is mapped back to natural coordinates. Verified for all four rotations against the frame
  rotation in tests, and on the emulator in both landscape directions.
- **Loading bars** are waited out for at most 2 s once the picture is still (pages often keep a bar
  up for a resource that never arrives); the element list still says `loading`, and `wait_idle`
  waits for as long as you allow.
- **Pacing.** A minimum gap between actions (300 ms) keeps taps from landing on half-drawn screens.

## Limitations

- Content without accessibility information (games, canvas, some WebViews) needs `screenshot`.
- The gRPC endpoint is unauthenticated on localhost; don't expose it.

## Development

```bash
pip install -e .[dev]
pytest                                         # offline tests for the element list
python scripts/bench.py                        # latency of each backend
python scripts/settle_trace.py "540,1355"      # frame-by-frame response to a tap
python scripts/mcp_call.py observe             # call tools like an MCP client
python scripts/gen_proto.py                    # regenerate gRPC stubs from proto/
```

## Related projects

- [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp): cross-platform (iOS + Android) MCP server
- [droidrun/mobilerun](https://github.com/droidrun/mobilerun): LLM-agnostic mobile agent framework
- [jodaco/android-uiautomator-mcp](https://github.com/jodaco/android-uiautomator-mcp),
  [tanbro/uiautomator2-mcp-server](https://github.com/tanbro/uiautomator2-mcp-server): uiautomator2-based MCP servers
- [openatx/uiautomator2](https://github.com/openatx/uiautomator2), which this builds on

## License

MIT. `proto/droidpilot/_proto/emulator_controller.proto` and the generated stubs come from the
Android Emulator and are Apache-2.0; see [LICENSE](LICENSE).
