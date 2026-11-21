package com.droidpilot.agent;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Measures throughput from this app's point of view, i.e. through whatever VPN
 * routing ordinary apps get (Termux and adb shell may be routed differently).
 * {"url": ..., "seconds": 10}            download for up to `seconds`
 * {"url": ..., "upload_bytes": N}        POST N zero bytes
 * {"url": ..., "text": true}             return the first 300 characters of the body
 */
final class NetTest {
    private NetTest() {}

    static JSONObject run(JSONObject req) throws Exception {
        String url = req.getString("url");
        if (!url.startsWith("http://") && !url.startsWith("https://")) throw new IllegalArgumentException("http(s) url only");
        long limitMs = Math.min(60, Math.max(1, req.optInt("seconds", 10))) * 1000L;
        long upload = req.optLong("upload_bytes", 0);
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(15000);
        c.setInstanceFollowRedirects(true);
        long t0 = System.nanoTime();
        JSONObject out = new JSONObject();
        byte[] buf = new byte[64 * 1024];
        try {
            if (upload > 0) {
                c.setDoOutput(true);
                c.setRequestMethod("POST");
                c.setFixedLengthStreamingMode(upload);
                long sent = 0;
                try (OutputStream os = c.getOutputStream()) {
                    while (sent < upload && System.nanoTime() - t0 < limitMs * 1_000_000L) {
                        int n = (int) Math.min(buf.length, upload - sent);
                        os.write(buf, 0, n);
                        sent += n;
                    }
                }
                int code = c.getResponseCode();
                double secs = (System.nanoTime() - t0) / 1e9;
                return out.put("status", code).put("bytes", sent).put("seconds", secs).put("mbps", sent * 8 / secs / 1e6);
            }
            int code = c.getResponseCode();
            long ttfb = System.nanoTime();
            InputStream in = code >= 400 ? c.getErrorStream() : c.getInputStream();
            long total = 0;
            ByteArrayOutputStream text = req.optBoolean("text") ? new ByteArrayOutputStream() : null;
            if (in != null) {
                try (InputStream s = in) {
                    int n;
                    while ((n = s.read(buf)) >= 0) {
                        total += n;
                        if (text != null && text.size() < 1200) text.write(buf, 0, Math.min(n, 1200 - text.size()));
                        if (System.nanoTime() - t0 > limitMs * 1_000_000L) break;
                    }
                }
            }
            double secs = (System.nanoTime() - t0) / 1e9;
            double body = (System.nanoTime() - ttfb) / 1e9;
            out.put("status", code).put("bytes", total).put("seconds", secs).put("ttfb", (ttfb - t0) / 1e9)
               .put("mbps", body > 0 ? total * 8 / body / 1e6 : 0);
            if (text != null) {
                String s = new String(text.toByteArray(), StandardCharsets.UTF_8);
                out.put("text", s.length() > 300 ? s.substring(0, 300) : s);
            }
            return out;
        } finally {
            c.disconnect();
        }
    }
}
