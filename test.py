import logging
logging.getLogger().setLevel(logging.DEBUG)

from pyac import AC
a = AC()

print a.getPower()
