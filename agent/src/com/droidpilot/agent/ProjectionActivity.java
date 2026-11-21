package com.droidpilot.agent;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;

/** Invisible activity that asks for screen-capture permission and hands the grant to Capture. */
public class ProjectionActivity extends Activity {
    private static final int REQUEST = 1;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        MediaProjectionManager mpm = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        startActivityForResult(mpm.createScreenCaptureIntent(), REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQUEST && resultCode == RESULT_OK && data != null) {
            Capture.start(getApplicationContext(), resultCode, data);
        }
        finish();
        overridePendingTransition(0, 0);
    }
}
