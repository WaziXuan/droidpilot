package com.droidpilot.agent;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.graphics.Point;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.DisplayMetrics;
import android.view.Display;
import android.view.WindowManager;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;

/**
 * Screen frames via MediaProjection (Android 9 has no accessibility screenshot API).
 * The projection is granted once through ProjectionActivity; the newest frame is
 * kept so a screenshot of a still screen still has something to return.
 */
final class Capture {
    private static final Object LOCK = new Object();
    private static MediaProjection projection;
    private static VirtualDisplay display;
    private static ImageReader reader;
    private static Image latest;
    private static int width, height;
    private static HandlerThread thread;
    private static Handler handler;
    static volatile long requestedAt;  // when the agent last asked for the permission dialog

    private Capture() {}

    static boolean ready() {
        synchronized (LOCK) { return projection != null; }
    }

    /** Ask for the capture permission (the service clicks through the system dialog). */
    static void request(Context ctx) {
        requestedAt = System.currentTimeMillis();
        Intent i = new Intent(ctx, ProjectionActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        ctx.startActivity(i);
    }

    static void start(Context ctx, int resultCode, Intent data) {
        MediaProjectionManager mpm = (MediaProjectionManager) ctx.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        MediaProjection p = mpm.getMediaProjection(resultCode, data);
        if (p == null) return;
        synchronized (LOCK) {
            stopLocked();
            if (thread == null) {
                thread = new HandlerThread("capture");
                thread.start();
                handler = new Handler(thread.getLooper());
            }
            projection = p;
            projection.registerCallback(new MediaProjection.Callback() {
                @Override public void onStop() {
                    synchronized (LOCK) {
                        if (projection != null) { projection = null; releaseDisplayLocked(); }
                    }
                }
            }, handler);
            ensureDisplayLocked(ctx);
        }
    }

    static void stop() {
        synchronized (LOCK) { stopLocked(); }
    }

    private static void stopLocked() {
        releaseDisplayLocked();
        if (projection != null) {
            MediaProjection p = projection;
            projection = null;
            p.stop();
        }
    }

    private static void releaseDisplayLocked() {
        if (latest != null) { latest.close(); latest = null; }
        if (display != null) { display.release(); display = null; }
        if (reader != null) { reader.close(); reader = null; }
        width = height = 0;
    }

    /** (Re)creates the virtual display when the screen size changed, e.g. after a rotation. */
    private static void ensureDisplayLocked(Context ctx) {
        WindowManager wm = (WindowManager) ctx.getSystemService(Context.WINDOW_SERVICE);
        Display d = wm.getDefaultDisplay();
        Point size = new Point();
        d.getRealSize(size);
        if (display != null && size.x == width && size.y == height) return;
        releaseDisplayLocked();
        DisplayMetrics dm = new DisplayMetrics();
        d.getRealMetrics(dm);
        width = size.x;
        height = size.y;
        reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 3);
        reader.setOnImageAvailableListener(r -> {
            synchronized (LOCK) {
                Image img;
                try { img = r.acquireLatestImage(); } catch (IllegalStateException e) { return; }
                if (img == null) return;
                if (latest != null) latest.close();
                latest = img;
            }
        }, handler);
        display = projection.createVirtualDisplay("droidpilot", width, height, dm.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, reader.getSurface(), null, handler);
    }

    /** JPEG of the newest frame, scaled to `targetWidth` (0 = full size); null if not granted yet. */
    static byte[] jpeg(Context ctx, int targetWidth, int quality) throws InterruptedException {
        Bitmap bmp;
        synchronized (LOCK) {
            if (projection == null) return null;
            ensureDisplayLocked(ctx);
        }
        // A freshly created display needs a moment for its first frame.
        long deadline = System.currentTimeMillis() + 1500;
        while (true) {
            synchronized (LOCK) {
                if (latest != null) { bmp = toBitmap(latest); break; }
            }
            if (System.currentTimeMillis() > deadline) return null;
            Thread.sleep(30);
        }
        if (targetWidth > 0 && targetWidth < bmp.getWidth()) {
            int h = Math.round(bmp.getHeight() * (float) targetWidth / bmp.getWidth());
            Bitmap scaled = Bitmap.createScaledBitmap(bmp, targetWidth, h, true);
            bmp.recycle();
            bmp = scaled;
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG, quality, out);
        bmp.recycle();
        return out.toByteArray();
    }

    private static Bitmap toBitmap(Image img) {
        Image.Plane plane = img.getPlanes()[0];
        ByteBuffer buf = plane.getBuffer();
        int pixelStride = plane.getPixelStride();
        int rowStride = plane.getRowStride();
        int w = img.getWidth(), h = img.getHeight();
        int padded = rowStride / pixelStride;
        Bitmap full = Bitmap.createBitmap(padded, h, Bitmap.Config.ARGB_8888);
        buf.rewind();
        full.copyPixelsFromBuffer(buf);
        if (padded == w) return full;
        Bitmap cropped = Bitmap.createBitmap(full, 0, 0, w, h);
        full.recycle();
        return cropped;
    }
}
