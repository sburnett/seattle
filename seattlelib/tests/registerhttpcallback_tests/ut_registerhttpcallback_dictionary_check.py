# tests a if the registorhttpcallback httprequest_dictionary that is a argument for
# the callback funciton is legit


# prints failed message if the test failes and raises an exception the registorhttpcallback
# or httpretrieve raises an exception and just excutes if the test passes


include registerhttpcallback.repy
include httpretrieve.repy


def test_normal_server(httprequest_dictionary):
  # normal server just sends a message  

  # store the http dictionary to check the content
  mycontext['httprequest_dictionary'] = httprequest_dictionary
  return ' '
   
    
if callfunc == 'initialize':
  # used to store the httprequest_dictionary from server
  mycontext['httprequest_dictionary'] = {}
  
  # used to send post data using the httpretrieve client
  mycontext['posted_data'] = ''
  for i in range(100):
    mycontext['posted_data'] += str(i)  

  # register the callback server
  try:
    handle = registerhttpcallback('http://127.0.0.1:12345', test_normal_server)
  except Exception, e:
     raise Exception('failed test: server raised an exception: ' + str(e))

  else:
    # send a request to receive the content sent from the server
    try: 
      recvd_content = httpretrieve_get_string('http://127.0.0.1:12345/fake/path.html?fakequerystring', mycontext['posted_data']) 
    except Exception, e:
      raise Exception('httpretrieve raised an exception: ' + str(e))

    else:
      # check the http request dictionary  
      httprequest_dictionary = mycontext['httprequest_dictionary']
      
      # check the essential dictionary content indvidually to see if they are returned to the callback function correctly 
      if httprequest_dictionary['Content-Length'] != str(len(mycontext['posted_data'])):
         print 'dictionary content length failed. Actual posted data length: ' + str(len(mycontext['posted_data']))
         print 'dictionaries content length: ' + str(httprequest_dictionary['Content-Length']) 

      if httprequest_dictionary['posted_data'] != mycontext['posted_data']:
         print 'dictionary posted_data failed. Actual posted data: ' + mycontext['posted_data']
         print ', dictionaries posted: ' + str(httprequest_dictionary['Content-Length']) 

      if httprequest_dictionary['http_version'] != 'HTTP/1.1':
        print 'dictionary http_version failed. Actual http_version: HTTP/1.1, dictionaries http_version: ' + httprequest_dictionary['http_version'] 

      if httprequest_dictionary['http_command'] != 'POST':
        print 'dictionary http_command failed. http_command, Actual http_command: POST, dictionaries http_command: ' + httprequest_dictionary['http_command'] 

      if httprequest_dictionary['Server'] != 'Seattle Testbed':    
        print 'dictionary Server failed. Actual Server: Seattle Testbed, dictionaries Server: ' + httprequest_dictionary['Server']
         
      if httprequest_dictionary['Host'] != '127.0.0.1:12345':
        print 'dictionary Host failed. Actual Host: 127.0.0.1:12345, dictionaries Host: ' + httprequest_dictionary['http_command']
         
      if httprequest_dictionary['path'] != '/fake/path.html':    
        print 'dictionary path failed. Actual path: /fake/path.html, dictionaries path: ' + httprequest_dictionary['path']

      if httprequest_dictionary['query'] != 'fakequerystring':
        print 'dictionary query failed. Actual query: ?fakequerystring, dictionaries query: ' + httprequest_dictionary['query']  
      
    finally: 
      # stop the server  
      stop_registerhttpcallback(handle)
