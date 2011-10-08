#!/usr/bin/env python

r"""gcc.beautifier: beautify gcc's error messages.

Since g++'s errors are notoriously hard to understand for novice programmers,
I wrote this module to simplify the errors.

There are four levels of beautification: Normal, Moderate, High and All. Each
level of beautification corresponds to the following actions:

Normal:
* Remove "with-statements" from error messages, replacing template parameters
  with their actual types, as stated in the "with-statement".
    Examples:
      Type<T> [with T = int]
        becomes
      Type<int>
      
      Type<T, U> [with T = int, U = char]
        becomes
      Type<int, char>

* Remove the "std::" prefix on standard types, such as "vector" or "string".

* Shorten templates just slightly by removing the space between ">" characters.
    Example:
      Type<T, U<V> >
        becomes
      Type<T, U<V>>

* Shorten known typedefs for the character-based and stream types. This works
  for both "char" and "wchar_t" variations.
    Examples:
      basic_string<char, char_traits<char>, allocator<char>>
        becomes
      string
      
      basic_iostream<char, char_traits<char>>
        becomes
      istream

* Remove known default template arguments for various standard containers.
    Examples:
      vector<T, allocator<T>>
        becomes
      vector<T>
      
      stack<T, deque<T, allocator<T>>>
        becomes
      stack<T>

Moderate:
* If the file name in an error message is a system file, remove it, along with
  the line number. Normally, this information is useless as these files rarely
  cause compiler errors. Lines containing these file names are typically either
  errors caused by something else, or notes to the user.
    Example:
      /usr/include/c++/4.4/bits/stl_vector.h:733: note: candidates are: void 
      vector<int>::push_back(const int&)
        becomes
      note: candidates are: void vector<int>::push_back(const int&)

High:
* Currently, this is the same as Moderate. No further modifications are made in
  this mode.

All:
* Currently, this is the same as High. No further modifications are made in
  this mode.

Lastly, error messages are word-wrapped to fit on an eighty-column display, to
prevent line breaks in the middle of a word. Some terminals don't handle
word-wrapping too nicely, especially if the error messages are printed in
colors. Subsequent wrapped lines are prefixed with a tab "\t" character.

See the documentation for the Beautifier class for a usage example.
"""

import os
import re
import textwrap
import kaedenn.gcc.parser

