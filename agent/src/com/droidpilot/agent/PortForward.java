package com.droidpilot.agent;

import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Forwards a TCP port on the phone's Tailscale address to a port on 127.0.0.1.
 *
 * Why: an app excluded from the VPN (Tailscale's split tunneling, e.g. Termux so that it keeps
 * using the home connection) cannot answer connections that arrive over the tailnet. This app
 * is still inside the VPN, and loopback never goes through it, so it can relay for that app.
 * Only connections addressed to a Tailscale address (100.64.0.0/10, fd7a:115c:a1e0::/48) are
 * accepted; the same port on Wi-Fi or mobile data is refused.
 */
final class PortForward {
    private static final String TAG = "droidpilot";

    final int listen, target;
    private final ServerSocket server;
    private final ExecutorService pool = Executors.newCachedThreadPool();
    private volatile boolean closed;

    PortForward(int listen, int target) throws IOException {
        this.listen = listen;
        this.target = target;
        server = new ServerSocket();
        server.setReuseAddress(true);
        server.bind(new InetSocketAddress(listen));
        Thread t = new Thread(this::acceptLoop, "forward-" + listen);
        t.setDaemon(true);
        t.start();
    }

    static boolean isTailnet(InetAddress a) {
        byte[] b = a.getAddress();
        if (a instanceof Inet4Address) return (b[0] & 0xff) == 100 && (b[1] & 0xc0) == 64;
        if (a instanceof Inet6Address) {
            if (((Inet6Address) a).isIPv4CompatibleAddress()) return false;
            // IPv4-mapped (::ffff:100.x.y.z) when the socket is dual-stack
            boolean mapped = true;
            for (int i = 0; i < 10; i++) if (b[i] != 0) { mapped = false; break; }
            if (mapped && (b[10] & 0xff) == 0xff && (b[11] & 0xff) == 0xff) {
                return (b[12] & 0xff) == 100 && (b[13] & 0xc0) == 64;
            }
            return (b[0] & 0xff) == 0xfd && (b[1] & 0xff) == 0x7a && (b[2] & 0xff) == 0x11
                && (b[3] & 0xff) == 0x5c && (b[4] & 0xff) == 0xa1 && (b[5] & 0xff) == 0xe0;
        }
        return false;
    }

    private void acceptLoop() {
        while (!closed) {
            Socket in;
            try {
                in = server.accept();
            } catch (IOException e) {
                if (!closed) Log.w(TAG, "forward " + listen + " accept: " + e);
                continue;
            }
            if (!isTailnet(in.getLocalAddress())) {
                closeQuietly(in);
                continue;
            }
            pool.execute(() -> handle(in));
        }
    }

    private void handle(Socket in) {
        Socket out = new Socket();
        try {
            out.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), target), 5000);
            in.setTcpNoDelay(true);
            out.setTcpNoDelay(true);
            pool.execute(() -> pump(out, in));
            pump(in, out);
        } catch (IOException e) {
            closeQuietly(in);
            closeQuietly(out);
        }
    }

    /** Copies src to dst; on EOF half-closes dst, on error closes both. */
    private static void pump(Socket src, Socket dst) {
        byte[] buf = new byte[32 * 1024];
        try {
            InputStream is = src.getInputStream();
            OutputStream os = dst.getOutputStream();
            int n;
            while ((n = is.read(buf)) >= 0) os.write(buf, 0, n);
            dst.shutdownOutput();
            if (src.isOutputShutdown()) { closeQuietly(src); closeQuietly(dst); }
        } catch (IOException e) {
            closeQuietly(src);
            closeQuietly(dst);
        }
    }

    void close() {
        closed = true;
        closeQuietly(server);
        pool.shutdownNow();
    }

    private static void closeQuietly(java.io.Closeable c) {
        try { c.close(); } catch (IOException ignored) {}
    }
}
