# -*- coding: utf-8 -*-
### Automatically generated by repyhelper.py ### /home/rille/skola/labbar/mpcsn_labs/distr_lab4/NATLayer_rpc.repy

### THIS FILE WILL BE OVERWRITTEN!
### DO NOT MAKE CHANGES HERE, INSTEAD EDIT THE ORIGINAL SOURCE FILE
###
### If changes to the src aren't propagating here, try manually deleting this file. 
### Deleting this file forces regeneration of a repy translation


from repyportability import *
import repyhelper
mycontext = repyhelper.get_shared_context()
callfunc = 'import'
callargs = []

"""

Author: Armon Dadgar, Eric Kimbrel

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).

"""


repyhelper.translate_and_import('NAT_advertisement.repy')
repyhelper.translate_and_import('Multiplexer.repy')



"""
This block of code declares and sets the constant values used for the forwarder RPC interface

NAT RPC requests are dictionaries that have special fields
A typical request would be like the following:

# Server requests to de-register
rpc_req = {"id":0,"request":"de_reg_serv"}

# Forwarder responds with success message
rpc_resp = {"id":0,"status":True,"value":None}

# To actually transfer this request, the following is necessary:
message = encode_rpc(rpc_req)
sock.send(message)

# Then, to receive a RPC mesg
rpc_mesg = decode_rpc(sock)

"""


# General Protocal Constants
RPC_VIRTUAL_IP = "0.0.0.0" # What IP is used for the virtual waitforconn / openconn
RPC_VIRTUAL_PORT = 0 # What virtual port to listen on for Remote Procedure Calls
RPC_FIXED_SIZE = 4   # Size of the RPC dictionary

# Defines fields
RPC_REQUEST_ID = "id"    # The identifier of the RPC request
RPC_FUNCTION = "request" # The remote function to call
RPC_PARAM = "value"      # The parameter to the requested function (if any)
RPC_ADDI_REQ = "additional" # Are there more RPC requests on the socket?
RPC_REQUEST_STATUS = "status" # The boolean status of the request
RPC_RESULT = "value"     # The result value if the RPC request

# Function Names
RPC_EXTERNAL_ADDR = "externaladdr"  # This allows the server to query its ip/port

# deterines if a connection is bi-directional
RPC_BI_DIRECTIONAL = "bidirectional"


# This allows a server to register with a forwarder
# This expects a MAC address as a parameter
RPC_REGISTER_SERVER = "reg_serv"    

# This allows a server to de-register from a forwarder
# This expects a MAC address as a parameter, or None to deregister all MAC's 
RPC_DEREGISTER_SERVER = "dereg_serv"

# The following two functions require an integer port and a server mac address
# # It expects the RPC_PARAM to be a dictionary:
# {"server":"__MAC__","port":50}
RPC_REGISTER_PORT = "reg_port"      # THis allows the server to register a wait port
RPC_DEREGISTER_PORT = "dereg_port"  # This allows the server to de-register a wait port

# This instructs the forwarder to begin forwarding data from this socket to a server
# It expects the RPC_PARAM to be a dictionary:
# {"server":"__MAC__","port":50}
RPC_CLIENT_INIT = "client_init"

# Helper Functions
def RPC_encode(rpc_dict):
  """
  <Purpose>
    Encodes an RPC request dictionary
  
  <Arguments>
    rpc_dict:
      A dictionary object
  
  <Returns>
    Returns a string that can be sent over a socket
  """
  rpc_dict_str = str(rpc_dict) # Conver to string
  rpc_length = str(len(rpc_dict_str)).rjust(RPC_FIXED_SIZE, "0") # Get length string
  return rpc_length + rpc_dict_str # Concatinate size with string

def RPC_decode(sock,blocking=False):
  """
  <Purpose>
    Returns an RPC request object from a socket
  
  <Arguments>
    sock:
      A socket that supports recv
    
    blocking:
      If the socket supports the blocking mode of operations, speicify this to be True
  
  <Returns>
    Returns a dictionary object containing the RPC Request
  """
  # Get the dictionary length
  # Then, Get the dictionary
  if blocking:
    length = int(sock.recv(RPC_FIXED_SIZE,blocking=True))
    dict_str = sock.recv(length,blocking=True)
  else:
    length = int(sock.recv(RPC_FIXED_SIZE))
    dict_str = sock.recv(length)
  
  dict_obj = deserialize(dict_str) # Convert to object
  return dict_obj
  




