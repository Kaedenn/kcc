#!/usr/bin/env python

r"""
gcc.parser: parse a line from g++'s error messages, returning all sorts of
information regarding that line.

Example usage:
  attributes = []
  for line in open("compiler_errors", "r"):
    p = Parser(line)
    attributes.append(p.parse_line())
  if attributes[0]["type"] not in (Parser.LT_ERROR, Parser.LT_WARNING,
                                   Parser.LT_MESSAGE, Parser.LT_NOTE):
    sys.stderr.write("I don't know what type of line the first line is\n")
  else:
    sys.stderr.write("File: %s\nLine: %s" % (attributes[0]["file"],
                                             attributes[0]["line"])
    sys.stderr.write("Message: %s" % attributes[0]["message"]["raw"])

The attributes dictionary has the following information:
  raw: the raw line, unaltered by any subclass
  type: type of line (either Error, Warning, Message, Note or None)
  file: file name (or an empty string if not present)
  line: line number (or -1 if not present)
  column: column number (or -1 if not present)
  message: a dictionary containing the content of the error message and other
           information about it

The message dictionary has the following information:
  raw: the raw message, without the file name, line number or column number.
  codelist: a list of strings, each containing C++ code from the error, in the
            order of discovery (left-to-right)
"""

import re

class Parser(object):
  """Parser: parse a line from g++'s error messages, returning information
  about that line.
  
  There are two ways to use this class, both giving identical results:
    p = Parser()
    attributes = []
    for line in open("compiler_errors", "r"):
      attributes.append(p.parse_line(line))
  or,
    attributes = []
    for line in open("compiler_errors", "r"):
      p = Parser(line)
      attributes.append(p.parse_line())
  """
  LT_ERROR = 1
  LT_WARNING = 2
  LT_MESSAGE = 3
  LT_NOTE = 4
  def __init__(self, line = ""):
    self._line = line
    self._basics = ["streambuf", "ofstream", "ifstream", "fstream", "filebuf",
                    "stringbuf", "ostream", "istream", "ostringstream",
                    "istringstream", "stringstream", "iostream", "ios",
                    "string"]
    self._line_groups = {"file": r"[^: ]+",
                         "sys_file": r"\/usr\/include\/[^:]+:"
                                     r"(?:[0-9]+(?:: |\,$)?)?",
                         "line": r"[0-9]+",
                         "column": r"[0-9]+",
                         "message": r".+",
                         "linker": r"\(\.[A-Za-z0-9_]+\+0x[A-Fa-f0-9_]+\)"}
    self._line_group_sep = r"(?:(?<!:):(?!:))|\,$"
    self._message_groups = {"code": u"\u2018[^\u2019]+\u2019"}
    for g in self._line_groups:
      self._line_groups[g] = r"(?P<%s>%s)" % (g, self._line_groups[g])
    for g in self._message_groups:
      self._message_groups[g] = r"(?P<%s>%s)" % (g, self._message_groups[g])
    self._attributes = {
      "raw": self._line,
      "type": None,
      "file": "",
      "line": -1,
      "column": -1,
      "message": {"raw": "", "codelist": []}
    }
  
  def _parse_message(self, segments):
    message = ": ".join(segments)
    attributes = {
      "raw": message,
      "codelist": []
    }
    codes = re.findall(self._message_groups["code"], message)
    if codes:
      for c in codes:
        code = {"raw": c[1:-1]}
        attributes["codelist"].append(code)
    elif len(segments):
      if segments[0] == "candidates are":
        code = {"raw": ":".join(segments[1:])}
        attributes["codelist"].append(code)
      else:
        code = {"raw": ":".join(segments)}
        attributes["codelist"].append(code)
    return attributes
  
  def _next_token(self, line, begin = 0):
    depth = {"<": 0, "[": 0, "{": 0, "(": 0}
    ends = {">": "<", "]": "[", "}": "{", ")": "("}
    delims = set((",", "="))
    for i, c in enumerate(line[begin:]):
      if c in delims and set(depth.values()) == set([0]):
        return line[begin:begin + i].strip()
      elif c in depth:
        depth[c] += 1
      elif c in ends:
        depth[ends[c]] -= 1
        if depth[ends[c]] < 0:
          return
  
  def parse_line(self, line = ""):
    "parse a line and return the attributes describing it"
    if line and line != self._line:
      self._line = line
    self._line = self._line.strip()
    self._attributes["raw"] = self._line
    segments = [s.strip() for s in re.split(self._line_group_sep, self._line)]
    if len(segments) == 0:
      return self._attributes
    elif len(segments) == 1:
      self._attributes["file"] = "<unknown>"
      self._attributes["type"] = Parser.LT_NOTE # safe default
      self._attributes["message"] = self._parse_message(segments)
      return self._attributes
    if "In file included from" in segments[0]:
      segments[0] = "".join(segments[0].split()[4:])
    elif segments[0][0:4] == "from":
      segments[0] = segments[0][5:]
    if segments[0] == "collect2":
      self._attributes["type"] = Parser.LT_MESSAGE
    elif re.match(self._line_groups["file"], segments[0]):
      self._attributes["file"] = segments[0]
      if re.match(self._line_groups["sys_file"], segments[0]):
        self._attributes["sys_file"] = True
      else:
        self._attributes["sys_file"] = False
      if re.match(self._line_groups["linker"], segments[1]):
        self._attributes["type"] = Parser.LT_WARNING
        self._attributes["message"] = self._parse_message(segments[2:])
      elif re.match(self._line_groups["line"], segments[1]):
        self._attributes["line"] = int(segments[1])
        if "error" in segments and len(segments) > 2:
          self._attributes["type"] = Parser.LT_ERROR
          if segments[2] == "error":
            self._attributes["message"] = self._parse_message(segments[3:])
          elif segments[3] == "error":
            if re.match(self._line_groups["column"], segments[2]):
              self._attributes["column"] = int(segments[2])
            self._attributes["message"] = self._parse_message(segments[4:])
        elif segments[2] == "warning":
          self._attributes["type"] = Parser.LT_WARNING
          self._attributes["message"] = self._parse_message(segments[3:])
        elif segments[2] == "note":
          self._attributes["type"] = Parser.LT_NOTE
          self._attributes["message"] = self._parse_message(segments[3:])
        else:
          self._attributes["type"] = Parser.LT_NOTE
          self._attributes["message"] = self._parse_message(segments[2:])
      elif re.match(self._line_groups["message"], segments[1]):
        self._attributes["type"] = Parser.LT_NOTE
        self._attributes["message"] = self._parse_message(segments[1:])
    return self._attributes

