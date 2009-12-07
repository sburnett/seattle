# checks if httpretrieve sends the posted data in correct format to a server


# prints failed error msg if httpretrieve failes the test and just excutes if the
# test pass's the test


include httpretrieve.repy
include registerhttpcallback.repy



def server_test_content(httprequest_dictionary):
  # temp server that sends the clients posted data as the http content   
      
  # return the content to check if the httpretrieve gets the same content 
  return httprequest_dictionary['posted_data']
  
  
       
if callfunc == 'initialize':

  # data to post to server using the httpretrieve 
  http_post = ''
  for i in range(100):
    http_post += str(i)  
    
  # build temp server that acts normally and sends what ever the client posted data is
  try:    
    server_handle = registerhttpcallback('http://127.0.0.1:12345', server_test_content)
  except Exception, e:
    stop_registerhttpcallback(server_handle)
    raise Exception('Server failed internally ' + str(e))  

  try:
    # use httpretrieve to retrieve the content form the server.(which is the posted data)  
    recv_msg = httpretrieve_get_string('http://127.0.0.1:12345', http_post)   

  except Exception, e:
    print 'Http retrieve failed on receiving content, Raised: ' + str(e)
  else:
    if recv_msg != http_post:
      print 'failed: the received posted data didnt match the actual posted data'
      print 'httpretrieve posted ' + http_post
      print 'server receieved ' + recv_msg 
  
  finally:
    #stop the server from waiting for more connections
    stop_registerhttpcallback(server_handle)
