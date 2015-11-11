# -*- coding: utf-8 -*-
### Automatically generated by repyhelper.py ### /home/rille/Skola/labbar/mpcsn_labs/distr_lab1/lab_skeleton/advanced/listops.repy

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

Module: A simple library of list commands that allow the programmer
        to do list composition operations

Start date: November 11th, 2008

This is a really simple module, only broken out to avoid duplicating 
functionality.

This was adopted from previous code in seash.   

I really should be using sets instead I think.   These are merely for 
convenience when you already have lists.

"""


def listops_difference(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in list_a that are not in list_b
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a - list_b
  """

  retlist = []
  for item in list_a:
    if item not in list_b:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)


def listops_union(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in list_a or in list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a union list_b
  """

  retlist = list_a[:]
  for item in list_b: 
    if item not in list_a:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)


def listops_intersect(list_a,list_b):
  """
   <Purpose>
      Return a list that has all of the items in both list_a and list_b.   
      Duplicates are removed from the output list

   <Arguments>
      list_a, list_b:
        The lists to operate on

   <Exceptions>
      TypeError if list_a or list_b is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing list_a intersect list_b
  """

  retlist = []
  for item in list_a:
    if item in list_b:
      retlist.append(item)

  # ensure that a duplicated item in list_a is only listed once
  return listops_uniq(retlist)
      

def listops_uniq(list_a):
  """
   <Purpose>
      Return a list that has no duplicate items

   <Arguments>
      list_a
        The list to operate on

   <Exceptions>
      TypeError if list_a is not a list.

   <Side Effects>
      None.

   <Returns>
      A list containing the unique items in list_a
  """
  retlist = []
  for item in list_a:
    if item not in retlist:
      retlist.append(item)

  return retlist



### Automatically generated by repyhelper.py ### /home/rille/Skola/labbar/mpcsn_labs/distr_lab1/lab_skeleton/advanced/listops.repy
