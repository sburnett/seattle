def foo(ip,port,sockobj, ch,mainch):
  stopcomm(mainch)
  stopcomm(ch)

if callfunc == 'initialize':
  waitforconn('127.0.0.1',12345,foo)
  sleep(.1)
  openconn('127.0.0.1',12345)
