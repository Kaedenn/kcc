#!/usr/bin/env python

import os
if os.name == "posix" or os.name == "mac":
  import _posix_codes as Codes
  from _posix_builder import Builder
else:
  import _fake_codes as Codes
  from _fake_builder import Builder

def color(string, *colors):
  b = Builder(string)
  for color in colors:
    b.insert(0, color)
  return b.result()

def color_only(string, *colors):
  b = Builder(string)
  for color in colors:
    b.insert(0, color)
  b.insert(-1, Codes.RESET)
  return b.result()

