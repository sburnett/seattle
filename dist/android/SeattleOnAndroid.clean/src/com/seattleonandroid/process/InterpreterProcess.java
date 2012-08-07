/*
 * Copyright (C) 2009 Google Inc.
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

package com.seattleonandroid.process;

import com.googlecode.android_scripting.Analytics;
import com.googlecode.android_scripting.AndroidProxy;
import com.googlecode.android_scripting.interpreter.Interpreter;
import com.googlecode.android_scripting.interpreter.InterpreterConstants;
import com.googlecode.android_scripting.interpreter.MyInterpreter;
import com.googlecode.android_scripting.jsonrpc.RpcReceiverManagerFactory;

import java.util.List;

/**
 * Slightly modified version of the InterpreterProcess from SL4A
 * 
 * This is a skeletal implementation of an interpreter process.
 * 
 * @author Damon Kohler (damonkohler@gmail.com)
 */
public class InterpreterProcess extends Process {

  private final AndroidProxy mProxy;
  private final Interpreter mInterpreter;
  private String mCommand;

  /**
   * Creates a new {@link InterpreterProcess}.
   * 
   * @param launchScript
   *          the absolute path to a script that should be launched with the interpreter
   * @param port
   *          the port that the AndroidProxy is listening on
   */
  public InterpreterProcess(MyInterpreter interpreter, AndroidProxy proxy) {
    mProxy = proxy;
    mInterpreter = interpreter.getInterpreter();

    setBinary(mInterpreter.getBinary());
    setName(mInterpreter.getNiceName());
    setCommand(mInterpreter.getInteractiveCommand());
    addAllArguments(interpreter.getArguments());
    putAllEnvironmentVariables(System.getenv());
    putEnvironmentVariable("AP_HOST", getHost());
    putEnvironmentVariable("AP_PORT", Integer.toString(getPort()));
    if (proxy.getSecret() != null) {
      putEnvironmentVariable("AP_HANDSHAKE", getSecret());
    }
    putAllEnvironmentVariables(mInterpreter.getEnvironmentVariables());
  }

  protected void setCommand(String command) {
    mCommand = command;
  }

  public Interpreter getInterpreter() {
    return mInterpreter;
  }

  public String getHost() {
    return mProxy.getAddress().getHostName();
  }

  public int getPort() {
    return mProxy.getAddress().getPort();
  }

  public String getSecret() {
    return mProxy.getSecret();
  }

  public RpcReceiverManagerFactory getRpcReceiverManagerFactory() {
    return mProxy.getRpcReceiverManagerFactory();
  }

  @Override
  public void start(final Runnable shutdownHook) {
	  start(shutdownHook, null);
  }

  public void start(final Runnable shutdownHook, List<String> args) {
    Analytics.track(mInterpreter.getName());
    // NOTE(damonkohler): String.isEmpty() doesn't work on Cupcake.
    if (!mCommand.equals("")) {
      addArgument(mCommand);
    }
    if(args != null)
    	addAllArguments(args);
    super.start(shutdownHook);
  }

  @Override
  public void kill() {
    super.kill();
    mProxy.shutdown();
  }

  @Override
  public String getWorkingDirectory() {
    return InterpreterConstants.SDCARD_SL4A_ROOT;
  }
}