# How long we should stall nat_waitforconn after we create the mux to check its status
NAT_MUX_STALL = 2  # In seconds

# Set the messages
NAT_STATUS_NO_SERVER = "NO_SERVER"
NAT_STATUS_BSY_SERVER = "BSY_SERVER"
NAT_STATUS_CONFIRMED = "CONFIRMED"
NAT_STATUS_FAILED = "FAILED"


# Dictionary holds NAT_Connection state
NAT_STATE_DATA = {}
NAT_STATE_DATA["mux"] = None # Initialize to nothing


NAT_SRV_CACHE = {}
NAT_FORWARDER_CACHE = {}

# Holds the ports we are listening on
NAT_LISTEN_PORTS = {}


# a lock used for stopcomm and nat_persist
NAT_STOP_LOCK = getlock()

#########################################################################

# Wrapper function around the NATLayer for clients        
def nat_openconn(destmac, destport, localip=None, localport=None, timeout = 5, forwarderIP=None,forwarderPort=None,usetimeoutsock=False):
  """
  <Purpose>
    Opens a connection to a server behind a NAT.
  
  <Arguments>
    destmac:
      A string identifer for the destination server
    
    destport:
      The port on the host to connect to.
    
    localip:
      See openconn.
    
    localport:
      See openconn.
    
    timeout:
      How long before timing out the forwarder connection
    
    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      forwarderPort must be specified if this is not None.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      forwarderIP must be specified if this is not None.
    
     usetimeoutsock:
       use a timeout_openconn instead of openconn to connect
       to the forwarder
       WARNING you must include sockettimeout.repy to use this

      
  <Returns>
     A socket-like object that can be used for communication. 
     Use send, recv, and close just like you would an actual socket object in python.
  """ 
  # cast the destmac to a string, internal methods may fail otherwise
  destmac = str(destmac)

  # use the forwarderIP and port provided
  if forwarderIP != None and forwarderPort != None:
    return _nat_try_connection_list([(forwarderIP,forwarderPort)],
                                            localip,localport,timeout,destmac,destport,usetimeoutsock)  
    
  
  # lookup the destmac if forwarderIP and port are not provided
  else:  
    # check the cache
    if destmac in NAT_SRV_CACHE:
      forwarders = NAT_SRV_CACHE[destmac]
      
      try:
        return _nat_try_connection_list(forwarders,localip,localport,timeout,destmac,destport,usetimeoutsock)
        
      except:  # remove this entry from the cache
        del NAT_SRV_CACHE[destmac]        
      
    # the cache failed, so do a fresh lookup
    forwarders = nat_server_list_lookup(destmac)
    socket = _nat_try_connection_list(forwarders,localip,localport,timeout,destmac,destport,usetimeoutsock)
    
    #this list succeded so add it to the cache
    NAT_SRV_CACHE[destmac] = forwarders
 
    return socket




def _nat_try_connection_list(forwarders,localip,localport,timeout,destmac,destport,usetimeoutsock):
  # try to connect to every forwarder listed until we suceed
  # or run out of forwarders
  connected = False
  exception_list = [] # we might accumulate several exceptions trying to connect
                      # to various forwarders to find the destmac
  
  for (ip,port) in forwarders:

    # Create a real connection to the forwarder
    try:
      if usetimeoutsock:
        socket = timeout_openconn(ip, int(port), localip, localport, timeout)
      else:
        socket = openconn(ip, int(port), localip, localport, timeout)
    except Exception, e:
      # try the next forwarder listed
      exception_list.append(str(e))
    else:
      # we connected to a forwarder
      connected = True
      
      try:  #Catch any exceptions and try the next forwarder if we fail
        socket.send('C') #tell the forwarder this is a client
    
        # Create an RPC request to connect to the desired server
        rpc_dict = {RPC_FUNCTION:RPC_CLIENT_INIT,
                    RPC_PARAM:{"server":destmac,"port":destport}}

        # Send the RPC request
        socket.send(RPC_encode(rpc_dict)) 

        # Get the response
        response = RPC_decode(socket)
  
        # Check the response 
        if response[RPC_RESULT] == NAT_STATUS_CONFIRMED:
          # Everything is good to go
          return socket
  
        # Handle no server at the forwarder  
        elif response[RPC_RESULT] == NAT_STATUS_NO_SERVER:
            raise EnvironmentError, "Connection Refused! No server at the forwarder!"
    
        # Handle busy forwarder
        elif response[RPC_RESULT] == NAT_STATUS_BSY_SERVER:
            raise EnvironmentError, "Connection Refused! Forwarder Busy."
      
      except Exception, e:
        exception_list.append(str(e))
          

  # General error     
  raise EnvironmentError, "Connection Refused! "+str(exception_list)  




 


 





