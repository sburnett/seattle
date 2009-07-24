 import deploy_main
 import deploy_server_monitor
 
 def main():
  # Stops the web server, and any custom scripts as well as the monitor service
  # also launches testing scripts every three hours
  if deploy_server_monitor.webserver_is_running():
    deploy_main.shellexec('
  while True:
    # so we don't spam, we just need to spin this main thread and keep it 
    # from exiting
    time.sleep(60)
  
if __name__ == "__main__":
  main()
