# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

#import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os, urllib2, string, re, htmlentitydefs, time, unicodedata

from xml.sax.saxutils import unescape
from xml.dom import minidom
from urllib import quote_plus

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Icecast"
__addonid__      = "plugin.audio.icecast"
__author__	= "Assen Totin <assen.totin@gmail.com>"
__credits__        = "Team XBMC"

BASE_URL = 'http://dir.xiph.org/yp.xml'

CHUNK_SIZE = 65536

# Parse XML line
def getText(nodelist):
  rc = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      rc.append(node.data)
  return ''.join(rc)

# Read the XML list from IceCast server
def readRemoteXML():
  # Create a dialog
  global dialog_was_canceled
  dialog = xbmcgui.DialogProgress()
  dialog.create(__language__(30093), __language__(30094))
  dialog.update(1)

  # Download in chunks of CHUNK_SIZE, update the dialog
  # URL progress bar code taken from triptych (http://stackoverflow.com/users/43089/triptych):
  # See original code http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
  response = urllib2.urlopen(BASE_URL);
  total_size = response.info().getheader('Content-Length').strip()
  total_size = int(total_size)
  bytes_so_far = 0
  str_list = []
  xml = ''

  while 1:
    chunk = response.read(CHUNK_SIZE)
    bytes_so_far += len(chunk)

    if not chunk: break

    if (dialog.iscanceled()):
      dialog_was_canceled = 1
      break

    # There are two a bit faster ways to do this: pseudo files (not sure how portable?) and list comprehensions (lazy about it).
    # As the performance penalty is not that big, I'll stay with the more straightforward: list + join
    str_list.append(chunk)

    percent = float(bytes_so_far) / total_size
    val = int(percent * 100)
    dialog.update(val)

  response.close()

  if dialog_was_canceled == 0:
    xml = ''.join(str_list)
    dialog.update(100)
    time.sleep(1)

  dialog.close
  return xml