# Private method to request a function on the forwarder and
# return the result
def _nat_rpc_call(mux, rpc_dict):
  # Get a virtual socket
  rpcsocket = mux.openconn(RPC_VIRTUAL_IP, RPC_VIRTUAL_PORT)
  
  # Get message encoding
  rpc_mesg = RPC_encode(rpc_dict)
  
  # Request, get the response
  rpcsocket.send(rpc_mesg)
  response = RPC_decode(rpcsocket,blocking=True)
  
  # Close the socket
  try:
    rpcsocket.close()
  except:
    pass
  
  # Return the status  
  return response[RPC_REQUEST_STATUS]
  


# Does an RPC call to the forwarder to register a port
def _nat_reg_port_rpc(mux, mac, port):
  rpc_dict = {RPC_REQUEST_ID:1,RPC_FUNCTION:RPC_REGISTER_PORT,RPC_PARAM:{"server":mac,"port":port}}
  return _nat_rpc_call(mux,rpc_dict)


# Does an RPC call to the forwarder to deregister a port
def _nat_dereg_port_rpc(mux, mac, port):
  rpc_dict = {RPC_REQUEST_ID:2,RPC_FUNCTION:RPC_DEREGISTER_PORT,RPC_PARAM:{"server":mac,"port":port}}
  return _nat_rpc_call(mux,rpc_dict)


# Does an RPC call to the forwarder to register a server
def _nat_reg_server_rpc(mux, mac):
  rpc_dict = {RPC_REQUEST_ID:3,RPC_FUNCTION:RPC_REGISTER_SERVER,RPC_PARAM:mac}
  return _nat_rpc_call(mux,rpc_dict)


# Does an RPC call to the forwarder to deregister a server
def _nat_dereg_server_rpc(mux, mac):
  rpc_dict = {RPC_REQUEST_ID:4,RPC_FUNCTION:RPC_DEREGISTER_SERVER,RPC_PARAM:mac}
  try:
    _nat_rpc_call(mux,rpc_dict)  
  except:
    pass # we expect an Exception to occur when the server is deregistered

# Simple wrapper function to determine if we are still waiting
# e.g. if the multiplexer is still alive
def nat_waitforconn_alive():
  """
  <Purpose>
    Informs the caller of the current state of the NAT waitforconn.
    
  <Returns>
    True if the connection to the forwarder is established and alive, False otherwise.    
  """
  return NAT_STATE_DATA["mux"] != None and NAT_STATE_DATA["mux"].isAlive()
  

