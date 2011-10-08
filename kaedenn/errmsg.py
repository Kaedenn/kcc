#!/usr/bin/env python

"""
Colorful error message handler

Coloring Functions:
  Messages: foreground brown, background default
  Notifications: foreground blue, background default
  Warnings: foreground green, background default
  Errors: foreground red, background default
"""

from kaedenn.colors import Builder, Codes

def highlight_line(string, color):
  b = Builder(string)
  b.insert(0, color)
  b.insert(-1, Codes.RESET)
  return b.result()

message = lambda msg: highlight_line(msg, Codes.BROWN)
notify = lambda msg: highlight_line(msg, Codes.BLUE)
warn = lambda msg: highlight_line(msg, Codes.GREEN)
error = lambda msg: highlight_line(msg, Codes.RED)

