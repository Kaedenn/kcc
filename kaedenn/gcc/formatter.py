#!/usr/bin/env python

"""gcc.formatter: convenience module for errmsg, gcc.parser and gcc.beautifier.

This module defines a single function that wraps the features provided by
errmsg and gcc.beautifier. See the documentation for gcc.formatter.format for
more information.
"""

import os
import sys
import kaedenn.errmsg
from kaedenn.gcc.beautifier import Beautifier
from kaedenn.gcc.parser import Parser

def format(output, color = True, level = Beautifier.LV_NORMAL):
  """Format gcc's error messages, coloring and beautifying them if desired.
  
  This function tries to classify each line as either an error, warning,
  message or notification. If color is True, errors will be decorated by
  errmsg.error, warnings by errmsg.warn, messages by errmsg.message and
  notifications by errmsg.notify. If color is False or the line cannot be
  classified, the line will not be decorated.
  
  The level argument states how vigorously to beautify the error messages. See
  the documentation of the gcc.beautifier module for more information regarding
  beautification.
  """
  result = []
  color_types = {
    Parser.LT_ERROR: kaedenn.errmsg.error,
    Parser.LT_WARNING: kaedenn.errmsg.warn,
    Parser.LT_MESSAGE: kaedenn.errmsg.message,
    Parser.LT_NOTE: kaedenn.errmsg.notify,
    None: lambda s: s
  }
  for line in output.splitlines():
    b = Beautifier(line, level, wrap = '-w' in sys.argv)
    attribs = b.parse_line()
    if '-C' not in sys.argv:
      color_func = color_types[attribs["type"]]
    else:
      color_func = color_types[None]
    result_line = b.build()
    if result_line:
      if color:
        result_line = color_func(result_line)
      result.append(result_line)
  return os.linesep.join(result)

if __name__ == "__main__":
  import sys
  sys.stdout.write(format(sys.stdin.read(), level = Beautifier.LV_ALL))
  sys.stdout.write(os.linesep)

