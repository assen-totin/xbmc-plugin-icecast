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

DB_FILE_NAME = 'icecast.sqlite'
DB_CREATE_TABLE_STATIONS = 'CREATE TABLE stations (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255));'
DB_CREATE_TABLE_FAVOURITES = 'CREATE TABLE favourites (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255));'
DB_CREATE_TABLE_RECENT = 'CREATE TABLE recent (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255), unix_timestamp VARCHAR(255));'
DB_CREATE_TABLE_SETTINGS = 'CREATE TABLE settings (name VARCHAR(255), val VARCHAR(255))'
DB_CREATE_TABLE_UPDATES = 'CREATE TABLE updates (unix_timestamp VARCHAR(255));'
DB_CREATE_TABLE_VERSION = 'CREATE TABLE version (version INT);'
DB_REQUIRED_VERSION = 1 

# Init function for SQLite
def initSQLite():
  sqlite_file_name = getSQLiteFileName()
  sqlite_con = sqlite.connect(sqlite_file_name)
  sqlite_cur = sqlite_con.cursor()
  try:
    sqlite_cur.execute(DB_CREATE_TABLE_STATIONS)
    sqlite_cur.execute(DB_CREATE_TABLE_FAVOURITES)
    sqlite_cur.execute(DB_CREATE_TABLE_RECENT)
    sqlite_cur.execute(DB_CREATE_TABLE_SETTINGS)
    sqlite_cur.execute(DB_CREATE_TABLE_UPDATES)
    sqlite_cur.execute(DB_CREATE_TABLE_VERSION)

    sql_query = "INSERT INTO version (version) VALUES (%u)" % (DB_REQUIRED_VERSION)
    sqlite_cur.execute(sql_query)

    sql_query = "INSERT INTO settings (name, val) VALUES ('%s','%s')" % ('30098','0')
    sqlite_cur.execute(sql_query)

    putTimestampSQLite(sqlite_con, sqlite_cur)

    sqlite_is_empty = 1
  except:
    # Check if the database needs upgrade
    try:
      version = 0
      sqlite_cur.execute("SELECT version FROM version")
      for version in sqlite_cur:
        if version < DB_REQUIRED_VERSION:
          upgradeDatabase(sqlite_con, sqlite_cur, version)
    except:
      # Upgrde from old version that has no 'version' table
      upgradeDatabase(0, sqlite_cur)
    
    sqlite_is_empty = 0
  return sqlite_con, sqlite_cur, sqlite_is_empty

# Database upgrade
def upgradeDatabase(sqlite_con, sqlite_cur, version):
  if version == 0:
    sqlite_cur.execute(DB_CREATE_TABLE_FAVOURITES)
    sqlite_cur.execute(DB_CREATE_TABLE_RECENT)
    sqlite_cur.execute(DB_CREATE_TABLE_SETTINGS)
    sqlite_cur.execute(DB_CREATE_TABLE_VERSION)
    sql_query = "INSERT INTO version (version) VALUES (%u)" % (DB_REQUIRED_VERSION)
    sqlite_cur.execute(sql_query)
    sql_query = "INSERT INTO settings (name, val) VALUES ('%s','%s')" % ('30098','0')
    sqlite_cur.execute(sql_query)
    sqlite_con.commit()

# Show settings menu (SQL version only)
def showSettings(sqlite_cur):
  settings_hash = {}
  val_new = 0
  txt = ''
  sqlite_cur.execute("SELECT name, val FROM settings")
  for name, val in sqlite_cur:
    settings_hash[name] = val

  # Favourites: 30098
  if settings_hash.has_key('30098'):
    if settings_hash['30098'] == '1':
      txt = "%s %s" % (__language__(30097),__language__(30098))
      val_new = 0
    elif settings_hash['30098'] == '0':
      txt = "%s %s" % (__language__(30096), __language__(30098))
      val_new = 1

    u = "%s?initial=settings&settings=%s&val=%s" % (sys.argv[0], '30098', val_new)
    liz = xbmcgui.ListItem(txt, iconImage="DefaultFolder.png", thumbnailImage="")
    liz.setInfo( type="Music", infoLabels={"Title": txt, "Size": 0} )
    liz.setProperty("IsPlayable","false");
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  # 'Done' link
  u = "%s" % (sys.argv[0])
  liz = xbmcgui.ListItem(__language__(30103), iconImage="DefaultFolder.png", thumbnailImage="")
  liz.setInfo( type="Music", infoLabels={"Title": __language__(30103), "Size": 0} )
  liz.setProperty("IsPlayable","false");
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def updateSettings(sqlite_con, sqlite_cur, settings, val):
  sql_query = "UPDATE settings SET val=%s WHERE name=%s" % (val, settings)
  sqlite_cur.execute(sql_query)
  sqlite_con.commit()

