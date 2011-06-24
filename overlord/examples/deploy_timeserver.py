import overlord

def main():
  # Deploy the time server on 5 vessels
  time_server = overlord.Overlord(GENI_USERNAME, 5, 'wan', 'time_server.py')
  # Override run()'s start-up function with print_foo
  time_server.init_overlord_func = print_foo
  time_server.run(time_server.config['geni_port'])


# Method that will override Overlord's init_overlord_func
def print_foo(overlord):
  # Access the current Overlord object's logger to print "foo"
  overlord.logger.info("foo")


if __name__ == "__main__":
  main()
