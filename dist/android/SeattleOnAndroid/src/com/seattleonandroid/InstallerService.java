/*
 * Copyright (C) 2010 Google Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.seattleonandroid;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Binder;
import android.os.Bundle;
import android.os.Environment;
import android.os.IBinder;
import android.os.StatFs;

import com.seattleonandroid.R;
import com.seattleonandroid.process.SeattleScriptProcess;
import com.googlecode.android_scripting.AndroidProxy;
import com.googlecode.android_scripting.BaseApplication;
import com.googlecode.android_scripting.FileUtils;
import com.googlecode.android_scripting.ForegroundService;
import com.googlecode.android_scripting.Log;
import com.googlecode.android_scripting.NotificationIdFactory;
import com.googlecode.android_scripting.interpreter.InterpreterConfiguration;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 
 * SeattleOnAndroid Installer Service
 * 
 * Loosely based on the Service found in the ScriptForAndroidTemplate project in SL4A
 *  
 */
public class InstallerService extends ForegroundService {

	private final static int NOTIFICATION_ID = NotificationIdFactory.create();
	private final IBinder mBinder;

	private InterpreterConfiguration mInterpreterConfiguration;
	private AndroidProxy mProxy;
	private Notification notification;

	// An instance of the service, used to determine whether it is running or not
	private static InstallerService instance = null;
	// Checks whether the service is running or not
	public static boolean isInstalling(){
		return instance!=null;
	}

	// Binder class
	public class LocalBinder extends Binder {
		public InstallerService getService() {
			return InstallerService.this;
		}
	}

	public InstallerService() {
		super(NOTIFICATION_ID);
		mBinder = new LocalBinder();
	}

	@Override
	public IBinder onBind(Intent intent) {
		return mBinder;
	}

	@Override
	public void onCreate() {
		super.onCreate();
		mInterpreterConfiguration = ((BaseApplication) getApplication()).getInterpreterConfiguration();
	}

	// Checks whether the installation was successful by inspecting the installInfo log file
	public boolean checkInstallationSuccess(){
		// Prefer installInfo.new to installInfo.old
		File f = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle/seattle_repy/installInfo.new");
		if(!f.exists()){
			f = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle/seattle_repy/installInfo.old");
			if(!f.exists())
				return false;
		}
		try {
			// Iterate through the file line by line, remembering the previous line
			BufferedReader r = new BufferedReader(new FileReader(f));
			String line, prevLine = null;
			while((line = r.readLine())!=null)
				prevLine = line;
			return (prevLine != null && prevLine.contains("seattle completed installation"));
		} catch (Exception e) {
			// Log exception
			Log.e(e);
		}
		return false;
	}

