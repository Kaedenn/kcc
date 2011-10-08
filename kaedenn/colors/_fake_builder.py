#!/usr/bin/env python

class Builder(object):
  """
  Default Builder object, which doesn't color anything. result() simply returns
  the specified string unchanged. This is for a sane default implementation.
  """
  def __init__(self, string):
    self._str = string
    self._codes = {}
  
  def insert(self, index, code):
    pass
  
  def update(self, codes):
    pass
  
  def result(self):
    return self._str

