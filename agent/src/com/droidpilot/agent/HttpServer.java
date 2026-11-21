package com.droidpilot.agent;

import android.util.Log;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Tiny HTTP/1.0-style server: one request per connection, enough for a single controlling client. */
final class HttpServer {
    static final String TAG = "droidpilot";

    static final class Request {
        String method, path;
        final Map<String, String> query = new HashMap<>();
        final Map<String, String> headers = new HashMap<>();
        byte[] body = new byte[0];
        InetAddress remote;

        String param(String name, String def) {
            String v = query.get(name);
            return v != null ? v : def;
        }

        String bodyText() { return new String(body, StandardCharsets.UTF_8); }
    }

    static final class Response {
        int status = 200;
        String type = "application/json; charset=utf-8";
        byte[] body;

        static Response json(int status, String json) {
            Response r = new Response();
            r.status = status;
            r.body = json.getBytes(StandardCharsets.UTF_8);
            return r;
        }

        static Response bytes(String type, byte[] body) {
            Response r = new Response();
            r.type = type;
            r.body = body;
            return r;
        }
    }

    interface Handler { Response handle(Request req) throws Exception; }

    private final int port;
    private final Handler handler;
    private final ExecutorService pool = Executors.newFixedThreadPool(4);
    private volatile ServerSocket socket;
    private Thread acceptor;

    HttpServer(int port, Handler handler) {
        this.port = port;
        this.handler = handler;
    }

    void start() {
        acceptor = new Thread(this::acceptLoop, "http-accept");
        acceptor.start();
    }

    void stop() {
        ServerSocket s = socket;
        socket = null;
        if (s != null) try { s.close(); } catch (IOException ignored) {}
        pool.shutdownNow();
    }

    private void acceptLoop() {
        // Retry binding: right after boot or a service restart the port can still be held briefly.
        while (true) {
            try {
                ServerSocket s = new ServerSocket();
                s.setReuseAddress(true);
                s.bind(new InetSocketAddress(port));
                socket = s;
                break;
            } catch (IOException e) {
                Log.w(TAG, "bind " + port + " failed, retrying", e);
                try { Thread.sleep(2000); } catch (InterruptedException ie) { return; }
            }
        }
        Log.i(TAG, "listening on " + port);
        while (socket != null) {
            try {
                Socket c = socket.accept();
                pool.execute(() -> serve(c));
            } catch (IOException e) {
                if (socket == null) return;
                Log.w(TAG, "accept failed", e);
            }
        }
    }

    private void serve(Socket c) {
        try (Socket conn = c) {
            conn.setSoTimeout(30000);
            InputStream in = new BufferedInputStream(conn.getInputStream());
            Request req = parse(in);
            Response res;
            if (req == null) {
                res = Response.json(400, "{\"error\":\"bad request\"}");
            } else {
                req.remote = conn.getInetAddress();
                try {
                    res = handler.handle(req);
                } catch (IllegalArgumentException e) {
                    res = Response.json(400, "{\"error\":" + Json.quote(String.valueOf(e.getMessage())) + "}");
                } catch (Throwable e) {
                    Log.e(TAG, "handler failed: " + req.path, e);
                    res = Response.json(500, "{\"error\":" + Json.quote(e.toString()) + "}");
                }
            }
            write(conn.getOutputStream(), res);
        } catch (IOException e) {
            Log.w(TAG, "connection failed", e);
        }
    }

    private static Request parse(InputStream in) throws IOException {
        String line = readLine(in);
        if (line == null || line.isEmpty()) return null;
        String[] parts = line.split(" ");
        if (parts.length < 2) return null;
        Request req = new Request();
        req.method = parts[0].toUpperCase(Locale.ROOT);
        String target = parts[1];
        int q = target.indexOf('?');
        req.path = q >= 0 ? target.substring(0, q) : target;
        if (q >= 0) {
            for (String kv : target.substring(q + 1).split("&")) {
                if (kv.isEmpty()) continue;
                int eq = kv.indexOf('=');
                String k = eq >= 0 ? kv.substring(0, eq) : kv;
                String v = eq >= 0 ? kv.substring(eq + 1) : "";
                req.query.put(URLDecoder.decode(k, "UTF-8"), URLDecoder.decode(v, "UTF-8"));
            }
        }
        String h;
        while ((h = readLine(in)) != null && !h.isEmpty()) {
            int colon = h.indexOf(':');
            if (colon > 0) req.headers.put(h.substring(0, colon).trim().toLowerCase(Locale.ROOT), h.substring(colon + 1).trim());
        }
        String len = req.headers.get("content-length");
        if (len != null) {
            int n = Integer.parseInt(len);
            if (n < 0 || n > 4 * 1024 * 1024) return null;
            byte[] body = new byte[n];
            int off = 0;
            while (off < n) {
                int r = in.read(body, off, n - off);
                if (r < 0) return null;
                off += r;
            }
            req.body = body;
        }
        return req;
    }

    private static String readLine(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        int b;
        while ((b = in.read()) >= 0) {
            if (b == '\n') break;
            if (b != '\r') buf.write(b);
            if (buf.size() > 16384) throw new IOException("line too long");
        }
        if (b < 0 && buf.size() == 0) return null;
        return buf.toString("UTF-8");
    }

    private static void write(OutputStream out, Response res) throws IOException {
        byte[] body = res.body != null ? res.body : new byte[0];
        String head = "HTTP/1.1 " + res.status + " " + (res.status == 200 ? "OK" : "Error") + "\r\n"
                + "Content-Type: " + res.type + "\r\n"
                + "Content-Length: " + body.length + "\r\n"
                + "Connection: close\r\n\r\n";
        out.write(head.getBytes(StandardCharsets.UTF_8));
        out.write(body);
        out.flush();
    }
}
