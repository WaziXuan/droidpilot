# droidpilot

Low-latency MCP server for driving an Android emulator from an LLM agent.

- **UI tree** via [uiautomator2](https://github.com/openatx/uiautomator2) (on-device server, ~30 ms per dump)
- **Frames and touch input** via the Android Emulator's gRPC endpoint (~8 ms for a downscaled frame, multi-touch gestures)

Work in progress.
