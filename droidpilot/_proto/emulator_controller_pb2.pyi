from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DisplayModeValue(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PHONE: _ClassVar[DisplayModeValue]
    FOLDABLE: _ClassVar[DisplayModeValue]
    TABLET: _ClassVar[DisplayModeValue]
    DESKTOP: _ClassVar[DisplayModeValue]
PHONE: DisplayModeValue
FOLDABLE: DisplayModeValue
TABLET: DisplayModeValue
DESKTOP: DisplayModeValue

class VmRunState(_message.Message):
    __slots__ = ("state",)
    class RunState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[VmRunState.RunState]
        RUNNING: _ClassVar[VmRunState.RunState]
        RESTORE_VM: _ClassVar[VmRunState.RunState]
        PAUSED: _ClassVar[VmRunState.RunState]
        SAVE_VM: _ClassVar[VmRunState.RunState]
        SHUTDOWN: _ClassVar[VmRunState.RunState]
        TERMINATE: _ClassVar[VmRunState.RunState]
        RESET: _ClassVar[VmRunState.RunState]
        INTERNAL_ERROR: _ClassVar[VmRunState.RunState]
        RESTART: _ClassVar[VmRunState.RunState]
        START: _ClassVar[VmRunState.RunState]
        STOP: _ClassVar[VmRunState.RunState]
    UNKNOWN: VmRunState.RunState
    RUNNING: VmRunState.RunState
    RESTORE_VM: VmRunState.RunState
    PAUSED: VmRunState.RunState
    SAVE_VM: VmRunState.RunState
    SHUTDOWN: VmRunState.RunState
    TERMINATE: VmRunState.RunState
    RESET: VmRunState.RunState
    INTERNAL_ERROR: VmRunState.RunState
    RESTART: VmRunState.RunState
    START: VmRunState.RunState
    STOP: VmRunState.RunState
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: VmRunState.RunState
    def __init__(self, state: _Optional[_Union[VmRunState.RunState, str]] = ...) -> None: ...

class ParameterValue(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, data: _Optional[_Iterable[float]] = ...) -> None: ...

class PhysicalModelValue(_message.Message):
    __slots__ = ("target", "status", "value")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OK: _ClassVar[PhysicalModelValue.State]
        NO_SERVICE: _ClassVar[PhysicalModelValue.State]
        DISABLED: _ClassVar[PhysicalModelValue.State]
        UNKNOWN: _ClassVar[PhysicalModelValue.State]
    OK: PhysicalModelValue.State
    NO_SERVICE: PhysicalModelValue.State
    DISABLED: PhysicalModelValue.State
    UNKNOWN: PhysicalModelValue.State
    class PhysicalType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        POSITION: _ClassVar[PhysicalModelValue.PhysicalType]
        ROTATION: _ClassVar[PhysicalModelValue.PhysicalType]
        MAGNETIC_FIELD: _ClassVar[PhysicalModelValue.PhysicalType]
        TEMPERATURE: _ClassVar[PhysicalModelValue.PhysicalType]
        PROXIMITY: _ClassVar[PhysicalModelValue.PhysicalType]
        LIGHT: _ClassVar[PhysicalModelValue.PhysicalType]
        PRESSURE: _ClassVar[PhysicalModelValue.PhysicalType]
        HUMIDITY: _ClassVar[PhysicalModelValue.PhysicalType]
        VELOCITY: _ClassVar[PhysicalModelValue.PhysicalType]
        AMBIENT_MOTION: _ClassVar[PhysicalModelValue.PhysicalType]
        HINGE_ANGLE0: _ClassVar[PhysicalModelValue.PhysicalType]
        HINGE_ANGLE1: _ClassVar[PhysicalModelValue.PhysicalType]
        HINGE_ANGLE2: _ClassVar[PhysicalModelValue.PhysicalType]
        ROLLABLE0: _ClassVar[PhysicalModelValue.PhysicalType]
        ROLLABLE1: _ClassVar[PhysicalModelValue.PhysicalType]
        ROLLABLE2: _ClassVar[PhysicalModelValue.PhysicalType]
        POSTURE: _ClassVar[PhysicalModelValue.PhysicalType]
        HEART_RATE: _ClassVar[PhysicalModelValue.PhysicalType]
        RGBC_LIGHT: _ClassVar[PhysicalModelValue.PhysicalType]
        WRIST_TILT: _ClassVar[PhysicalModelValue.PhysicalType]
    POSITION: PhysicalModelValue.PhysicalType
    ROTATION: PhysicalModelValue.PhysicalType
    MAGNETIC_FIELD: PhysicalModelValue.PhysicalType
    TEMPERATURE: PhysicalModelValue.PhysicalType
    PROXIMITY: PhysicalModelValue.PhysicalType
    LIGHT: PhysicalModelValue.PhysicalType
    PRESSURE: PhysicalModelValue.PhysicalType
    HUMIDITY: PhysicalModelValue.PhysicalType
    VELOCITY: PhysicalModelValue.PhysicalType
    AMBIENT_MOTION: PhysicalModelValue.PhysicalType
    HINGE_ANGLE0: PhysicalModelValue.PhysicalType
    HINGE_ANGLE1: PhysicalModelValue.PhysicalType
    HINGE_ANGLE2: PhysicalModelValue.PhysicalType
    ROLLABLE0: PhysicalModelValue.PhysicalType
    ROLLABLE1: PhysicalModelValue.PhysicalType
    ROLLABLE2: PhysicalModelValue.PhysicalType
    POSTURE: PhysicalModelValue.PhysicalType
    HEART_RATE: PhysicalModelValue.PhysicalType
    RGBC_LIGHT: PhysicalModelValue.PhysicalType
    WRIST_TILT: PhysicalModelValue.PhysicalType
    TARGET_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    target: PhysicalModelValue.PhysicalType
    status: PhysicalModelValue.State
    value: ParameterValue
    def __init__(self, target: _Optional[_Union[PhysicalModelValue.PhysicalType, str]] = ..., status: _Optional[_Union[PhysicalModelValue.State, str]] = ..., value: _Optional[_Union[ParameterValue, _Mapping]] = ...) -> None: ...

class SensorValue(_message.Message):
    __slots__ = ("target", "status", "value")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OK: _ClassVar[SensorValue.State]
        NO_SERVICE: _ClassVar[SensorValue.State]
        DISABLED: _ClassVar[SensorValue.State]
        UNKNOWN: _ClassVar[SensorValue.State]
    OK: SensorValue.State
    NO_SERVICE: SensorValue.State
    DISABLED: SensorValue.State
    UNKNOWN: SensorValue.State
    class SensorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ACCELERATION: _ClassVar[SensorValue.SensorType]
        GYROSCOPE: _ClassVar[SensorValue.SensorType]
        MAGNETIC_FIELD: _ClassVar[SensorValue.SensorType]
        ORIENTATION: _ClassVar[SensorValue.SensorType]
        TEMPERATURE: _ClassVar[SensorValue.SensorType]
        PROXIMITY: _ClassVar[SensorValue.SensorType]
        LIGHT: _ClassVar[SensorValue.SensorType]
        PRESSURE: _ClassVar[SensorValue.SensorType]
        HUMIDITY: _ClassVar[SensorValue.SensorType]
        MAGNETIC_FIELD_UNCALIBRATED: _ClassVar[SensorValue.SensorType]
        GYROSCOPE_UNCALIBRATED: _ClassVar[SensorValue.SensorType]
        HEART_RATE: _ClassVar[SensorValue.SensorType]
        RGBC_LIGHT: _ClassVar[SensorValue.SensorType]
        ACCELERATION_UNCALIBRATED: _ClassVar[SensorValue.SensorType]
        HEADING: _ClassVar[SensorValue.SensorType]
    ACCELERATION: SensorValue.SensorType
    GYROSCOPE: SensorValue.SensorType
    MAGNETIC_FIELD: SensorValue.SensorType
    ORIENTATION: SensorValue.SensorType
    TEMPERATURE: SensorValue.SensorType
    PROXIMITY: SensorValue.SensorType
    LIGHT: SensorValue.SensorType
    PRESSURE: SensorValue.SensorType
    HUMIDITY: SensorValue.SensorType
    MAGNETIC_FIELD_UNCALIBRATED: SensorValue.SensorType
    GYROSCOPE_UNCALIBRATED: SensorValue.SensorType
    HEART_RATE: SensorValue.SensorType
    RGBC_LIGHT: SensorValue.SensorType
    ACCELERATION_UNCALIBRATED: SensorValue.SensorType
    HEADING: SensorValue.SensorType
    TARGET_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    target: SensorValue.SensorType
    status: SensorValue.State
    value: ParameterValue
    def __init__(self, target: _Optional[_Union[SensorValue.SensorType, str]] = ..., status: _Optional[_Union[SensorValue.State, str]] = ..., value: _Optional[_Union[ParameterValue, _Mapping]] = ...) -> None: ...

class BrightnessValue(_message.Message):
    __slots__ = ("target", "value")
    class LightType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LCD: _ClassVar[BrightnessValue.LightType]
        KEYBOARD: _ClassVar[BrightnessValue.LightType]
        BUTTON: _ClassVar[BrightnessValue.LightType]
    LCD: BrightnessValue.LightType
    KEYBOARD: BrightnessValue.LightType
    BUTTON: BrightnessValue.LightType
    TARGET_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    target: BrightnessValue.LightType
    value: int
    def __init__(self, target: _Optional[_Union[BrightnessValue.LightType, str]] = ..., value: _Optional[int] = ...) -> None: ...

class DisplayMode(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: DisplayModeValue
    def __init__(self, value: _Optional[_Union[DisplayModeValue, str]] = ...) -> None: ...

class XrOptions(_message.Message):
    __slots__ = ("environment", "passthrough_coefficient")
    class Environment(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LIVING_ROOM_DAY: _ClassVar[XrOptions.Environment]
        LIVING_ROOM_NIGHT: _ClassVar[XrOptions.Environment]
    LIVING_ROOM_DAY: XrOptions.Environment
    LIVING_ROOM_NIGHT: XrOptions.Environment
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    PASSTHROUGH_COEFFICIENT_FIELD_NUMBER: _ClassVar[int]
    environment: XrOptions.Environment
    passthrough_coefficient: float
    def __init__(self, environment: _Optional[_Union[XrOptions.Environment, str]] = ..., passthrough_coefficient: _Optional[float] = ...) -> None: ...

class LogMessage(_message.Message):
    __slots__ = ("contents", "start", "next", "sort", "entries")
    class LogType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Text: _ClassVar[LogMessage.LogType]
        Parsed: _ClassVar[LogMessage.LogType]
    Text: LogMessage.LogType
    Parsed: LogMessage.LogType
    CONTENTS_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    NEXT_FIELD_NUMBER: _ClassVar[int]
    SORT_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    contents: str
    start: int
    next: int
    sort: LogMessage.LogType
    entries: _containers.RepeatedCompositeFieldContainer[LogcatEntry]
    def __init__(self, contents: _Optional[str] = ..., start: _Optional[int] = ..., next: _Optional[int] = ..., sort: _Optional[_Union[LogMessage.LogType, str]] = ..., entries: _Optional[_Iterable[_Union[LogcatEntry, _Mapping]]] = ...) -> None: ...

class LogcatEntry(_message.Message):
    __slots__ = ("timestamp", "pid", "tid", "level", "tag", "msg")
    class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[LogcatEntry.LogLevel]
        DEFAULT: _ClassVar[LogcatEntry.LogLevel]
        VERBOSE: _ClassVar[LogcatEntry.LogLevel]
        DEBUG: _ClassVar[LogcatEntry.LogLevel]
        INFO: _ClassVar[LogcatEntry.LogLevel]
        WARN: _ClassVar[LogcatEntry.LogLevel]
        ERR: _ClassVar[LogcatEntry.LogLevel]
        FATAL: _ClassVar[LogcatEntry.LogLevel]
        SILENT: _ClassVar[LogcatEntry.LogLevel]
    UNKNOWN: LogcatEntry.LogLevel
    DEFAULT: LogcatEntry.LogLevel
    VERBOSE: LogcatEntry.LogLevel
    DEBUG: LogcatEntry.LogLevel
    INFO: LogcatEntry.LogLevel
    WARN: LogcatEntry.LogLevel
    ERR: LogcatEntry.LogLevel
    FATAL: LogcatEntry.LogLevel
    SILENT: LogcatEntry.LogLevel
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    TID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    pid: int
    tid: int
    level: LogcatEntry.LogLevel
    tag: str
    msg: str
    def __init__(self, timestamp: _Optional[int] = ..., pid: _Optional[int] = ..., tid: _Optional[int] = ..., level: _Optional[_Union[LogcatEntry.LogLevel, str]] = ..., tag: _Optional[str] = ..., msg: _Optional[str] = ...) -> None: ...

class VmConfiguration(_message.Message):
    __slots__ = ("hypervisorType", "numberOfCpuCores", "ramSizeBytes")
    class VmHypervisorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[VmConfiguration.VmHypervisorType]
        NONE: _ClassVar[VmConfiguration.VmHypervisorType]
        KVM: _ClassVar[VmConfiguration.VmHypervisorType]
        HAXM: _ClassVar[VmConfiguration.VmHypervisorType]
        HVF: _ClassVar[VmConfiguration.VmHypervisorType]
        WHPX: _ClassVar[VmConfiguration.VmHypervisorType]
        AEHD: _ClassVar[VmConfiguration.VmHypervisorType]
    UNKNOWN: VmConfiguration.VmHypervisorType
    NONE: VmConfiguration.VmHypervisorType
    KVM: VmConfiguration.VmHypervisorType
    HAXM: VmConfiguration.VmHypervisorType
    HVF: VmConfiguration.VmHypervisorType
    WHPX: VmConfiguration.VmHypervisorType
    AEHD: VmConfiguration.VmHypervisorType
    HYPERVISORTYPE_FIELD_NUMBER: _ClassVar[int]
    NUMBEROFCPUCORES_FIELD_NUMBER: _ClassVar[int]
    RAMSIZEBYTES_FIELD_NUMBER: _ClassVar[int]
    hypervisorType: VmConfiguration.VmHypervisorType
    numberOfCpuCores: int
    ramSizeBytes: int
    def __init__(self, hypervisorType: _Optional[_Union[VmConfiguration.VmHypervisorType, str]] = ..., numberOfCpuCores: _Optional[int] = ..., ramSizeBytes: _Optional[int] = ...) -> None: ...

class ClipData(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class Touch(_message.Message):
    __slots__ = ("x", "y", "identifier", "pressure", "touch_major", "touch_minor", "expiration", "orientation")
    class EventExpiration(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        EVENT_EXPIRATION_UNSPECIFIED: _ClassVar[Touch.EventExpiration]
        NEVER_EXPIRE: _ClassVar[Touch.EventExpiration]
    EVENT_EXPIRATION_UNSPECIFIED: Touch.EventExpiration
    NEVER_EXPIRE: Touch.EventExpiration
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    PRESSURE_FIELD_NUMBER: _ClassVar[int]
    TOUCH_MAJOR_FIELD_NUMBER: _ClassVar[int]
    TOUCH_MINOR_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    identifier: int
    pressure: int
    touch_major: int
    touch_minor: int
    expiration: Touch.EventExpiration
    orientation: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., identifier: _Optional[int] = ..., pressure: _Optional[int] = ..., touch_major: _Optional[int] = ..., touch_minor: _Optional[int] = ..., expiration: _Optional[_Union[Touch.EventExpiration, str]] = ..., orientation: _Optional[int] = ...) -> None: ...

class Pen(_message.Message):
    __slots__ = ("location", "button_pressed", "rubber_pointer")
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    BUTTON_PRESSED_FIELD_NUMBER: _ClassVar[int]
    RUBBER_POINTER_FIELD_NUMBER: _ClassVar[int]
    location: Touch
    button_pressed: bool
    rubber_pointer: bool
    def __init__(self, location: _Optional[_Union[Touch, _Mapping]] = ..., button_pressed: _Optional[bool] = ..., rubber_pointer: _Optional[bool] = ...) -> None: ...

class TouchEvent(_message.Message):
    __slots__ = ("touches", "display")
    TOUCHES_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    touches: _containers.RepeatedCompositeFieldContainer[Touch]
    display: int
    def __init__(self, touches: _Optional[_Iterable[_Union[Touch, _Mapping]]] = ..., display: _Optional[int] = ...) -> None: ...

class TouchpadEvent(_message.Message):
    __slots__ = ("touches", "touchpad")
    TOUCHES_FIELD_NUMBER: _ClassVar[int]
    TOUCHPAD_FIELD_NUMBER: _ClassVar[int]
    touches: _containers.RepeatedCompositeFieldContainer[Touch]
    touchpad: int
    def __init__(self, touches: _Optional[_Iterable[_Union[Touch, _Mapping]]] = ..., touchpad: _Optional[int] = ...) -> None: ...

class PenEvent(_message.Message):
    __slots__ = ("events", "display")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[Pen]
    display: int
    def __init__(self, events: _Optional[_Iterable[_Union[Pen, _Mapping]]] = ..., display: _Optional[int] = ...) -> None: ...

class MouseEvent(_message.Message):
    __slots__ = ("x", "y", "buttons", "display")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    BUTTONS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    buttons: int
    display: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ..., buttons: _Optional[int] = ..., display: _Optional[int] = ...) -> None: ...

class WheelEvent(_message.Message):
    __slots__ = ("dx", "dy", "display")
    DX_FIELD_NUMBER: _ClassVar[int]
    DY_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    dx: int
    dy: int
    display: int
    def __init__(self, dx: _Optional[int] = ..., dy: _Optional[int] = ..., display: _Optional[int] = ...) -> None: ...

class KeyboardEvent(_message.Message):
    __slots__ = ("codeType", "eventType", "keyCode", "key", "text")
    class KeyCodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Usb: _ClassVar[KeyboardEvent.KeyCodeType]
        Evdev: _ClassVar[KeyboardEvent.KeyCodeType]
        XKB: _ClassVar[KeyboardEvent.KeyCodeType]
        Win: _ClassVar[KeyboardEvent.KeyCodeType]
        Mac: _ClassVar[KeyboardEvent.KeyCodeType]
    Usb: KeyboardEvent.KeyCodeType
    Evdev: KeyboardEvent.KeyCodeType
    XKB: KeyboardEvent.KeyCodeType
    Win: KeyboardEvent.KeyCodeType
    Mac: KeyboardEvent.KeyCodeType
    class KeyEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        keydown: _ClassVar[KeyboardEvent.KeyEventType]
        keyup: _ClassVar[KeyboardEvent.KeyEventType]
        keypress: _ClassVar[KeyboardEvent.KeyEventType]
    keydown: KeyboardEvent.KeyEventType
    keyup: KeyboardEvent.KeyEventType
    keypress: KeyboardEvent.KeyEventType
    CODETYPE_FIELD_NUMBER: _ClassVar[int]
    EVENTTYPE_FIELD_NUMBER: _ClassVar[int]
    KEYCODE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    codeType: KeyboardEvent.KeyCodeType
    eventType: KeyboardEvent.KeyEventType
    keyCode: int
    key: str
    text: str
    def __init__(self, codeType: _Optional[_Union[KeyboardEvent.KeyCodeType, str]] = ..., eventType: _Optional[_Union[KeyboardEvent.KeyEventType, str]] = ..., keyCode: _Optional[int] = ..., key: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class XrCommand(_message.Message):
    __slots__ = ("action",)
    class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        RECENTER: _ClassVar[XrCommand.Action]
    RECENTER: XrCommand.Action
    ACTION_FIELD_NUMBER: _ClassVar[int]
    action: XrCommand.Action
    def __init__(self, action: _Optional[_Union[XrCommand.Action, str]] = ...) -> None: ...

class InputEvent(_message.Message):
    __slots__ = ("key_event", "touch_event", "mouse_event", "android_event", "pen_event", "wheel_event", "xr_hand_event", "xr_eye_event", "xr_command", "xr_head_rotation_event", "xr_head_movement_event", "xr_head_angular_velocity_event", "xr_head_velocity_event", "touchpad_event")
    KEY_EVENT_FIELD_NUMBER: _ClassVar[int]
    TOUCH_EVENT_FIELD_NUMBER: _ClassVar[int]
    MOUSE_EVENT_FIELD_NUMBER: _ClassVar[int]
    ANDROID_EVENT_FIELD_NUMBER: _ClassVar[int]
    PEN_EVENT_FIELD_NUMBER: _ClassVar[int]
    WHEEL_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_HAND_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_EYE_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_COMMAND_FIELD_NUMBER: _ClassVar[int]
    XR_HEAD_ROTATION_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_HEAD_MOVEMENT_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_HEAD_ANGULAR_VELOCITY_EVENT_FIELD_NUMBER: _ClassVar[int]
    XR_HEAD_VELOCITY_EVENT_FIELD_NUMBER: _ClassVar[int]
    TOUCHPAD_EVENT_FIELD_NUMBER: _ClassVar[int]
    key_event: KeyboardEvent
    touch_event: TouchEvent
    mouse_event: MouseEvent
    android_event: AndroidEvent
    pen_event: PenEvent
    wheel_event: WheelEvent
    xr_hand_event: MouseEvent
    xr_eye_event: MouseEvent
    xr_command: XrCommand
    xr_head_rotation_event: RotationRadian
    xr_head_movement_event: Translation
    xr_head_angular_velocity_event: AngularVelocity
    xr_head_velocity_event: Velocity
    touchpad_event: TouchpadEvent
    def __init__(self, key_event: _Optional[_Union[KeyboardEvent, _Mapping]] = ..., touch_event: _Optional[_Union[TouchEvent, _Mapping]] = ..., mouse_event: _Optional[_Union[MouseEvent, _Mapping]] = ..., android_event: _Optional[_Union[AndroidEvent, _Mapping]] = ..., pen_event: _Optional[_Union[PenEvent, _Mapping]] = ..., wheel_event: _Optional[_Union[WheelEvent, _Mapping]] = ..., xr_hand_event: _Optional[_Union[MouseEvent, _Mapping]] = ..., xr_eye_event: _Optional[_Union[MouseEvent, _Mapping]] = ..., xr_command: _Optional[_Union[XrCommand, _Mapping]] = ..., xr_head_rotation_event: _Optional[_Union[RotationRadian, _Mapping]] = ..., xr_head_movement_event: _Optional[_Union[Translation, _Mapping]] = ..., xr_head_angular_velocity_event: _Optional[_Union[AngularVelocity, _Mapping]] = ..., xr_head_velocity_event: _Optional[_Union[Velocity, _Mapping]] = ..., touchpad_event: _Optional[_Union[TouchpadEvent, _Mapping]] = ...) -> None: ...

class AndroidEvent(_message.Message):
    __slots__ = ("type", "code", "value", "display")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    type: int
    code: int
    value: int
    display: int
    def __init__(self, type: _Optional[int] = ..., code: _Optional[int] = ..., value: _Optional[int] = ..., display: _Optional[int] = ...) -> None: ...

class Fingerprint(_message.Message):
    __slots__ = ("isTouching", "touchId")
    ISTOUCHING_FIELD_NUMBER: _ClassVar[int]
    TOUCHID_FIELD_NUMBER: _ClassVar[int]
    isTouching: bool
    touchId: int
    def __init__(self, isTouching: _Optional[bool] = ..., touchId: _Optional[int] = ...) -> None: ...

class GpsState(_message.Message):
    __slots__ = ("passiveUpdate", "latitude", "longitude", "speed", "bearing", "altitude", "satellites")
    PASSIVEUPDATE_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    BEARING_FIELD_NUMBER: _ClassVar[int]
    ALTITUDE_FIELD_NUMBER: _ClassVar[int]
    SATELLITES_FIELD_NUMBER: _ClassVar[int]
    passiveUpdate: bool
    latitude: float
    longitude: float
    speed: float
    bearing: float
    altitude: float
    satellites: int
    def __init__(self, passiveUpdate: _Optional[bool] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., speed: _Optional[float] = ..., bearing: _Optional[float] = ..., altitude: _Optional[float] = ..., satellites: _Optional[int] = ...) -> None: ...

class BatteryState(_message.Message):
    __slots__ = ("hasBattery", "isPresent", "charger", "chargeLevel", "health", "status")
    class BatteryStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[BatteryState.BatteryStatus]
        CHARGING: _ClassVar[BatteryState.BatteryStatus]
        DISCHARGING: _ClassVar[BatteryState.BatteryStatus]
        NOT_CHARGING: _ClassVar[BatteryState.BatteryStatus]
        FULL: _ClassVar[BatteryState.BatteryStatus]
    UNKNOWN: BatteryState.BatteryStatus
    CHARGING: BatteryState.BatteryStatus
    DISCHARGING: BatteryState.BatteryStatus
    NOT_CHARGING: BatteryState.BatteryStatus
    FULL: BatteryState.BatteryStatus
    class BatteryCharger(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NONE: _ClassVar[BatteryState.BatteryCharger]
        AC: _ClassVar[BatteryState.BatteryCharger]
        USB: _ClassVar[BatteryState.BatteryCharger]
        WIRELESS: _ClassVar[BatteryState.BatteryCharger]
    NONE: BatteryState.BatteryCharger
    AC: BatteryState.BatteryCharger
    USB: BatteryState.BatteryCharger
    WIRELESS: BatteryState.BatteryCharger
    class BatteryHealth(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        GOOD: _ClassVar[BatteryState.BatteryHealth]
        FAILED: _ClassVar[BatteryState.BatteryHealth]
        DEAD: _ClassVar[BatteryState.BatteryHealth]
        OVERVOLTAGE: _ClassVar[BatteryState.BatteryHealth]
        OVERHEATED: _ClassVar[BatteryState.BatteryHealth]
    GOOD: BatteryState.BatteryHealth
    FAILED: BatteryState.BatteryHealth
    DEAD: BatteryState.BatteryHealth
    OVERVOLTAGE: BatteryState.BatteryHealth
    OVERHEATED: BatteryState.BatteryHealth
    HASBATTERY_FIELD_NUMBER: _ClassVar[int]
    ISPRESENT_FIELD_NUMBER: _ClassVar[int]
    CHARGER_FIELD_NUMBER: _ClassVar[int]
    CHARGELEVEL_FIELD_NUMBER: _ClassVar[int]
    HEALTH_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    hasBattery: bool
    isPresent: bool
    charger: BatteryState.BatteryCharger
    chargeLevel: int
    health: BatteryState.BatteryHealth
    status: BatteryState.BatteryStatus
    def __init__(self, hasBattery: _Optional[bool] = ..., isPresent: _Optional[bool] = ..., charger: _Optional[_Union[BatteryState.BatteryCharger, str]] = ..., chargeLevel: _Optional[int] = ..., health: _Optional[_Union[BatteryState.BatteryHealth, str]] = ..., status: _Optional[_Union[BatteryState.BatteryStatus, str]] = ...) -> None: ...

class ImageTransport(_message.Message):
    __slots__ = ("channel", "handle")
    class TransportChannel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TRANSPORT_CHANNEL_UNSPECIFIED: _ClassVar[ImageTransport.TransportChannel]
        MMAP: _ClassVar[ImageTransport.TransportChannel]
    TRANSPORT_CHANNEL_UNSPECIFIED: ImageTransport.TransportChannel
    MMAP: ImageTransport.TransportChannel
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    HANDLE_FIELD_NUMBER: _ClassVar[int]
    channel: ImageTransport.TransportChannel
    handle: str
    def __init__(self, channel: _Optional[_Union[ImageTransport.TransportChannel, str]] = ..., handle: _Optional[str] = ...) -> None: ...

class FoldedDisplay(_message.Message):
    __slots__ = ("width", "height", "xOffset", "yOffset")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    XOFFSET_FIELD_NUMBER: _ClassVar[int]
    YOFFSET_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    xOffset: int
    yOffset: int
    def __init__(self, width: _Optional[int] = ..., height: _Optional[int] = ..., xOffset: _Optional[int] = ..., yOffset: _Optional[int] = ...) -> None: ...

class ImageFormat(_message.Message):
    __slots__ = ("format", "rotation", "width", "height", "display", "transport", "foldedDisplay", "displayMode")
    class ImgFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PNG: _ClassVar[ImageFormat.ImgFormat]
        RGBA8888: _ClassVar[ImageFormat.ImgFormat]
        RGB888: _ClassVar[ImageFormat.ImgFormat]
    PNG: ImageFormat.ImgFormat
    RGBA8888: ImageFormat.ImgFormat
    RGB888: ImageFormat.ImgFormat
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_FIELD_NUMBER: _ClassVar[int]
    FOLDEDDISPLAY_FIELD_NUMBER: _ClassVar[int]
    DISPLAYMODE_FIELD_NUMBER: _ClassVar[int]
    format: ImageFormat.ImgFormat
    rotation: Rotation
    width: int
    height: int
    display: int
    transport: ImageTransport
    foldedDisplay: FoldedDisplay
    displayMode: DisplayModeValue
    def __init__(self, format: _Optional[_Union[ImageFormat.ImgFormat, str]] = ..., rotation: _Optional[_Union[Rotation, _Mapping]] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., display: _Optional[int] = ..., transport: _Optional[_Union[ImageTransport, _Mapping]] = ..., foldedDisplay: _Optional[_Union[FoldedDisplay, _Mapping]] = ..., displayMode: _Optional[_Union[DisplayModeValue, str]] = ...) -> None: ...

class Image(_message.Message):
    __slots__ = ("format", "width", "height", "image", "seq", "timestampUs")
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPUS_FIELD_NUMBER: _ClassVar[int]
    format: ImageFormat
    width: int
    height: int
    image: bytes
    seq: int
    timestampUs: int
    def __init__(self, format: _Optional[_Union[ImageFormat, _Mapping]] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., image: _Optional[bytes] = ..., seq: _Optional[int] = ..., timestampUs: _Optional[int] = ...) -> None: ...

class Rotation(_message.Message):
    __slots__ = ("rotation", "xAxis", "yAxis", "zAxis")
    class SkinRotation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PORTRAIT: _ClassVar[Rotation.SkinRotation]
        LANDSCAPE: _ClassVar[Rotation.SkinRotation]
        REVERSE_PORTRAIT: _ClassVar[Rotation.SkinRotation]
        REVERSE_LANDSCAPE: _ClassVar[Rotation.SkinRotation]
    PORTRAIT: Rotation.SkinRotation
    LANDSCAPE: Rotation.SkinRotation
    REVERSE_PORTRAIT: Rotation.SkinRotation
    REVERSE_LANDSCAPE: Rotation.SkinRotation
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    XAXIS_FIELD_NUMBER: _ClassVar[int]
    YAXIS_FIELD_NUMBER: _ClassVar[int]
    ZAXIS_FIELD_NUMBER: _ClassVar[int]
    rotation: Rotation.SkinRotation
    xAxis: float
    yAxis: float
    zAxis: float
    def __init__(self, rotation: _Optional[_Union[Rotation.SkinRotation, str]] = ..., xAxis: _Optional[float] = ..., yAxis: _Optional[float] = ..., zAxis: _Optional[float] = ...) -> None: ...

class PhoneCall(_message.Message):
    __slots__ = ("operation", "number")
    class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        InitCall: _ClassVar[PhoneCall.Operation]
        AcceptCall: _ClassVar[PhoneCall.Operation]
        RejectCallExplicit: _ClassVar[PhoneCall.Operation]
        RejectCallBusy: _ClassVar[PhoneCall.Operation]
        DisconnectCall: _ClassVar[PhoneCall.Operation]
        PlaceCallOnHold: _ClassVar[PhoneCall.Operation]
        TakeCallOffHold: _ClassVar[PhoneCall.Operation]
    InitCall: PhoneCall.Operation
    AcceptCall: PhoneCall.Operation
    RejectCallExplicit: PhoneCall.Operation
    RejectCallBusy: PhoneCall.Operation
    DisconnectCall: PhoneCall.Operation
    PlaceCallOnHold: PhoneCall.Operation
    TakeCallOffHold: PhoneCall.Operation
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    operation: PhoneCall.Operation
    number: str
    def __init__(self, operation: _Optional[_Union[PhoneCall.Operation, str]] = ..., number: _Optional[str] = ...) -> None: ...

class PhoneResponse(_message.Message):
    __slots__ = ("response",)
    class Response(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OK: _ClassVar[PhoneResponse.Response]
        BadOperation: _ClassVar[PhoneResponse.Response]
        BadNumber: _ClassVar[PhoneResponse.Response]
        InvalidAction: _ClassVar[PhoneResponse.Response]
        ActionFailed: _ClassVar[PhoneResponse.Response]
        RadioOff: _ClassVar[PhoneResponse.Response]
    OK: PhoneResponse.Response
    BadOperation: PhoneResponse.Response
    BadNumber: PhoneResponse.Response
    InvalidAction: PhoneResponse.Response
    ActionFailed: PhoneResponse.Response
    RadioOff: PhoneResponse.Response
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: PhoneResponse.Response
    def __init__(self, response: _Optional[_Union[PhoneResponse.Response, str]] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class EntryList(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: _containers.RepeatedCompositeFieldContainer[Entry]
    def __init__(self, entry: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class EmulatorStatus(_message.Message):
    __slots__ = ("version", "uptime", "booted", "vmConfig", "hardwareConfig", "heartbeat", "guestConfig")
    class GuestConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    VERSION_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    BOOTED_FIELD_NUMBER: _ClassVar[int]
    VMCONFIG_FIELD_NUMBER: _ClassVar[int]
    HARDWARECONFIG_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    GUESTCONFIG_FIELD_NUMBER: _ClassVar[int]
    version: str
    uptime: int
    booted: bool
    vmConfig: VmConfiguration
    hardwareConfig: EntryList
    heartbeat: int
    guestConfig: _containers.ScalarMap[str, str]
    def __init__(self, version: _Optional[str] = ..., uptime: _Optional[int] = ..., booted: _Optional[bool] = ..., vmConfig: _Optional[_Union[VmConfiguration, _Mapping]] = ..., hardwareConfig: _Optional[_Union[EntryList, _Mapping]] = ..., heartbeat: _Optional[int] = ..., guestConfig: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AudioFormat(_message.Message):
    __slots__ = ("samplingRate", "channels", "format", "mode")
    class SampleFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        AUD_FMT_U8: _ClassVar[AudioFormat.SampleFormat]
        AUD_FMT_S16: _ClassVar[AudioFormat.SampleFormat]
    AUD_FMT_U8: AudioFormat.SampleFormat
    AUD_FMT_S16: AudioFormat.SampleFormat
    class Channels(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Mono: _ClassVar[AudioFormat.Channels]
        Stereo: _ClassVar[AudioFormat.Channels]
    Mono: AudioFormat.Channels
    Stereo: AudioFormat.Channels
    class DeliveryMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MODE_UNSPECIFIED: _ClassVar[AudioFormat.DeliveryMode]
        MODE_REAL_TIME: _ClassVar[AudioFormat.DeliveryMode]
    MODE_UNSPECIFIED: AudioFormat.DeliveryMode
    MODE_REAL_TIME: AudioFormat.DeliveryMode
    SAMPLINGRATE_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    samplingRate: int
    channels: AudioFormat.Channels
    format: AudioFormat.SampleFormat
    mode: AudioFormat.DeliveryMode
    def __init__(self, samplingRate: _Optional[int] = ..., channels: _Optional[_Union[AudioFormat.Channels, str]] = ..., format: _Optional[_Union[AudioFormat.SampleFormat, str]] = ..., mode: _Optional[_Union[AudioFormat.DeliveryMode, str]] = ...) -> None: ...

class AudioPacket(_message.Message):
    __slots__ = ("format", "timestamp", "audio")
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FIELD_NUMBER: _ClassVar[int]
    format: AudioFormat
    timestamp: int
    audio: bytes
    def __init__(self, format: _Optional[_Union[AudioFormat, _Mapping]] = ..., timestamp: _Optional[int] = ..., audio: _Optional[bytes] = ...) -> None: ...

class SmsMessage(_message.Message):
    __slots__ = ("srcAddress", "text")
    SRCADDRESS_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    srcAddress: str
    text: str
    def __init__(self, srcAddress: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class DisplayConfiguration(_message.Message):
    __slots__ = ("width", "height", "dpi", "flags", "display")
    class DisplayFlags(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DISPLAYFLAGS_UNSPECIFIED: _ClassVar[DisplayConfiguration.DisplayFlags]
        VIRTUAL_DISPLAY_FLAG_PUBLIC: _ClassVar[DisplayConfiguration.DisplayFlags]
        VIRTUAL_DISPLAY_FLAG_PRESENTATION: _ClassVar[DisplayConfiguration.DisplayFlags]
        VIRTUAL_DISPLAY_FLAG_SECURE: _ClassVar[DisplayConfiguration.DisplayFlags]
        VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY: _ClassVar[DisplayConfiguration.DisplayFlags]
        VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR: _ClassVar[DisplayConfiguration.DisplayFlags]
    DISPLAYFLAGS_UNSPECIFIED: DisplayConfiguration.DisplayFlags
    VIRTUAL_DISPLAY_FLAG_PUBLIC: DisplayConfiguration.DisplayFlags
    VIRTUAL_DISPLAY_FLAG_PRESENTATION: DisplayConfiguration.DisplayFlags
    VIRTUAL_DISPLAY_FLAG_SECURE: DisplayConfiguration.DisplayFlags
    VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY: DisplayConfiguration.DisplayFlags
    VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR: DisplayConfiguration.DisplayFlags
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DPI_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    dpi: int
    flags: int
    display: int
    def __init__(self, width: _Optional[int] = ..., height: _Optional[int] = ..., dpi: _Optional[int] = ..., flags: _Optional[int] = ..., display: _Optional[int] = ...) -> None: ...

class DisplayConfigurations(_message.Message):
    __slots__ = ("displays", "userConfigurable", "maxDisplays")
    DISPLAYS_FIELD_NUMBER: _ClassVar[int]
    USERCONFIGURABLE_FIELD_NUMBER: _ClassVar[int]
    MAXDISPLAYS_FIELD_NUMBER: _ClassVar[int]
    displays: _containers.RepeatedCompositeFieldContainer[DisplayConfiguration]
    userConfigurable: int
    maxDisplays: int
    def __init__(self, displays: _Optional[_Iterable[_Union[DisplayConfiguration, _Mapping]]] = ..., userConfigurable: _Optional[int] = ..., maxDisplays: _Optional[int] = ...) -> None: ...

class Notification(_message.Message):
    __slots__ = ("cameraNotification", "displayConfigurationsChangedNotification", "posture", "booted", "brightness", "textViewFocus", "xrOptions")
    CAMERANOTIFICATION_FIELD_NUMBER: _ClassVar[int]
    DISPLAYCONFIGURATIONSCHANGEDNOTIFICATION_FIELD_NUMBER: _ClassVar[int]
    POSTURE_FIELD_NUMBER: _ClassVar[int]
    BOOTED_FIELD_NUMBER: _ClassVar[int]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    TEXTVIEWFOCUS_FIELD_NUMBER: _ClassVar[int]
    XROPTIONS_FIELD_NUMBER: _ClassVar[int]
    cameraNotification: CameraNotification
    displayConfigurationsChangedNotification: DisplayConfigurationsChangedNotification
    posture: Posture
    booted: BootCompletedNotification
    brightness: BrightnessValue
    textViewFocus: TextViewFocus
    xrOptions: XrOptions
    def __init__(self, cameraNotification: _Optional[_Union[CameraNotification, _Mapping]] = ..., displayConfigurationsChangedNotification: _Optional[_Union[DisplayConfigurationsChangedNotification, _Mapping]] = ..., posture: _Optional[_Union[Posture, _Mapping]] = ..., booted: _Optional[_Union[BootCompletedNotification, _Mapping]] = ..., brightness: _Optional[_Union[BrightnessValue, _Mapping]] = ..., textViewFocus: _Optional[_Union[TextViewFocus, _Mapping]] = ..., xrOptions: _Optional[_Union[XrOptions, _Mapping]] = ...) -> None: ...

class BootCompletedNotification(_message.Message):
    __slots__ = ("time",)
    TIME_FIELD_NUMBER: _ClassVar[int]
    time: int
    def __init__(self, time: _Optional[int] = ...) -> None: ...

class CameraNotification(_message.Message):
    __slots__ = ("active", "display")
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    active: bool
    display: int
    def __init__(self, active: _Optional[bool] = ..., display: _Optional[int] = ...) -> None: ...

class TextViewFocus(_message.Message):
    __slots__ = ("textViewHasFocus", "display")
    TEXTVIEWHASFOCUS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_FIELD_NUMBER: _ClassVar[int]
    textViewHasFocus: bool
    display: int
    def __init__(self, textViewHasFocus: _Optional[bool] = ..., display: _Optional[int] = ...) -> None: ...

class DisplayConfigurationsChangedNotification(_message.Message):
    __slots__ = ("displayConfigurations",)
    DISPLAYCONFIGURATIONS_FIELD_NUMBER: _ClassVar[int]
    displayConfigurations: DisplayConfigurations
    def __init__(self, displayConfigurations: _Optional[_Union[DisplayConfigurations, _Mapping]] = ...) -> None: ...

class RotationRadian(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Translation(_message.Message):
    __slots__ = ("delta_x", "delta_y", "delta_z")
    DELTA_X_FIELD_NUMBER: _ClassVar[int]
    DELTA_Y_FIELD_NUMBER: _ClassVar[int]
    DELTA_Z_FIELD_NUMBER: _ClassVar[int]
    delta_x: float
    delta_y: float
    delta_z: float
    def __init__(self, delta_x: _Optional[float] = ..., delta_y: _Optional[float] = ..., delta_z: _Optional[float] = ...) -> None: ...

class AngularVelocity(_message.Message):
    __slots__ = ("omega_x", "omega_y", "omega_z")
    OMEGA_X_FIELD_NUMBER: _ClassVar[int]
    OMEGA_Y_FIELD_NUMBER: _ClassVar[int]
    OMEGA_Z_FIELD_NUMBER: _ClassVar[int]
    omega_x: float
    omega_y: float
    omega_z: float
    def __init__(self, omega_x: _Optional[float] = ..., omega_y: _Optional[float] = ..., omega_z: _Optional[float] = ...) -> None: ...

class Velocity(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Posture(_message.Message):
    __slots__ = ("value",)
    class PostureValue(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        POSTURE_UNKNOWN: _ClassVar[Posture.PostureValue]
        POSTURE_CLOSED: _ClassVar[Posture.PostureValue]
        POSTURE_HALF_OPENED: _ClassVar[Posture.PostureValue]
        POSTURE_OPENED: _ClassVar[Posture.PostureValue]
        POSTURE_FLIPPED: _ClassVar[Posture.PostureValue]
        POSTURE_TENT: _ClassVar[Posture.PostureValue]
        POSTURE_MAX: _ClassVar[Posture.PostureValue]
    POSTURE_UNKNOWN: Posture.PostureValue
    POSTURE_CLOSED: Posture.PostureValue
    POSTURE_HALF_OPENED: Posture.PostureValue
    POSTURE_OPENED: Posture.PostureValue
    POSTURE_FLIPPED: Posture.PostureValue
    POSTURE_TENT: Posture.PostureValue
    POSTURE_MAX: Posture.PostureValue
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: Posture.PostureValue
    def __init__(self, value: _Optional[_Union[Posture.PostureValue, str]] = ...) -> None: ...

class PhoneNumber(_message.Message):
    __slots__ = ("number",)
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    number: str
    def __init__(self, number: _Optional[str] = ...) -> None: ...