# Compose the SQLite database file name
def getSQLiteFileName():
  cache_file_dir = getUserdataDir()
  db_file_name = os.path.join(cache_file_dir,DB_FILE_NAME)
  return db_file_name

# Populate SQLite table
def DOMtoSQLite(dom, sqlite_con, sqlite_cur):
  sqlite_cur.execute("DELETE FROM stations")
  sqlite_con.commit()

  entries = dom.getElementsByTagName("entry")
  for entry in entries:

    listen_url_objects = entry.getElementsByTagName("listen_url")
    for listen_url_object in listen_url_objects:
      listen_url = getText(listen_url_object.childNodes)
      listen_url = re.sub("'","&apos",listen_url)

    server_name_objects = entry.getElementsByTagName("server_name")
    for server_name_object in server_name_objects:
      server_name = getText(server_name_object.childNodes)
      server_name = re.sub("'","&apos",server_name)

    bitrate_objects = entry.getElementsByTagName("bitrate")
    for bitrate_object in bitrate_objects:
      bitrate = getText(bitrate_object.childNodes)

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

      for genre_name_single in genre_name.split():
        genre_name_single = re.sub("'","&apos",genre_name_single)
        sql_query = "INSERT INTO stations (server_name, listen_url, bitrate, genre) VALUES ('%s','%s','%s','%s')" % (server_name, listen_url, bitrate, genre_name_single)
        sqlite_cur.execute(sql_query)

  sqlite_con.commit()

# Build the list of genres from SQLite
def buildGenreList(sqlite_cur):
  sqlite_cur.execute("SELECT genre, COUNT(*) AS cnt FROM stations GROUP BY genre")
  for genre, cnt in sqlite_cur: 
    addDir(genre, cnt)

# Build list of links in a given genre from SQLite
def buildLinkList(sqlite_cur, genre_name_orig):
  from_recent = 0
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE genre='%s'" % (genre_name_orig)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate, from_recent)

# Build list of links in a given genre from SQLite
def showRecent(sqlite_cur):
  from_recent = 1
  sqlite_cur.execute("SELECT server_name, listen_url, bitrate FROM recent ORDER BY unix_timestamp DESC LIMIT 20")
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate, from_recent)

# Do a search in SQLite
def doSearchSQLite(sqlite_cur, query):
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE (genre LIKE '@@@%s@@@') OR (server_name LIKE '@@@%s@@@')" % (query, query)
  sql_query = re.sub('@@@','%',sql_query)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate)

# Functions to read and write unix timestamp to database or file
def putTimestamp(sqlite_con, sqlite_cur):
  unix_timestamp = int(time.time())
  sql_line = "INSERT INTO updates (unix_timestamp) VALUES (%u)" % (unix_timestamp)
  sqlite_cur.execute(sql_line)
  sqlite_con.commit()

def getTimestamp(sqlite_cur): 
  sqlite_cur.execute("SELECT unix_timestamp FROM updates ORDER BY unix_timestamp DESC LIMIT 1")
  #unix_timestamp = sqlite_cur.fetchall()
  for unix_timestamp in sqlite_cur:
    return int(unix_timestamp[0])

# Timestamp wrappers
def timestampExpired(sqlite_cur):
  current_unix_timestamp = int(time.time())
  saved_unix_timestamp = getTimestampSQLite(sqlite_cur)
  if (current_unix_timestamp - saved_unix_timestamp) > TIMESTAMP_THRESHOLD :
    return 1
  return 0