class Beautifier(kaedenn.gcc.parser.Parser):
  """
  Beautify (format) errors given by g++ to something more readable
  
  This class works on a line-by-line basis. Example use:
  
  for line in open("compiler_errors", "r"):
    b = Beautifier(line, Beautifier.LV_MODERATE)
    b.parse_line()
    sys.stderr.write("%s\n" % b.build())
  """
  LV_NONE = 0
  LV_NORMAL = 1
  LV_MODERATE = 2
  LV_HIGH = 3
  LV_ALL = 4
  def __init__(self, line, level = LV_MODERATE, width = 72, wrap = True):
    super(Beautifier, self).__init__(line)
    self._level = level
    self._width = width
    self._result = line
    if wrap:
      self._wrapper = textwrap.TextWrapper(width, subsequent_indent = "    ")
    else:
      self._wrapper = None
    self._str_types = {
      "basic_ios<%s, char_traits<%s>>": "ios",
      "basic_streambuf<%s, char_traits<%s>>": "streambuf",
      "basic_istream<%s, char_traits<%s>>": "istream",
      "basic_ostream<%s, char_traits<%s>>": "ostream",
      "basic_iostream<%s, char_traits<%s>>": "iostream",
      "basic_ifstream<%s, char_traits<%s>>": "ifstream",
      "basic_ofstream<%s, char_traits<%s>>": "ofstream",
      "basic_fstream<%s, char_traits<%s>>": "fstream",
      "basic_istringstream<%s, char_traits<%s>, allocator<%s>>": "istringstream",
      "basic_ostringstream<%s, char_traits<%s>, allocator<%s>>": "ostringstream",
      "basic_stringstream<%s, char_traits<%s>, allocator<%s>>": "stringstream",
      "basic_string<%s, char_traits<%s>, allocator<%s>>": "string"
    }
    self._replacements = {
      "vector": (
        ("vector<%s, allocator<%s>>", "vector<%s>"),
        ("typename vector<%s>::value_type", "%s")
      ),
      "list": (
        ("list<%s, allocator<%s>>", "list<%s>"),
        ("typename list<%s>::value_type", "%s")
      ),
      "queue": (
        ("queue<%s, deque<%s>>", "queue<%s>"),
        ("typename queue<%s>::value_type", "%s")
      ),
      "deque": (
        ("deque<%s, allocator<%s>>", "deque<%s>"),
        ("typename deque<%s>::value_type", "%s")
      ),
      "stack": (
        ("stack<%s, deque<%s>>", "stack<%s>"),
        ("typename stack<%s>::value_type", "%s")
      ),
      "set": (
        ("set<%s, less<%s>, allocator<%s>>", "set<%s>"),
        ("typename set<%s>::value_type", "%s")
      )
    }
    self._char_types = ("char", "wchar_t")
    self._with_stmt = r"\[with\s*(?P<with>[^\]]+)\]"
  
  def _parse_with_stmts(self, code):
    match = re.search(self._with_stmt, code)
    tokens = []
    if match:
      stmt = match.groupdict()["with"]
      depth = {"<": 0, "[": 0, "{": 0, "(": 0}
      ends = {">": "<", "]": "[", "}": "{", ")": "("}
      begin = 0
      for i, c in enumerate(stmt + ","):
        if c == "," and set(depth.values()) == set([0]):
          key, value = stmt[begin:i].split("=")
          key = key.strip()
          value = value.strip()
          tokens.append((key, value))
          begin = i + 1
        elif c in depth:
          depth[c] += 1
        elif c in ends:
          depth[ends[c]] -= 1
    return tokens
  
  def _compact_typedefs(self, message):
    for t in self._str_types:
      for c in self._char_types:
        tp = t.replace("%s", c)
        if tp in message:
          r = self._str_types[t]
          if c[0] == "w":
            r = "w" + r
          message = message.replace(tp, r)
    return message
  
  def _parse_templates(self, message):
    for container in self._replacements:
      if container in message:
        begin = message.find(container) + len(container) + 1
        tp = self._next_token(message, begin)
        if tp:
          for full, small in self._replacements[container]:
            full = full.replace("%s", tp)
            small = small.replace("%s", tp)
            message = message.replace(full, small)
    return message
  
  def _parse_message(self, segments):
    attributes = super(Beautifier, self)._parse_message(segments)
    for code in attributes["codelist"]:
      code["with_tokens"] = self._parse_with_stmts(code["raw"])
    return attributes
  
  def build(self):
    "apply beautification to the line and return the result"
    if self._level == Beautifier.LV_NONE: return self._result
    for code in self._attributes["message"]["codelist"]:
      if "formatted" not in code:
        code["formatted"] = code["raw"]
      if self._level >= Beautifier.LV_NORMAL:
        if "with_tokens" in code:
          for key, value in code["with_tokens"]:
            # TODO: make the replacements not clobber things
            code["formatted"] = code["formatted"].replace(key, value)
          code["formatted"] = re.sub(self._with_stmt, "", code["formatted"])
          code["formatted"] = code["formatted"].strip()
        while "> >" in code["formatted"]:
          code["formatted"] = code["formatted"].replace("> >", ">>")
        code["formatted"] = code["formatted"].replace("std::", "")
        code["formatted"] = code["formatted"].replace("__gnu_cxx::", "")
        code["formatted"] = self._compact_typedefs(code["formatted"])
        code["formatted"] = self._parse_templates(code["formatted"])
      if self._level >= Beautifier.LV_MODERATE:
        self._result = re.sub(self._line_groups["sys_file"], "", self._result)
        if self._result.startswith("error: "):
          return ""
        code["formatted"] = code["formatted"].replace("boost::detail::", "")
        code["formatted"] = code["formatted"].replace("boost::", "")
      self._result = self._result.replace(code["raw"], code["formatted"])
    self._result = self._result.strip()
    if self._wrapper is not None:
      self._result = self._wrapper.fill(self._result)
    for prefix in ("from", "note: previous definition", "In file included from"):
      if self._result.startswith(prefix):
        return ""
    return self._result