	@Override
	public void onStart(Intent intent, final int startId) {
		super.onStart(intent, startId);
		
		// Set instance to self
		instance = this;
		
		// Set up notification icon
		String ns = Context.NOTIFICATION_SERVICE;
		final NotificationManager mNotificationManager = (NotificationManager) getSystemService(ns);

		Intent callIntent = new Intent(this, ScriptActivity.class);
		final PendingIntent contentIntent = PendingIntent.getActivity(this, 0, callIntent, 0);

		notification.setLatestEventInfo(this, this.getString(R.string.srvc_install_name), this.getString(R.string.srvc_install_copy), contentIntent);
		notification.flags = Notification.FLAG_AUTO_CANCEL;
		
		mNotificationManager.notify(NOTIFICATION_ID, notification);

		final ForegroundService s = this;
		final Intent fInt = intent;
		
		Thread t = new Thread()
		{
			public void run(){
				// Create seattle root folder
				File seattleFolder = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle/");
				if (seattleFolder.mkdirs())
					; // folder created
				else
					; // folder not created
				
				// Copy seattle archive to seattle root;
				// Reason: random access is not possible on resources inside the apk
				//File archive = FileUtils.copyFromStream(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle.zip", getResources().openRawResource(R.raw.seattle));
				File archive = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle.zip");
				archive.delete();
		
				String user_hash = ReferralReceiver.retrieveReferralParams(s.getApplicationContext()).get("utm_content");
				if (user_hash == null)
					user_hash = "flibble";
				
				try {
					URL url = new URL("https://seattlegeni.cs.washington.edu/geni/download/"+user_hash+"/seattle_win.zip");
					Log.d(url.toString());
					URLConnection ucon = url.openConnection();
					InputStream is = ucon.getInputStream();
					BufferedInputStream bis = new BufferedInputStream(is);
					FileOutputStream fos = new FileOutputStream(archive);
					int len = 0;
					byte[] buffer = new byte[4096];
					Log.d("Download started...");
					while ((len = bis.read(buffer)) != -1) {
						fos.write(buffer,0,len);
					}
					Log.d("Download finished...");
					bis.close();
					fos.close();
				} catch (MalformedURLException e) {
					e.printStackTrace();
					
					instance = null;
					ScriptActivity.handler.sendEmptyMessage(ScriptActivity.INSTALL_FAILED);
					// 	Stop service
					stopSelf(startId);
					return;
					
				} catch (IOException e) {
					e.printStackTrace();
					
					instance = null;
					ScriptActivity.handler.sendEmptyMessage(ScriptActivity.INSTALL_FAILED);
					// 	Stop service
					stopSelf(startId);
					return;
					
				}
		
				// Unzip archive
				try{
					Unzip.unzip(archive.getAbsolutePath(), Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a");
				} catch (Exception e) {
					e.printStackTrace();
					
					
					archive.delete();
					
					instance = null;
					ScriptActivity.handler.sendEmptyMessage(ScriptActivity.INSTALL_FAILED);
					// 	Stop service
					stopSelf(startId);
					return;					
				}
		
				// Remove archive
				archive.delete();
		
				// Update notification
				notification.setLatestEventInfo(s, s.getString(R.string.srvc_install_name), s.getString(R.string.srvc_install_config), contentIntent);
				notification.flags = Notification.FLAG_AUTO_CANCEL;
				mNotificationManager.notify(NOTIFICATION_ID, notification);
		
				// Get installer script file
				File installer = new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle/seattle_repy/seattleinstaller.py");
				
				mProxy = new AndroidProxy(s, null, true);
				mProxy.startLocal();
		
				// Get percentage of resources to donate 
				Bundle b = fInt.getExtras();
				int donate = b.getInt(ScriptActivity.RESOURCES_TO_DONATE, 50);
				
				String[] iflist = b.getStringArray(ScriptActivity.PERMITTED_INTERFACES);
				
				// Get information about cores and storage space
				StatFs statfs = new StatFs(Environment.getExternalStorageDirectory().getPath());
				int cores = Runtime.getRuntime().availableProcessors();
				int freeSpace = statfs.getAvailableBlocks() *statfs.getBlockSize();
				
				// Set environmental variables
				Map<String, String> env = new HashMap<String, String>();
				env.put("SEATTLE_AVAILABLE_CORES", Integer.toString(cores));
				env.put("SEATTLE_AVAILABLE_SPACE", Integer.toString(freeSpace));
		
				// Set arguments
				List<String> args = new ArrayList<String>();
				args.add("--percent");
				args.add(Integer.toString(donate)); // make sure that dot is used as the decimal separator instead of comma
				args.add("--disable-startup-script");
				args.add("True");
				
				if (iflist != null)
				{
					for(int i=0; i<iflist.length; i++)
					{
						args.add("--nm-iface");
						args.add(iflist[i]);
						args.add("--repy-iface");
						args.add(iflist[i]);
					}
					args.add("--repy-nootherips");
				}
				
				String optionalArgs = b.getString(ScriptActivity.OPTIONAL_ARGUMENTS);
				if (optionalArgs != null)
					args.add(optionalArgs);
				
				// Launch installer
				SeattleScriptProcess.launchScript(installer, mInterpreterConfiguration, mProxy, new Runnable() {
					@Override
					public void run() {
						mProxy.shutdown();
		
						// Mark installation terminated
						instance = null;
		
						// Check whether the installation was successful or not
						if(checkInstallationSuccess())
						{
							// Send message to activity about success
							ScriptActivity.handler.sendEmptyMessage(ScriptActivity.SEATTLE_INSTALLED);
						}
						else
						{
							// If it was unsuccessful, remove nmmain.py, so that the app will not think seattle is installed
							// Other files are not removed to preserve the log files 
							FileUtils.delete(new File(Environment.getExternalStorageDirectory().getAbsolutePath()+"/sl4a/seattle/seattle_repy/nmmain.py"));
							// Send message to activity about failure
							instance = null;
							ScriptActivity.handler.sendEmptyMessage(ScriptActivity.INSTALL_FAILED);
						}
		
						// Stop service
						stopSelf(startId);
					}
				}, installer.getParent(), args, env);
			};
		};
		
		t.start();
	}

	// Create initial notification
	@Override
	protected Notification createNotification() {
		
		Notification notification = new Notification(R.drawable.seattlelogo, this.getString(R.string.srvc_install_start), System.currentTimeMillis());
		
		Intent intent = new Intent(this, ScriptActivity.class);
		PendingIntent contentIntent = PendingIntent.getActivity(this, 0, intent, 0);
		
		notification.setLatestEventInfo(this, this.getString(R.string.srvc_install_name), this.getString(R.string.srvc_install_start), contentIntent);
		
		notification.flags = Notification.FLAG_AUTO_CANCEL;
		this.notification = notification;
		
		return notification;
	}
}
