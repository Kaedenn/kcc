#!/usr/bin/env python

class Builder(object):
  def __init__(self, string):
    self._str = string
    self._codes = {}
  
  def _build_code(self, codelist):
    return "\033[" + ";".join(codelist) + "m"
  
  def insert(self, index, code):
    while index < 0:
      index = len(self._str) + 1 + index
    if index in self._codes:
      if code not in self._codes[index]:
        self._codes[index].append(str(code))
    else:
      self._codes[index] = [str(code)]
  
  def update(self, codes):
    for i in codes:
      for c in codes[i]:
        self.insert(i, c)
  
  def result(self):
    l = list(self._str)
    for i in sorted(self._codes.keys(), reverse = True):
      l.insert(i, self._build_code(self._codes[i]))
    return "".join(l)

