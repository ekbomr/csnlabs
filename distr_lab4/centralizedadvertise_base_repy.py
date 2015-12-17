# -*- coding: utf-8 -*-
### Automatically generated by repyhelper.py ### /home/simon/dev/csnlabs/distr_lab4/centralizedadvertise_base.repy

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
Author: Justin Cappos

Start Date: July 8, 2008

Description:
Advertisements to a central server (similar to openDHT)


"""

repyhelper.translate_and_import('session.repy')
# I'll use socket timeout to prevent hanging when it takes a long time...
repyhelper.translate_and_import('sockettimeout.repy')
repyhelper.translate_and_import('serialize.repy')


class CentralAdvertiseError(Exception):
  """Error when advertising a value to the central advertise service."""

def centralizedadvertisebase_announce(servername, serverport, key, value, ttlval):
  """
   <Purpose>
     Announce a key / value pair into the CHT.

   <Arguments>
     servername: the server ip/name to contact.  Must be a string.

     serverport: the server port to contact.  Must be an integer.

     key: the key to put the value under. This will be converted to a string.

     value: the value to store at the key. This is also converted to a string.

     ttlval: the amount of time until the value expires.   Must be an integer

   <Exceptions>
     TypeError if ttlval is of the wrong type.

     ValueError if ttlval is not positive 

     CentralAdvertiseError is raised the server response is corrupted

     Various network and timeout exceptions are raised by timeout_openconn
     and session_sendmessage / session_recvmessage

   <Side Effects>
     The CHT will store the key / value pair.

   <Returns>
     None
  """
  # do basic argument checking / munging
  key = str(key)
  value = str(value)

  if not type(ttlval) is int and not type(ttlval) is long:
    raise TypeError("Invalid type '"+str(type(ttlval))+"' for ttlval.")

  if ttlval < 1:
    raise ValueError("The argument ttlval must be positive, not '"+str(ttlval)+"'")

  
  # build the tuple to send, then convert to a string because only strings
  # (bytes) can be transmitted over the network...
  datatosend = ('PUT',key,value,ttlval)
  datastringtosend = serialize_serializedata(datatosend)

  
  # send the data over a timeout socket using the session library, then
  # get a response from the server.
  sockobj = timeout_openconn(servername,serverport, timeout=10)
  try:
    session_sendmessage(sockobj, datastringtosend)
    rawresponse = session_recvmessage(sockobj)
  finally:
    # BUG: This raises an error right now if the call times out ( #260 )
    # This isn't a big problem, but it is the "wrong" exception
    sockobj.close()
  
  # We should check that the response is 'OK'
  try:
    response = serialize_deserializedata(rawresponse)
    if response != 'OK':
      raise CentralAdvertiseError("Centralized announce failed with '"+response+"'")
  except ValueError, e:
    raise CentralAdvertiseError("Received unknown response from server '"+rawresponse+"'")
      



def centralizedadvertisebase_lookup(servername, serverport, key, maxvals=100):
  """
   <Purpose>
     Returns a list of valid values stored under a key

   <Arguments>
     servername: the server ip/name to contact.  Must be a string.

     serverport: the server port to contact.  Must be an integer.

     key: the key to put the value under. This will be converted to a string.

     maxvals: the maximum number of values to return.   Must be an integer

   <Exceptions>
     TypeError if maxvals is of the wrong type.

     ValueError if maxvals is not a positive number

     CentralAdvertiseError is raised the server response is corrupted

     Various network and timeout exceptions are raised by timeout_openconn
     and session_sendmessage / session_recvmessage

   <Side Effects>
     None

   <Returns>
     The list of values
  """

  # do basic argument checking / munging
  key = str(key)

  if not type(maxvals) is int and not type(maxvals) is long:
    raise TypeError("Invalid type '"+str(type(maxvals))+"' for ttlval.")

  if maxvals < 1:
    raise ValueError("The argument ttlval must be positive, not '"+str(ttlval)+"'")

  # build the tuple to send, then convert to a string because only strings
  # (bytes) can be transmitted over the network...
  messagetosend = ('GET',key,maxvals)
  messagestringtosend = serialize_serializedata(messagetosend)


  sockobj = timeout_openconn(servername,serverport, timeout=10)
  try:
    session_sendmessage(sockobj, messagestringtosend)
    rawreceiveddata = session_recvmessage(sockobj)
  finally:
    # BUG: This raises an error right now if the call times out ( #260 )
    # This isn't a big problem, but it is the "wrong" exception
    sockobj.close()


  try:
    responsetuple = serialize_deserializedata(rawreceiveddata)
  except ValueError, e:
    raise CentralAdvertiseError("Received unknown response from server '"+rawresponse+"'")

  # For a set of values, 'a','b','c',  I should see the response: 
  # ('OK', ['a','b','c'])    Anything else is WRONG!!!
  
  if not type(responsetuple) is tuple:
    raise CentralAdvertiseError("Received data is not a tuple '"+rawresponse+"'")

  if len(responsetuple) != 2:
    raise CentralAdvertiseError("Response tuple did not have exactly two elements '"+rawresponse+"'")
  if responsetuple[0] != 'OK':
    raise CentralAdvertiseError("Central server returns error '"+str(responsetuple)+"'")

  
  if not type(responsetuple[1]) is list:
    raise CentralAdvertiseError("Received item is not a list '"+rawresponse+"'")

  for responseitem in responsetuple[1]:
    if not type(responseitem) is str:
      raise CentralAdvertiseError("Received item '"+str(responseitem)+"' is not a string in '"+rawresponse+"'")

  # okay, we *finally* seem to have what we expect...

  return responsetuple[1]

### Automatically generated by repyhelper.py ### /home/simon/dev/csnlabs/distr_lab4/centralizedadvertise_base.repy
