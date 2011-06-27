import sys

dy_import_module_symbols("shimstackinterface")
dy_import_module_symbols("random")


SHIM_STR = "(FECShim)"
SERVER_IP = getmyip()
SERVER_PORT = 35742

NUM_MSG_TO_SEND = 2**10
MAX_MSG_LENGTH = 2**12


msg_sent_set = set()
msg_recv_set = set()

duplicated_msgs = []
corrupted_msgs = []
dropped_msgs = []



# Listen for UDP messages.
def launch_server(udpserver_socket):

  def _server_helper():
    log("Launching server on port %d\n" % SERVER_PORT)
    sys.stdout.flush()

    while True:
      try:
        rip, rport, message = udpserver_socket.getmessage()
      except SocketWouldBlockError:
        pass
      except SocketClosedLocal:
        break
      else:
        if message in msg_recv_set:
          duplicated_msgs.append(message)
        else:
          msg_recv_set.add(message)

  return _server_helper



# The test launching point.
def launch_test():

  recv_shim_obj = ShimStackInterface(SHIM_STR)
  udpserver_socket = recv_shim_obj.listenformessage(SERVER_IP, SERVER_PORT)

  try:

    server = launch_server(udpserver_socket)
    createthread(server)

    sleep(2)

    send_shim_obj = ShimStackInterface(SHIM_STR)
    
    for i in range(NUM_MSG_TO_SEND):
      message = generate_message()
      while message in msg_sent_set:
        message = generate_message()
      send_shim_obj.sendmessage(SERVER_IP, SERVER_PORT, message, SERVER_IP, SERVER_PORT+1)
      msg_sent_set.add(message)
      
    sleep(2)

    for message in msg_recv_set:
      if message not in msg_sent_set:
        corrupted_msgs.append(message)

    for message in msg_sent_set:
      if message not in msg_recv_set:
        dropped_msgs.append(message)

    log("Messages Sent: %d\n" % len(msg_sent_set))
    log("Messages Received: %d\n" % len(msg_recv_set))

    log("Duplicated Messages: %d\n" % len(duplicated_msgs))
    log("Corrupted Messages: %d\n" % len(corrupted_msgs))
    log("Dropped Messages: %d\n" % len(dropped_msgs))

    if duplicated_msgs or corrupted_msgs or dropped_msgs:
      log("[FAIL]\n")
      raise Exception("There were %d duplicated, %d corrupted, and %d dropped messages!" \
                      % (len(duplicated_msgs),len(corrupted_msgs),len(dropped_msgs)))
    else:
      log("[PASS]\n")

  finally:
    udpserver_socket.close()



# Generate a random message to send
def generate_message():
  msg_len = random_randint(1, MAX_MSG_LENGTH)
  return random_randombytes(msg_len)



launch_test()

