#!/usr/bin/python

"""
This middleware application forwards packets from the MultipathShim of the
sending host to the MultipathShim of the receiving host, although it can be
easily modified to forward the messages to the other forwarders as well.

Written by: Danny Y. Huang (yh1@cs.williams.edu)

"""

from repyportability import *
import repyhelper

repyhelper.translate_and_import('advertise.repy')

# The interval (in seconds) between successive forwarding of messages
SENDMESS_INTERVAL = 0.01

myip = getmyip()
myport = 37201

# Lock for the event queue
queue_lock = getlock()

# Lock for logfile I/O
log_lock = getlock()

# All pending messages are written to the event queue.
send_queue = []

# Indicates whether the forwarder is active. Set to false to quit.
active = True


def main():
    """
    Command-line argument: [sendmess_interval] A float that indicates how fast
    we should forward messages. Optional.

    """
    global active

    # Resets log file
    try:
        logfile = open('multipath.log', 'w')
    finally:
        logfile.close()

    # Set up listener
    handle = recvmess(myip, myport, incoming_message)

    # Advertise myself in a separate thread
    settimer(0, advertise_forwarder, [])

    # Try to obtain the sendmess interval from the command-line (optional argument)
    try:
        sendmess_interval = float(callargs[0])
    except:
        sendmess_interval = SENDMESS_INTERVAL

    # Keep forwarding until keyboard interrupt
    while True:
        forward_message()
        try:
            sleep(sendmess_interval)
        except KeyboardInterrupt, err:
            break

    # Clean up threads
    active = False
    stopcomm(handle)

    return



def forward_message():
    """
    Grabs a message from the send queue and forwards it to the correct
    destination.

    """
    try:
        queue_lock.acquire()
        (msg, remoteip, remoteport) = send_queue.pop(0)
    except IndexError, err:
        # Empty queue.
        return
    finally:
        queue_lock.release()

    # Extracts and parses the header from the message, which is in the form of
    # dest_host@dest_port@hops@src_host@src_port@msg_id@message_content. Here,
    # we are not interested in the message_id or the message content.
    try:
        (dest_host, dest_port, hops, src_host, src_port, payload) = msg.split('@', 5)
        dest_port = int(dest_port)
        src_port = int(src_port)
        hops = int(hops)
    except ValueError, err:
        logthis('ERROR: Bad message from %s with length %s.' % (remoteip, len(msg)))
        return

    # Drops message to prevent circular hopping
    if hops <= 0:
        return

    # If the src information is not set (default zero), we can set it now
    # because we know this is the first hop.
    if src_host == '0' and src_port == 0:
        src_host = remoteip
        src_port = remoteport

    # Reassemble message with decreased hopcount
    new_msg = '@'.join([dest_host, str(dest_port), str(hops - 1),
                        src_host, str(src_port), payload])

    # Send message to the intended destination. We can easily modify the
    # following statement so that the message is sent to the other forwarders as
    # well.
    try:
        sendmess(dest_host, dest_port, new_msg)
    except Exception, err:
        logthis('ERROR: Unable to send message to %s:%s because "%s".' % (dest_host, dest_port, err))





def incoming_message(remoteip, remoteport, msg, handle):
    """
    Forwards incoming message to its own destination. Each message is encoded as
    follows:

    dest_host@dest_port@hops@src_host@src_port@msg_id@msg_contents

    Each message is not immediately forwarded. Instead, it is held in a send
    queue. This shortens the execution time of this thread and thus makes it
    less likely for the OS to drop incoming messages.

    """
    queue_lock.acquire()
    send_queue.append([msg, remoteip, remoteport])
    queue_lock.release()



def advertise_forwarder():
    """
    Advertise the IP address of this forwarder at a fixed interval. This
    facilitates the multipath shim to locate the forwarder.

    """
    # The value to advertise
    myname = myip + ':' + str(myport)

    # We will print the advertisement status only once.
    print_status_once = False

    while active:

        # Advertise until successful
        while True:
            try:
                advertise_announce('multipath_forwarders', myname, 120)
                if not print_status_once:
                    print_status_once = True
                    logthis('Advertised ' + myname)
            except Exception, err:
                sleep(1)
            else:
                break

        sleep(40)



def logthis(logstr):
    """ Appends logs to multipath.log. """
    try:
        log_lock.acquire()
        logfile = open('multipath.log', 'a')
        logfile.write(str(logstr) + '\n')
        print str(logstr)
    except Exception, err:
        pass
    finally:
        logfile.close()
        log_lock.release()




if __name__ == '__main__':
    main()