# Wrapper function around the NATLayer for servers  
def nat_waitforconn(localmac, localport, function, forwarderIP=None, forwarderPort=None, forwarderCltPort=None, errdel=None,persist=True):
  """
  <Purpose>
    Allows a server to accept connections from behind a NAT.
    
  <Arguments>
    See wait for conn.

    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      All forwarder information must be specified if this is set.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      All forwarder information must be specified if this is set.           
  
    forwarderCltPort:
      The port for clients to connect to on the explicitly specified forwarder.
      All forwarder information must be specified if this is set.
      
    errdel:
      Sets the Error Delegate for the underlying multiplexer. See Multiplexer.setErrorDelegate.
      Argument should be a function pointer, the function should take 3 parameters, (mux, location, exception)
      
    persist:
      If set to true the natlayer will reconnect to another forwarder in the
      case of failure, this is the recommeneded default 

  <Side Effects>
    An event will be used to monitor new connections
    If persist is true an event is used to check forwarder connection    

  <Returns>
    A handle, this can be used with nat_stopcomm to stop listening.      
  """  
  # cast the localmac to a str, internal methods may fail otherwise
  localmac = str(localmac)

  # Check if our current mux is dead (if it exists)
  if NAT_STATE_DATA["mux"] != None and not NAT_STATE_DATA["mux"].isAlive():
    # Delete the mux
    NAT_STATE_DATA["mux"] = None
    nat_isalive() # deletes all mux state
  


  # Use the exisiting mux (if there is one)
  if NAT_STATE_DATA["mux"] != None:
    try:
      # try to connectin with the existing mux
      return _nat_register_server_with_forwarder(localmac,
                            localport,function,errdel,persist)
    except:
      # the mux is dead, so we need to drop it and make a new one  
      NAT_STATE_DATA['mux'] = None
      nat_isalive() # deletes all mux state

  
  # make a new forwarder connection and a new mux

  # Get a forwarder to use
  if forwarderIP == None or forwarderPort == None or forwarderCltPort == None:
    forwarders_list = nat_forwarder_list_lookup()
  else:
    forwarders_list = [(forwarderIP, forwarderPort, forwarderCltPort)]

  # do this until we get a connection or run out of forwarders
  connected = False
  for (forwarderIP, forwarderPort, forwarderCltPort) in forwarders_list:
        
    try:  
      # Create a real connection to the forwarder
      socket = openconn(forwarderIP, int(forwarderPort))
      socket.send('S') # tell the forwarder this is a server
      _nat_wait_establish_mux(socket,forwarderIP,forwarderPort,
                                 forwarderCltPort,localport)
      return _nat_register_server_with_forwarder(localmac,
                             localport,function,errdel,persist)
    except:
      pass # do nothing and try the next forwarder
    else:
      # we got a connection so stop looping
     connected = True      
     break
    
  if not connected:
    raise EnvironmentError, "Failed to connect to a forwarder."
     
  
    
def _nat_wait_establish_mux(socket,forwarderIP,forwarderPort,
                            forwarderCltPort,localport):
# create a new mux with the forwarder
    
    # Save this information
    NAT_STATE_DATA["forwarderIP"] = forwarderIP
    NAT_STATE_DATA["forwarderPort"] = forwarderPort
    NAT_STATE_DATA["forwarderCltPort"] = forwarderCltPort


    # Immediately create a multiplexer from this connection
    mux = Multiplexer(socket, {"localip":getmyip(), "localport":localport})

    # Stall for a while then check the status of the mux
    sleep(NAT_MUX_STALL)
    
    # If the mux is no longer initialized, or never could initialize, then raise an exception
    if not mux.isAlive():
      raise EnvironmentError, "Failed to begin listening!"
    
    # Add the multiplexer to our state
    NAT_STATE_DATA["mux"] = mux
  
    
    


def _nat_register_server_with_forwarder(localmac,localport,function,
                                        errdel,persist):
# register a server with the forwarder on an existing mux
  mux = NAT_STATE_DATA["mux"]

  # If the error delegate is assigned, set up error delegation
  if errdel != None:
    mux.setErrorDelegate(errdel)
        
  # Register us as a server, if necessary
  if not localmac in NAT_LISTEN_PORTS:
    success = _nat_reg_server_rpc(mux, localmac)
    if success:
      # Create a set for the ports
      NAT_LISTEN_PORTS[localmac] = set()
      
      # Setup an advertisement
      nat_server_advertise(localmac, NAT_STATE_DATA["forwarderIP"], NAT_STATE_DATA["forwarderCltPort"])
      nat_toggle_advertisement(True)
    
    else:
      # Something is wrong, raise Exception
      raise EnvironmentError, "Failed to begin listening!"
      
  # Setup the waitforconn
  mux.waitforconn(localmac, localport, function)

  # Register our wait port on the forwarder, if necessary
  if not localport in NAT_LISTEN_PORTS[localmac]:
    success = _nat_reg_port_rpc(mux, localmac, localport)
    if success:
      # Register this port
      NAT_LISTEN_PORTS[localmac].add(localport)
    else:
      # Something is wrong, raise Exception
      raise EnvironmentError, "Failed to begin listening!"
   

  # Setup a function to check that the waitforconn is still
  # functioning, and peroform a new waitforconn if its now
  if persist:
    settimer(10,nat_persist,[localmac, localport, function, errdel])
 
 
  # Return the localmac and localport, for stopcomm
  return (localmac,localport)
  

