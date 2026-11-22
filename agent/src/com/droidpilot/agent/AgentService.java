package com.droidpilot.agent;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.app.ActivityManager;
import android.app.KeyguardManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Path;
import android.graphics.Point;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Map;
import java.util.TreeMap;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/**
 * The on-phone half of droidpilot's wireless backend. Runs as an accessibility
 * service, so Android restarts it by itself after a reboot (no adb, no USB), and
 * serves the screen tree, screenshots and input over HTTP on PORT.
 */
public class AgentService extends AccessibilityService {
    static final String TAG = HttpServer.TAG;
    static final int PORT = 8790;
    static final String VERSION = "0.2";

    // Labels of the system screen-capture dialog (English, Chinese, Japanese).
    private static final String[] START_LABELS = {"start now", "立即开始", "立即開始", "今すぐ開始"};
    private static final String[] DONT_ASK_LABELS = {"don't show again", "不再显示", "不再顯示", "今後は表示しない"};

    private final Handler main = new Handler(Looper.getMainLooper());
    private HttpServer server;
    private String token;
    private volatile String lastPackage = "", lastActivity = "";
    private PowerManager.WakeLock wakeLock;
    private final Map<Integer, PortForward> forwards = new TreeMap<>();

    // -- lifecycle --------------------------------------------------------------

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        token = loadToken();
        server = new HttpServer(PORT, this::route);
        server.start();
        restoreForwards();
        // Ask for screen capture once the system has settled after boot.
        main.postDelayed(() -> { if (!Capture.ready()) Capture.request(this); }, 5000);
        Log.i(TAG, "agent " + VERSION + " connected");
    }

    @Override
    public boolean onUnbind(Intent intent) {
        shutdown();
        return super.onUnbind(intent);
    }

    @Override
    public void onDestroy() {
        shutdown();
        super.onDestroy();
    }

    private void shutdown() {
        if (server != null) { server.stop(); server = null; }
        synchronized (forwards) {
            for (PortForward f : forwards.values()) f.close();
            forwards.clear();
        }
        Capture.stop();
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
    }

    @Override
    public void onInterrupt() {}

    @Override
    public void onAccessibilityEvent(AccessibilityEvent e) {
        if (e.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence pkg = e.getPackageName(), cls = e.getClassName();
        if (pkg == null) return;
        if ("com.android.systemui".contentEquals(pkg)) {
            maybeAcceptCapture();
            return;
        }
        // Our own invisible capture-permission activity is not what the user is looking at.
        if (cls != null && !getPackageName().contentEquals(pkg) && isActivity(pkg.toString(), cls.toString())) {
            lastPackage = pkg.toString();
            lastActivity = cls.toString();
        }
    }

    private boolean isActivity(String pkg, String cls) {
        try {
            getPackageManager().getActivityInfo(new ComponentName(pkg, cls), 0);
            return true;
        } catch (PackageManager.NameNotFoundException ex) {
            return false;
        }
    }

    /** Clicks through the system's screen-capture dialog, but only right after we asked for it. */
    private void maybeAcceptCapture() {
        if (System.currentTimeMillis() - Capture.requestedAt > 20000) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;
        AccessibilityNodeInfo dontAsk = findByLabel(root, DONT_ASK_LABELS);
        if (dontAsk != null && dontAsk.isCheckable() && !dontAsk.isChecked()) {
            dontAsk.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        }
        AccessibilityNodeInfo start = findByLabel(root, START_LABELS);
        if (start != null) {
            main.postDelayed(() -> start.performAction(AccessibilityNodeInfo.ACTION_CLICK), 300);
            Capture.requestedAt = 0;
        }
    }

    private static AccessibilityNodeInfo findByLabel(AccessibilityNodeInfo n, String[] labels) {
        CharSequence t = n.getText();
        if (t != null) {
            String s = t.toString().trim().toLowerCase(Locale.ROOT);
            for (String l : labels) if (s.equals(l)) return n;
        }
        for (int i = 0; i < n.getChildCount(); i++) {
            AccessibilityNodeInfo c = n.getChild(i);
            if (c == null) continue;
            AccessibilityNodeInfo hit = findByLabel(c, labels);
            if (hit != null) return hit;
        }
        return null;
    }

    // -- auth -------------------------------------------------------------------

    private String loadToken() {
        SharedPreferences prefs = getSharedPreferences("agent", Context.MODE_PRIVATE);
        String t = prefs.getString("token", null);
        if (t == null) {
            byte[] b = new byte[24];
            new SecureRandom().nextBytes(b);
            StringBuilder sb = new StringBuilder();
            for (byte x : b) sb.append(String.format("%02x", x & 0xff));
            t = sb.toString();
            prefs.edit().putString("token", t).apply();
        }
        return t;
    }

    private boolean authorized(HttpServer.Request req) {
        String given = req.headers.get("x-token");
        if (given == null) return false;
        return MessageDigest.isEqual(given.getBytes(StandardCharsets.UTF_8), token.getBytes(StandardCharsets.UTF_8));
    }

    // -- port forwards ------------------------------------------------------------

    /**
     * {} lists; {"listen": 8023, "target": 8022} adds (saved, restored after reboot);
     * {"listen": 8023, "remove": true} removes. See PortForward for what it is for.
     */
    private HttpServer.Response forwardsRoute(JSONObject body) throws Exception {
        if (body.has("listen")) {
            int listen = body.getInt("listen");
            if (listen < 1024 || listen > 65535 || listen == PORT) throw new IllegalArgumentException("bad listen port");
            synchronized (forwards) {
                PortForward old = forwards.remove(listen);
                if (old != null) old.close();
                if (!body.optBoolean("remove")) {
                    int target = body.getInt("target");
                    if (target < 1 || target > 65535) throw new IllegalArgumentException("bad target port");
                    forwards.put(listen, new PortForward(listen, target));
                }
                saveForwards();
            }
        }
        JSONArray list = new JSONArray();
        synchronized (forwards) {
            for (PortForward f : forwards.values()) list.put(new JSONObject().put("listen", f.listen).put("target", f.target));
        }
        return ok(new JSONObject().put("forwards", list));
    }

    private void saveForwards() {
        StringBuilder sb = new StringBuilder();
        for (PortForward f : forwards.values()) sb.append(sb.length() > 0 ? "," : "").append(f.listen).append(':').append(f.target);
        getSharedPreferences("agent", Context.MODE_PRIVATE).edit().putString("forwards", sb.toString()).apply();
    }

    private void restoreForwards() {
        String saved = getSharedPreferences("agent", Context.MODE_PRIVATE).getString("forwards", "");
        for (String item : saved.split(",")) {
            if (item.isEmpty()) continue;
            String[] lt = item.split(":");
            int listen = Integer.parseInt(lt[0]), target = Integer.parseInt(lt[1]);
            // The port can still be held by the previous instance for a moment; retry in the background.
            new Thread(() -> {
                for (int i = 0; i < 30; i++) {
                    try {
                        PortForward f = new PortForward(listen, target);
                        synchronized (forwards) {
                            if (server == null) { f.close(); return; }
                            forwards.put(listen, f);
                        }
                        return;
                    } catch (java.io.IOException e) {
                        try { Thread.sleep(2000); } catch (InterruptedException ie) { return; }
                    }
                }
                Log.w(TAG, "forward " + listen + " could not bind");
            }, "restore-forward").start();
        }
    }

    // -- routing ----------------------------------------------------------------

    private HttpServer.Response route(HttpServer.Request req) throws Exception {
        String p = req.path;
        if (p.equals("/ping")) {
            return ok(new JSONObject().put("agent", VERSION));
        }
        if (p.equals("/token")) {
            // Only processes on the phone itself (adb shell, Termux) may read the token.
            if (!req.remote.isLoopbackAddress()) return HttpServer.Response.json(403, "{\"error\":\"loopback only\"}");
            return ok(new JSONObject().put("token", token));
        }
        if (!authorized(req)) return HttpServer.Response.json(401, "{\"error\":\"bad or missing X-Token\"}");
        JSONObject body = req.body.length > 0 ? new JSONObject(req.bodyText()) : new JSONObject();
        switch (p) {
            case "/info": return ok(info());
            case "/dump": return HttpServer.Response.bytes("text/xml; charset=utf-8",
                    onMain(this::dump).getBytes(StandardCharsets.UTF_8));
            case "/screenshot": return screenshot(Integer.parseInt(req.param("width", "0")),
                    Integer.parseInt(req.param("quality", "80")));
            case "/tap": return gesture(stroke(body.getInt("x"), body.getInt("y"), body.getInt("x"), body.getInt("y"), 0, 60));
            case "/long_press": return gesture(stroke(body.getInt("x"), body.getInt("y"), body.getInt("x"), body.getInt("y"),
                    0, body.optInt("hold_ms", 800)));
            case "/swipe": return swipe(body);
            case "/pinch": return pinch(body);
            case "/key": return key(body.getString("key"));
            case "/set_text": return setText(body.getString("text"), body.optBoolean("clear"), body.optString("hint", null));
            case "/wake": wake(); return ok(new JSONObject());
            case "/launch": return launch(body.getString("package"));
            case "/stop": return stopApp(body.getString("package"));
            case "/current": return ok(new JSONObject().put("package", currentPackage()).put("activity", lastActivity));
            case "/apps": return apps();
            case "/rotate": return rotate(body.getInt("rotation"));
            case "/capture": Capture.request(this); return ok(new JSONObject().put("requested", true));
            case "/nettest": return ok(NetTest.run(body));
            case "/forwards": return forwardsRoute(body);
            default: return HttpServer.Response.json(404, "{\"error\":\"no such endpoint\"}");
        }
    }

    private static HttpServer.Response ok(JSONObject o) throws Exception {
        o.put("ok", true);
        return HttpServer.Response.json(200, o.toString());
    }

    /** Accessibility node APIs are not thread safe; run tree work on the main thread. */
    private <T> T onMain(Callable<T> fn) throws Exception {
        AtomicReference<T> result = new AtomicReference<>();
        AtomicReference<Exception> error = new AtomicReference<>();
        CountDownLatch done = new CountDownLatch(1);
        main.post(() -> {
            try { result.set(fn.call()); } catch (Exception e) { error.set(e); }
            done.countDown();
        });
        if (!done.await(10, TimeUnit.SECONDS)) throw new IllegalStateException("main thread busy");
        if (error.get() != null) throw error.get();
        return result.get();
    }

    // -- observation --------------------------------------------------------------

    private int rotation() {
        return ((WindowManager) getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRotation();
    }

    private JSONObject info() throws Exception {
        Point size = new Point();
        ((WindowManager) getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRealSize(size);
        PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
        KeyguardManager km = (KeyguardManager) getSystemService(KEYGUARD_SERVICE);
        return new JSONObject()
                .put("agent", VERSION)
                .put("sdk", Build.VERSION.SDK_INT)
                .put("model", Build.MODEL)
                .put("width", size.x).put("height", size.y)
                .put("rotation", rotation())
                .put("screen_on", pm.isInteractive())
                .put("locked", km.isKeyguardLocked())
                .put("secure_lock", km.isKeyguardSecure())
                .put("capture", Capture.ready());
    }

    private String dump() {
        List<AccessibilityWindowInfo> windows = getWindows();
        AccessibilityNodeInfo root = getRootInActiveWindow();
        String xml = TreeDumper.dump(windows, root, rotation());
        if (windows != null) for (AccessibilityWindowInfo w : windows) w.recycle();
        return xml;
    }

    private HttpServer.Response screenshot(int width, int quality) throws Exception {
        if (!Capture.ready()) {
            Capture.request(this);
            return HttpServer.Response.json(503, "{\"error\":\"screen capture not granted yet; asked for it, retry in a few seconds\"}");
        }
        byte[] jpg = Capture.jpeg(this, width, Math.max(10, Math.min(100, quality)));
        if (jpg == null) return HttpServer.Response.json(503, "{\"error\":\"no frame yet\"}");
        return HttpServer.Response.bytes("image/jpeg", jpg);
    }

    private String currentPackage() {
        if (!lastPackage.isEmpty()) return lastPackage;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        return root != null && root.getPackageName() != null ? root.getPackageName().toString() : "";
    }

    // -- gestures -----------------------------------------------------------------

    private static GestureDescription.StrokeDescription stroke(float x1, float y1, float x2, float y2, long start, long dur) {
        Path path = new Path();
        path.moveTo(x1, y1);
        if (x1 != x2 || y1 != y2) path.lineTo(x2, y2);
        return new GestureDescription.StrokeDescription(path, start, Math.max(1, dur));
    }

    /** Dispatches a gesture made of `strokes` and waits until it has finished. */
    private boolean dispatch(GestureDescription.StrokeDescription... strokes) throws InterruptedException {
        GestureDescription.Builder b = new GestureDescription.Builder();
        long longest = 0;
        for (GestureDescription.StrokeDescription s : strokes) {
            b.addStroke(s);
            longest = Math.max(longest, s.getStartTime() + s.getDuration());
        }
        GestureDescription g = b.build();
        GestureWaiter waiter = new GestureWaiter();
        main.post(() -> {
            if (!dispatchGesture(g, waiter, main)) waiter.done.countDown();
        });
        waiter.done.await(longest + 5000, TimeUnit.MILLISECONDS);
        return waiter.completed.get();
    }

    // A named class: d8 8.2 crashes (NPE) on an anonymous subclass of GestureResultCallback.
    private static final class GestureWaiter extends AccessibilityService.GestureResultCallback {
        final CountDownLatch done = new CountDownLatch(1);
        final AtomicBoolean completed = new AtomicBoolean();

        @Override public void onCompleted(GestureDescription d) { completed.set(true); done.countDown(); }
        @Override public void onCancelled(GestureDescription d) { done.countDown(); }
    }

    private HttpServer.Response gesture(GestureDescription.StrokeDescription s) throws Exception {
        if (!dispatch(s)) return HttpServer.Response.json(409, "{\"error\":\"gesture was cancelled\"}");
        return ok(new JSONObject());
    }

    /** A drag with optional pauses: hold_ms at the start (press-and-drag), end_hold_ms before lifting. */
    private HttpServer.Response swipe(JSONObject b) throws Exception {
        int x1 = b.getInt("x1"), y1 = b.getInt("y1"), x2 = b.getInt("x2"), y2 = b.getInt("y2");
        long dur = b.optLong("duration_ms", 300), hold = b.optLong("hold_ms", 0), endHold = b.optLong("end_hold_ms", 0);
        if (Build.VERSION.SDK_INT < 26 || (hold == 0 && endHold == 0)) {
            return gesture(stroke(x1, y1, x2, y2, 0, dur));
        }
        // Android 8+: chain strokes that keep the finger down between them.
        List<GestureDescription.StrokeDescription> parts = new ArrayList<>();
        GestureDescription.StrokeDescription prev = null;
        if (hold > 0) {
            prev = continued(null, x1, y1, x1, y1, hold, true);
            parts.add(prev);
        }
        prev = continued(prev, x1, y1, x2, y2, dur, endHold > 0);
        parts.add(prev);
        if (endHold > 0) parts.add(continued(prev, x2, y2, x2, y2, endHold, false));
        for (GestureDescription.StrokeDescription s : parts) {
            if (!dispatch(s)) return HttpServer.Response.json(409, "{\"error\":\"gesture was cancelled\"}");
        }
        return ok(new JSONObject());
    }

    private static GestureDescription.StrokeDescription continued(GestureDescription.StrokeDescription prev,
            float x1, float y1, float x2, float y2, long dur, boolean willContinue) {
        Path path = new Path();
        path.moveTo(x1, y1);
        if (x1 != x2 || y1 != y2) path.lineTo(x2, y2);
        dur = Math.max(1, dur);
        return prev == null ? new GestureDescription.StrokeDescription(path, 0, dur, willContinue)
                : prev.continueStroke(path, 0, dur, willContinue);
    }

    private HttpServer.Response pinch(JSONObject b) throws Exception {
        int cx = b.getInt("cx"), cy = b.getInt("cy"), from = b.getInt("start"), to = b.getInt("end");
        long dur = b.optLong("duration_ms", 400);
        return dispatch(stroke(cx - from / 2f, cy, cx - to / 2f, cy, 0, dur), stroke(cx + from / 2f, cy, cx + to / 2f, cy, 0, dur))
                ? ok(new JSONObject()) : HttpServer.Response.json(409, "{\"error\":\"gesture was cancelled\"}");
    }

    // -- keys and text ------------------------------------------------------------

    private HttpServer.Response key(String key) throws Exception {
        String k = key.trim().toLowerCase(Locale.ROOT);
        if (k.startsWith("keycode_")) k = k.substring(8);
        int action;
        switch (k) {
            case "3": case "home": action = GLOBAL_ACTION_HOME; break;
            case "4": case "back": action = GLOBAL_ACTION_BACK; break;
            case "187": case "app_switch": case "recents": case "recent": action = GLOBAL_ACTION_RECENTS; break;
            case "83": case "notification": case "notifications": action = GLOBAL_ACTION_NOTIFICATIONS; break;
            case "quick_settings": action = GLOBAL_ACTION_QUICK_SETTINGS; break;
            case "power_dialog": action = GLOBAL_ACTION_POWER_DIALOG; break;
            case "223": case "sleep": case "lock":
                if (Build.VERSION.SDK_INT < 28) throw new IllegalArgumentException("locking needs Android 9");
                action = GLOBAL_ACTION_LOCK_SCREEN; break;
            case "224": case "wakeup": case "wake": wake(); return ok(new JSONObject());
            case "26": case "power":
                if (((PowerManager) getSystemService(POWER_SERVICE)).isInteractive() && Build.VERSION.SDK_INT >= 28) {
                    action = GLOBAL_ACTION_LOCK_SCREEN;
                    break;
                }
                wake();
                return ok(new JSONObject());
            case "67": case "del": case "delete": case "backspace": return deleteChar();
            default:
                throw new IllegalArgumentException("key '" + key + "' is not available without adb "
                        + "(supported: home, back, recents, notifications, quick_settings, power, wakeup, sleep, delete)");
        }
        boolean done = onMain(() -> performGlobalAction(action));
        return done ? ok(new JSONObject()) : HttpServer.Response.json(409, "{\"error\":\"action refused\"}");
    }

    private AccessibilityNodeInfo focusedInput() {
        AccessibilityNodeInfo f = findFocus(AccessibilityNodeInfo.FOCUS_INPUT);
        if (f != null) return f;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        return root != null ? root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT) : null;
    }

    private HttpServer.Response setText(String text, boolean clear, String hint) throws Exception {
        JSONObject r = onMain(() -> {
            AccessibilityNodeInfo f = focusedInput();
            if (f == null) return null;
            f.refresh();
            String current = f.getText() != null ? f.getText().toString() : "";
            boolean showingHint = Build.VERSION.SDK_INT >= 26 && f.isShowingHintText();
            if (clear || showingHint || (hint != null && current.equals(hint))) current = "";
            Bundle args = new Bundle();
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, current + text);
            boolean done = f.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
            return new JSONObject().put("set", done);
        });
        if (r == null) return HttpServer.Response.json(409, "{\"error\":\"no focused text field; tap the field first\"}");
        return ok(r);
    }

    private HttpServer.Response deleteChar() throws Exception {
        Boolean done = onMain(() -> {
            AccessibilityNodeInfo f = focusedInput();
            if (f == null) return null;
            f.refresh();
            boolean showingHint = Build.VERSION.SDK_INT >= 26 && f.isShowingHintText();
            String current = f.getText() != null && !showingHint ? f.getText().toString() : "";
            if (current.isEmpty()) return true;
            int cut = current.offsetByCodePoints(current.length(), -1);
            Bundle args = new Bundle();
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, current.substring(0, cut));
            return f.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
        });
        if (done == null) return HttpServer.Response.json(409, "{\"error\":\"no focused text field\"}");
        return ok(new JSONObject());
    }

    @SuppressWarnings("deprecation")
    private void wake() throws InterruptedException {
        PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
        if (!pm.isInteractive()) {
            if (wakeLock == null) {
                wakeLock = pm.newWakeLock(PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP
                        | PowerManager.ON_AFTER_RELEASE, "droidpilot:wake");
            }
            wakeLock.acquire(5000);
            Thread.sleep(600);
        }
        // A swipe-only lock screen goes away with a swipe up; a PIN lock cannot be passed (and is not tried).
        KeyguardManager km = (KeyguardManager) getSystemService(KEYGUARD_SERVICE);
        if (km.isKeyguardLocked() && !km.isKeyguardSecure()) {
            Point size = new Point();
            ((WindowManager) getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRealSize(size);
            dispatch(stroke(size.x / 2f, size.y * 0.85f, size.x / 2f, size.y * 0.25f, 0, 250));
            Thread.sleep(400);
        }
    }

    // -- apps and settings ----------------------------------------------------------

    private HttpServer.Response launch(String pkg) throws Exception {
        Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
        if (i == null) throw new IllegalArgumentException("no launchable app " + pkg);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        startActivity(i);
        return ok(new JSONObject());
    }

    /** Without adb there is no force-stop: go home and let Android kill the now-background app. */
    private HttpServer.Response stopApp(String pkg) throws Exception {
        if (pkg.equals(currentPackage())) {
            onMain(() -> performGlobalAction(GLOBAL_ACTION_HOME));
            Thread.sleep(500);
        }
        ((ActivityManager) getSystemService(ACTIVITY_SERVICE)).killBackgroundProcesses(pkg);
        return ok(new JSONObject());
    }

    private HttpServer.Response apps() throws Exception {
        JSONArray out = new JSONArray();
        for (ApplicationInfo a : getPackageManager().getInstalledApplications(0)) out.put(a.packageName);
        return ok(new JSONObject().put("packages", out));
    }

    private HttpServer.Response rotate(int rotation) throws Exception {
        if (!Settings.System.canWrite(this)) {
            throw new IllegalArgumentException("rotation needs the 'modify system settings' grant "
                    + "(adb shell appops set com.droidpilot.agent WRITE_SETTINGS allow)");
        }
        Settings.System.putInt(getContentResolver(), Settings.System.ACCELEROMETER_ROTATION, 0);
        Settings.System.putInt(getContentResolver(), Settings.System.USER_ROTATION, rotation & 3);
        return ok(new JSONObject());
    }
}
