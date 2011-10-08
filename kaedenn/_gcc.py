#!/usr/bin/env python

"""
Perform operations on gcc's output to make it easier to read and understand.
"""

import re
import sys
from kaedenn.colors import Builder, Codes
import kaedenn.errmsg
import kaedenn.gcc

def _decorate(line, func, *args, **kwargs):
  return func(line)

def _error(line, *args, **kwargs):
  return _decorate(line, kaedenn.errmsg.error, *args, **kwargs)

def _warn(line, *args, **kwargs):
  return _decorate(line, kaedenn.errmsg.warn, *args, **kwargs)

def _message(line, *args, **kwargs):
  return _decorate(line, kaedenn.errmsg.message, *args, **kwargs)

def _notify(line, *args, **kwargs):
  return _decorate(line, kaedenn.errmsg.notify, *args, **kwargs)

def color(output):
  return kaedenn.gcc.color(output)
  FILE = r"\s*(?P<file>[^: ]+)"
  LINE = r"(?P<line>[0-9]+)"
  COL = r"(?P<col>[0-9]+)"
  MSG = "(?P<msg>.+)"
  LINK = r"(?P<link>\(\.[0-9a-zA-Z_]+\+0x[0-9A-Fa-f]+\))"
  SEP = r"\s*:\s*"
  
  if sys.platform == "win32":
    lines = output.decode("UTF-16", "replace").splitlines()
  else:
    lines = output.decode("UTF-8", "replace").splitlines()
  
  def cat(*args):
    return SEP.join(args)
  
  rules = (
    ("^" + cat(FILE, LINE, COL, "error", MSG), _error),
    ("^" + cat(FILE, LINE, "note", MSG), _notify),
    ("^" + cat(FILE, LINK, MSG), _warn),
    ("^" + cat(FILE, LINE, "warning", MSG), _warn),
    ("^" + cat(FILE, LINE, "error", MSG), _error),
    ("^" + cat(FILE, LINE, MSG), _message),
    (cat("collect2", MSG), _message),
    ("^" + cat(FILE, MSG), _notify),
    (r"^(In file included)?\s*from " + cat(FILE, LINE), _notify)
  )
  
  result = []
  for line in lines:
    for regex, func in rules:
      m = re.match(regex, line)
      if m:
        result.append(func(line, match = m))
        break
    else:
      result.append(line)
  
  if sys.platform == "win32":
    return "\n".join(result).encode("UTF-16", "ignore")
  else:
    return "\n".join(result).encode("UTF-8", "ignore")

def _beautify_standard_types(output, level):
  """
  * level 1
  *) remove std::
  *) remove char_traits<T>, allocator<T> from containers
  *) remove "basic_" from IO and character-handling types
  * level 2
  *) remove reserved identifiers from template arguments
  *) remove with-statements
  *) remove reserved identifiers in comma-delimited lists
  * level 3
  *) remove file names for files inside /usr/include
  """
  containers = ["list", "deque", "vector", "set", "multiset", "map", "multimap",
                "queue", "stack"]
  basics = ["streambuf", "ofstream", "ifstream", "fstream", "filebuf",
            "stringbuf", "ostream", "istream", "ostringstream", "istringstream",
            "stringstream", "iostream", "ios", "string"]
  self_cast = r"\(\((?P<ctype>[^\)])+\)this)\-\>"
  removals = {2: [r"\,?\s+char_traits\s*\<[A-Za-z0-9_ ]+\s*\>\s*",
                  r"\,?\s+allocator\s*\<[A-Za-z0-9_ ]+\s*\>\s*",
                  r"\,\s+_[A-Z][A-Za-z0-9_ ]+\s*",
                  r"\[with\s*[^\]]+\]",
                  r"\<(,?\s*_[A-Z][A-Za-z0-9_ ]+)+\>"],
              3: [r"\/usr\/include\/[^: ]+\s*:\s*[0-9]+\s*:\s*"]}
  if level >= 1:
    output = output.replace("std::", "")
    for t in basics:
      output = output.replace("basic_" + t, t)
  for l in removals:
    if level >= l:
      for i in removals[l]:
        output = re.sub(i, "", output)
  return output

def beautify(err, level = 1):
  err = err.decode("UTF-8")
  result = []
  for line in err.splitlines():
    result.append(kaedenn.gcc.beautify(line, level))
  return "\n".join(result).encode("UTF-8")
  enqu = unichr(0x2018)
  dequ = unichr(0x2019)
  output = _beautify_standard_types(err, level)
  return output.encode("UTF-8")

