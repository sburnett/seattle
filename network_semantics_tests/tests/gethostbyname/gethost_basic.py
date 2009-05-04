# a call to gethostbyname_ex with a valid host name will return a 3-tuple
# of information about the host


if callfunc == 'initialize':

  host = 'www.google.com'

  (one,two,three) = gethostbyname_ex(host)

