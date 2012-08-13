package com.seattleonandroid;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;

/***
 * 
 * Listens for a BOOT_COMPLETED intent and starts the application if AUTOSTART_ON_BOOT is set
 *
 */
public class AutostartListener extends BroadcastReceiver {
	private static final int DEFAULT_STARTUP_DELAY = 30000; // Default delay (30 seconds), just in case the delay was not set in the settings
	@Override
	public void onReceive(final Context context, Intent intent) {
		// Executed on successful booting
		SharedPreferences settings = context.getSharedPreferences(ScriptActivity.SEATTLE_PREFERENCES, Context.MODE_WORLD_WRITEABLE);
		// Check if the app is to be run on startup
		if (settings.getBoolean(ScriptActivity.AUTOSTART_ON_BOOT, false)){
			int delay = settings.getInt(ScriptActivity.AUTOSTART_DELAY, DEFAULT_STARTUP_DELAY);
			// Use a handler to defer the starting of the service to a later time
			Handler handler = new Handler();
			handler.postDelayed(new Runnable() {
				public void run() {
					// Get connectivity manager and network information
					ConnectivityManager cManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
					NetworkInfo info = cManager.getActiveNetworkInfo();

					// If the external storage device is mounted properly and the network is up and running -> start the service 
					if (Environment.getExternalStorageState().equals(Environment.MEDIA_MOUNTED)
							&& info != null && info.isConnected()) {
						// Start the service
						Log.i(Common.LOG_TAG, Common.LOG_INFO_SEATTLE_STARTED_AUTOMATICALLY);
						ScriptService.serviceInitiatedByUser = true;
						context.startService(new Intent(context.getApplicationContext(), ScriptService.class));
					}
				}
			}, delay); 
			
		}
	}
}