# Private method to make nat_waitforconn persist across
# forwarder errors.
# if the forwarder or mux fails redo the waitforconn unless
# stopcomm has been called   
def nat_persist(localmac, localport, function, errdel):
  
  # WHILE STOPCOMM HAS NOT BEEN CALLED 
  while True:
    NAT_STOP_LOCK.acquire()  #prevent race with stopcomm
    if not (localmac in NAT_LISTEN_PORTS and 
         localport in NAT_LISTEN_PORTS[localmac]):
      NAT_STOP_LOCK.release()
      return

    if not nat_isalive():
      nat_waitforconn(localmac, localport, function,errdel)
    NAT_STOP_LOCK.release() 
    sleep(10)
  
  
    
# Private method to check to see if the nat_waitforconn is still active
# used with persist to determine if we need to connect to a new forwarder
def nat_isalive():

  # Check if our current mux is dead (if it exists)
  if NAT_STATE_DATA["mux"] == None or not NAT_STATE_DATA["mux"].isAlive():
    # Delete the mux

    for key in NAT_STATE_DATA.keys():
      del NAT_STATE_DATA[key]
    NAT_STATE_DATA["mux"] = None
    for key in NAT_LISTEN_PORTS.keys():
      del NAT_LISTEN_PORTS[key]
    
    return False
  
  return True



# Stops the socketReader for the given natcon  
def nat_stopcomm(handle):
  """
  <Purpose>
    Stops listening on a NATConnection, opened by nat_waitforconn
    
  <Arguments>
    handle:
        Handle returned by nat_waitforconn.
  
  """
  NAT_STOP_LOCK.acquire() # prevent a race with persist
  
  # Get the mux
  mux = NAT_STATE_DATA["mux"]
  
  # Check the status of the mux, is it alive?
  if mux != None and not mux.isAlive():
    # Delete the mux, and stop listening on everything
    NAT_STATE_DATA["mux"] = None
    NAT_LISTEN_PORTS.clear()
    mux = None
  
  # Unpack the handle
  (localmac, localport) = handle
  
  if mux != None and localmac in NAT_LISTEN_PORTS and localport in NAT_LISTEN_PORTS[localmac]:
    # Tell the Mux to stop listening
    mux.stopcomm(str(handle))
    
    # Cleanup
    NAT_LISTEN_PORTS[localmac].discard(localport)
  
    # De-register our port from the forwarder
    _nat_dereg_port_rpc(mux, localmac, localport)
    
    # Are we listening on any ports?
    numListen = len(NAT_LISTEN_PORTS[localmac])
    
    if numListen == 0:
      # De-register the server entirely
      _nat_dereg_server_rpc(mux, localmac)
      
      # Stop advertising
      nat_stop_server_advertise(localmac)
      
      # Cleanup
      del NAT_LISTEN_PORTS[localmac]
    
    # Are we listening as any server?
    if len(NAT_LISTEN_PORTS) == 0:
      # Close the mux, and set it to Null
      mux.close()
      NAT_STATE_DATA["mux"] = None
      
      # Disable advertisement
      nat_toggle_advertisement(False, False)
  
  NAT_STOP_LOCK.release()




