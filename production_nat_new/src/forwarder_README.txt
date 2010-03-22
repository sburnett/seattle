This README is currently a working list of thngs to do on the forwarder.

	1. Backwards compatibility
	2. Logging
	
Information i would want to know

1. how many forwarders are available.  - advertisement
2. how many servers is each forwarder supporting. - advertisement
3. how many clients are connected to each server - client log
4. what number of clients are legacy, what number are not
5. What errors have occured. - error log

summary:

1+2 each forwarder advertises its name and how many servers are connected
3+4. a client log will exist with entries like
	TIME,CLIENT,LEGACY | CURRENT,CONNECTED | DISCONNECTED,SERVER
5.  the error log is just a print out of errors.

6. hey, why not a server log that looks like to the client log.


NOTES:

old forwarders would toggle their advertisements on and off when they are full
THis forwarder does not (not even for the legacy advertisement)
Because of this legacy clients are more likely to recieve the nat_Status_bsy signal
but this should be okay, it will just take longer for them to find a forwarder to
connect to.

	