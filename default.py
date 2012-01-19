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

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
#import os, urllib2, string, re, htmlentitydefs, time, unicodedata

#from xml.sax.saxutils import unescape
#from xml.dom import minidom
#from urllib import quote_plus

from icecast_common import *

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Icecast"
__addonid__      = "plugin.audio.icecast"
__author__	= "Assen Totin <assen.totin@gmail.com>"
__credits__        = "Team XBMC"

# SQLite support - if available
try:
  # First, try built-in sqlite in Python 2.5 and newer:
  from sqlite3 import dbapi2 as sqlite
  log_notice("Using built-in SQLite via sqlite3!")
  use_sqlite = 1
except:
  # No luck so far: try the external sqlite
  try:
    from pysqlite2 import dbapi2 as sqlite
    log_notice("Using external SQLite via pysqlite2!")
    use_sqlite = 1
  except: 
    use_sqlite = 0
    log_notice("SQLite not found -- reverting to older (and slower) text cache.")

params=getParams()

try:
  genre = params["genre"]
except:
  genre = "0";
try:
  mode = params["mode"]
except:
  mode = "0";
try:
  url = params["url"]
except:
  url = "0";
try:
  settings = params["settings"]
except:
  settings = "0";
try:
  val = params["val"]
except:
  val = "0";
try:
  mod_recent = params["mod_recent"]
except:
  mod_recent = 0

igenre = len(genre)
iplay = len(play)
imode = len(initial)
isettings = len(settings)

dialog_was_canceled = 0

if use_sqlite == 1:
  from icecast_sql import *
  sqlite_con, sqlite_cur, sqlite_is_empty = initSQLite()
  timestamp_expired = timestampExpired(sqlite_cur)
  if (sqlite_is_empty == 1) or (timestamp_expired == 1):
    xml = readRemoteXML()
    if dialog_was_canceled == 0:
      dom = parseXML(xml)
      DOMtoSQLite(dom, sqlite_con, sqlite_cur)
      putTimestamp(sqlite_con, sqlite_cur)

elif use_sqlite == 0:
  from icecast_dom import * 
  timestamp_expired = timestampExpired()
  if timestamp_expired == 1:
    xml = readRemoteXML()
    if dialog_was_canceled == 0:
      writeLocalXML(xml)
      putTimestamp()
  elif timestamp_expired == 0:
    xml = readLocalXML()
  dom = parseXML(xml)

# Mode selector
if mode == "search":
  query = readKbd()
  if use_sqlite == 1:
    doSearch(sqlite_cur, query)
  else:
    doSearch(dom, query)
  sort()

elif mode == "list":
  if use_sqlite == 1:
    buildGenreList(sqlite_cur)
  else:
    buildGenreList(dom)
  sort(True)

elif mode == "genre":
  if use_sqlite == 1:
    timestamp_expired = timestampExpired(sqlite_cur)
    if timestamp_expired == 1:
      xml = readRemoteXML()
      if dialog_was_canceled == 0:
        dom = parseXML(xml)
        DOMtoSQLite(dom, sqlite_con, sqlite_cur)
        putTimestamp(sqlite_con, sqlite_cur)
    buildLinkList(sqlite_cur, genre)
  else:
    timestamp_expired = timestampExpired()
    if timestamp_expired == 1:
      xml = readRemoteXML()
      if dialog_was_canceled == 0:
        writeLocalXML(xml)
        putTimestamp()
    else:
      xml = readLocalXML()
    dom = parseXML(xml)
    buildLinkList(dom, genre)
  sort()

elif mode == "settings":
  if use_sqlite == 1:
    if isettings > 0:
      updateSettings(sqlite_con, sqlite_cur, settings, val)
    showSettings(sqlite_cur)
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok(__language__(30101),__language__(30102))

elif mode == "recent":
  if use_sqlite == 1:
    showRecent(sqlite_cur)
    sort()
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok(__language__(30101),__language__(30102))
         
elif mode == "play":
  if use_sqlite == 1:
    if mod_recent == 0:
      sqlite_con, sqlite_cur, sqlite_is_empty = initSQLite()
      unix_timestamp = int(time.time())
      sql_query = "INSERT INTO recent (server_name,listen_url,bitrate,genre,unix_timestamp) SELECT server_name,listen_url,bitrate,genre,'%s' FROM stations WHERE listen_url='%s' LIMIT 1" % (unix_timestamp, play)
      sqlite_cur.execute(sql_query)
      sqlite_con.commit()
  playLink(play)
  
else:
  u = "%s?mode=list" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30090), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?mode=search" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30091), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?mode=recent" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30104), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?mode=settings" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30095), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

