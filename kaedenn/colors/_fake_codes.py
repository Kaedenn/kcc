#!/usr/bin/env python

"""
Default set of codes, having no value other than enumeration and sane defualts.
"""

_counter = -1
def _count():
  global _counter
  _counter += 1
  return _counter

# special control codes
RESET = _count()

# foreground colors
WHITE = _count()
BLACK = _count()
RED = _count()
BROWN = _count()
ORANGE = _count()
YELLOW = _count()
GREEN = _count()
BLUE = _count()
CYAN = _count()
MAGENTA = _count()
DEFAULT = _count()

# background colors
WHITE_BG = _count()
BLACK_BG = _count()
RED_BG = _count()
BROWN_BG = _count()
ORANGE_BG = _count()
YELLOW_BG = _count()
GREEN_BG = _count()
BLUE_BG = _count()
CYAN_BG = _count()
MAGENTA_BG = _count()
DEFAULT_BG = _count()

# other attributes
BOLD = _count()
BOLD_OFF = _count()
UNDERLINE = _count()
UNDERLINE_OFF = _count()
BLINK = _count()
BLINK_OFF = _count()

