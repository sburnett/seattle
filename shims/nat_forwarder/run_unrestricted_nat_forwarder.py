import sys
import dylink_portability

if len(sys.argv) < 2:
    print "Usage: \n\t$> python run_nat_forwarder.py TCP_PORT"
    sys.exit()

TCP_PORT = sys.argv[1]

dylink_portability.run_unrestricted_repy_code("nat_forwarder.repy", [TCP_PORT])