# Determine if you have a bi-directional connection
def nat_check_bi_directional(localip,port,forwarderIP=None,forwarderCltPort=None):
  """
  <Purpose>
    Allows a vessel to determine if they can establish a bi-direction connection
    without use of the nat layer
  
  <Arguments>
    forwarderIP/forwarderPort:
      If None, a forwarder will be automatically selected. They can also be explicitly specified.
      forwarderPort must be a client port.
  
    localip: the ip to be used for a temporay waitforconn
    port: the port to be used for a temporary waitforconn

  <Side Effects>
    This operation will use a socket while it is running.
  
  <Returns>
    True if the client needs to use the nat layer
    False if they don't
  """
  # If we don't have an explicit forwarder, pick a random one
  if forwarderIP == None or forwarderCltPort == None:
    forwarder_list = nat_forwarder_list_lookup()
  else:
    forwarder_list = [(forwarderIP,None,forwarderCltPort)]

  connected = False
  # try this until we get a good connection or run out of forwarders
  for (forwarderIP, forwarderPort, forwarderCltPort) in forwarder_list:

    # Create a real connection to the forwarder
    try:
      rpcsocket = openconn(forwarderIP, int(forwarderCltPort))
    except Exception, e:
      print str(e)
      pass
    else:
      connected = True
      rpcsocket.send('C') #tell the forwarder this is a client
      break
    
  if not connected:
    raise EnvironmentError, "Failed to connect to forwarder. Please try again."
  
  # define an echo function to test the connection  
  def nat_echo_test(rip,remoteport,test_sock,th,lh):
    while True:
      try:
        msg = test_sock.recv(1024)
        test_sock.send(msg)
      except Exception:
        test_sock.close()
        return

  # start a listener
  handle = waitforconn(localip,port,nat_echo_test)

  # Now connect to a forwarder, and get our external ip/port
  # Create a RPC dictionary
  rpc_request = {RPC_FUNCTION:RPC_BI_DIRECTIONAL}
  rpc_request[RPC_PARAM] = {'localip':localip,'waitport':port}

  # Send the RPC message
  rpcsocket.send(RPC_encode(rpc_request))
  
  # Get the response
  response = RPC_decode(rpcsocket)
  
  # Close the socket
  rpcsocket.close()
  
  # stop the listener
  stopcomm(handle)

  # Return the IP
  return response[RPC_RESULT]



# SUPERCEEDED
# Determines if you are behind a NAT (Network-Address-Translation)
# this fuction along with get_my_external_ip have been replaced with 
# nat_check_bi_directional but remain here as it may still be of
# interest for some users.
def behind_nat(forwarderIP=None,forwarderCltPort=None):
  """
  <Purpose>
    Determines if the currently executing node is behind a Network-Address-Translation device
  
  <Arguments>
    forwarderip:
      Defaults to None. This can be set for explicitly forcing the use of a forwarder
    
    forwarderport:
      Defaults to None. This can be set for explicitly forcing the use of a port on a forwarder.
      This must be the client port, not the server port.
  
  <Exceptions>
    This may raise various network related Exceptions if not connected to the internet.
  
  <Returns>
    True if behind a nat, False otherwise.
  """
  # Get "normal" ip
  ip = getmyip()
  
  # Get external ip
  externalip = getmy_external_ip(forwarderIP, forwarderCltPort)
  
  return (ip != externalip)



# Pings a forwarder to get our external IP
# SUPERCEEDED - should not be in use
# this function and use_nat are superceeded by the new nat_check_bi_directional.
# they remain here because this function may still be of interest for some users
def getmy_external_ip(forwarderIP=None,forwarderCltPort=None):
  """
  <Purpose>
    Allows a vessel to determine its external IP address. E.g. this will differ from getmyip if you are on a NAT.
  
  <Arguments>
    forwarderIP/forwarderPort:
      If None, a forwarder will be automatically selected. They can also be explicitly specified.
      forwarderPort must be a client port.
  
  <Side Effects>
    This operation will use a socket while it is running.
  
  <Returns>
    A string IP address
  """
  # If we don't have an explicit forwarder, pick a random one
  if forwarderIP == None or forwarderCltPort == None:
    forwarder_list = nat_forwarder_list_lookup()
  else:
    forwarder_list = [(forwarderIP,None,forwarderCltPort)]

  connected = False
  # try this until we get a good connection or run out of forwarders
  for (forwarderIP, forwarderPort, forwarderCltPort) in forwarder_list:

    # Create a real connection to the forwarder
    try:
      rpcsocket = openconn(forwarderIP, int(forwarderCltPort))
    except Exception, e:
      print str(e)
      pass
    else:
      connected = True
      rpcsocket.send('C') # tell the forwarder this is a client
      break
    
  if not connected:
    raise EnvironmentError, "Failed to connect to forwarder. Please try again."
  # Now connect to a forwarder, and get our external ip/port
  # Create a RPC dictionary
  rpc_request = {RPC_FUNCTION:RPC_EXTERNAL_ADDR}
  
  # Send the RPC message
  rpcsocket.send(RPC_encode(rpc_request))
  
  # Get the response
  response = RPC_decode(rpcsocket)
  
  # Close the socket
  rpcsocket.close()
  
  # Return the IP
  return response[RPC_RESULT]["ip"]


### Automatically generated by repyhelper.py ### /home/rille/skola/labbar/mpcsn_labs/distr_lab4/NATLayer_rpc.repy
