"""
<Program>
    shim_dumb_server.py

<Author>
    Monzur Muhammad
    monzum@cs.washington.edu

<Purpose>
    This will retrieve file from the apache http
    server, and return it to the requesting machine.
"""

import os
import sys
import repyportability


# The address and port of the outgoing connection.
server_address = "localhost"
server_port = 80

# The max buffersize. The amount of data to send at a time.
buffer_size = 2<<14 # 32KB


def tcp_file_server(remoteip, remoteport, sockobj, thiscomm_handle, listen_handle):
    """
    <Purpose>
        This function is launched when there is any incoming messages
        from a client.

    <Arguments>
        remoteip - the ip address of the remote node.
        remoteport - the port of the remote host.
        sockobj - a socket like object used for communication.
        thiscomm_handle - a handle for this communication.
        listen_handle - handle for listening to communication.

    <Exceptions>
        None.

    <Return>
        None.
    """

    print "Incoming connection from: %s:%s" % (remoteip, remoteport)

    # We are going to wait until we receive a message from the
    # client.
    message_received = ""
    while True:
        try:
            message_received = sockobj.recv(1024)
        except Exception, err: 
            # If there is any exception, we return because
            # we did not receive the proper message.
            sockobj.close()
            return
        
        if message_received:
            break


    # Open a connection to the server to send the message.
    server_sockobj = repyportability.openconn(server_address, server_port)
    
    # If we fail to send the message, then we just close 
    # the connection and return.
    try:
        server_sockobj.send(message_received)
    except:
        server_sockobj.close()
        sockobj.close()
        return

    
    # We will now receive the response from the server
    # and forward them back to the client.
    while True:
        try:
            sockobj.send(server_sockobj.recv(buffer_size))
        except:
            # This will occur most likely if the server side
            # closes the connection after they have sent all
            # the data.
            break
    
    
    # Close the socket object now that we are done sending the
    # data back to the client.
    try:
        sockobj.close()
        server_sockobj.close()
    except:
        pass

    print "Transfered data to %s:%s" % (remoteip, remoteport)  
        



            

def main():
    """
    <Purpose>
        This is the main of the function. It launches a 
        tcp client to connect to local apache server and
        then retrieve a file. It also has a server to 
        listen for incoming connections from the client
        version of this program.

    <Arguments>
        None.

    <Exceptions>
        None.

    <Return>
        None.
    """

    if len(sys.argv) < 4:
        usage()


    global server_address
    global server_port

    # Specify the server address and port
    server_address = sys.argv[1]
    server_port = int(sys.argv[2])
    # Specify the TCP port to listen on.
    incoming_connection_port = int(sys.argv[3])
                         

    # Launch a TCP server to listen on from the client side.
    repyportability.waitforconn(repyportability.getmyip(), incoming_connection_port, tcp_file_server)




def usage():
    message = "Usage:\n\tpython shim_apache_client.py server_addr server_port listening_port"
    print message
    sys.exit()


if __name__ == "__main__":
    main()





