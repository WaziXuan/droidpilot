package com.droidpilot.agent;

import android.graphics.Rect;
import android.os.Build;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import java.util.List;

/**
 * Writes the accessibility tree in uiautomator's dump format, so droidpilot's
 * parser reads it unchanged: one top-level node per window, top window first.
 */
final class TreeDumper {
    private static final int MAX_DEPTH = 80;

    private TreeDumper() {}

    static String dump(List<AccessibilityWindowInfo> windows, AccessibilityNodeInfo fallbackRoot, int rotation) {
        StringBuilder sb = new StringBuilder(64 * 1024);
        sb.append("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>");
        sb.append("<hierarchy rotation=\"").append(rotation).append("\">");
        boolean any = false;
        if (windows != null) {
            int index = 0;
            for (AccessibilityWindowInfo w : windows) {
                AccessibilityNodeInfo root = w.getRoot();
                if (root == null) continue;
                node(sb, root, index++, 0);
                root.recycle();
                any = true;
            }
        }
        if (!any && fallbackRoot != null) {
            node(sb, fallbackRoot, 0, 0);
        }
        sb.append("</hierarchy>");
        return sb.toString();
    }

    private static void node(StringBuilder sb, AccessibilityNodeInfo n, int index, int depth) {
        Rect r = new Rect();
        n.getBoundsInScreen(r);
        sb.append("<node index=\"").append(index).append('"');
        attr(sb, "text", n.getText());
        attr(sb, "resource-id", n.getViewIdResourceName());
        attr(sb, "class", n.getClassName());
        attr(sb, "package", n.getPackageName());
        attr(sb, "content-desc", n.getContentDescription());
        if (Build.VERSION.SDK_INT >= 26) attr(sb, "hint", n.getHintText());
        bool(sb, "checkable", n.isCheckable());
        bool(sb, "checked", n.isChecked());
        bool(sb, "clickable", n.isClickable());
        bool(sb, "enabled", n.isEnabled());
        bool(sb, "focusable", n.isFocusable());
        bool(sb, "focused", n.isFocused());
        bool(sb, "scrollable", n.isScrollable());
        bool(sb, "long-clickable", n.isLongClickable());
        bool(sb, "password", n.isPassword());
        bool(sb, "selected", n.isSelected());
        bool(sb, "visible-to-user", n.isVisibleToUser());
        sb.append(" bounds=\"[").append(r.left).append(',').append(r.top).append("][")
          .append(r.right).append(',').append(r.bottom).append("]\"");
        int count = depth < MAX_DEPTH ? n.getChildCount() : 0;
        if (count == 0) {
            sb.append(" />");
            return;
        }
        sb.append('>');
        for (int i = 0; i < count; i++) {
            AccessibilityNodeInfo c = n.getChild(i);
            if (c == null) continue;
            node(sb, c, i, depth + 1);
            c.recycle();
        }
        sb.append("</node>");
    }

    private static void bool(StringBuilder sb, String name, boolean v) {
        sb.append(' ').append(name).append("=\"").append(v ? "true" : "false").append('"');
    }

    private static void attr(StringBuilder sb, String name, CharSequence v) {
        sb.append(' ').append(name).append("=\"");
        if (v != null) escape(sb, v);
        sb.append('"');
    }

    private static void escape(StringBuilder sb, CharSequence s) {
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '&': sb.append("&amp;"); break;
                case '<': sb.append("&lt;"); break;
                case '>': sb.append("&gt;"); break;
                case '"': sb.append("&quot;"); break;
                case '\n': sb.append("&#10;"); break;
                case '\r': sb.append("&#13;"); break;
                case '\t': sb.append("&#9;"); break;
                default:
                    // XML 1.0 forbids most control characters; apps do put them in labels.
                    if (c < 0x20 || c == 0xFFFE || c == 0xFFFF) sb.append(' ');
                    else sb.append(c);
            }
        }
    }
}
