#/*
# *      Copyright (C) 2010 Team XBMC
# *
# *
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

import urllib2,string,xbmc,xbmcgui,xbmcplugin, xbmcaddon
from xml.dom import minidom
from urllib import quote_plus
import unicodedata

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.shoutcast')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Icecast"
__addonid__      = "plugin.audio.icecast"
__author__        = "Team XBMC"

BASE_URL = 'http://dir.xiph.org/yp.xml'

def getText(nodelist):
  rc = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      rc.append(node.data)
  return ''.join(rc)

# Read the XML list from IceCast server
def readRemoteXML():
  req = urllib2.Request(BASE_URL)
  response = urllib2.urlopen(req)
  xml = response.read()
  response.close()
  return xml

# Parse XML
def parseXML(xml):
  dom = minidom.parseString(xml)
  return dom

# Read the XML file form local cache
def readLocalXML():
  f = open('icecast.cache','r')
  xml = f.read()
  f.close()
  return xml

# Overwrite the local cache
def writeLocalXML(xml):
  f = open('icecast.cache','w')
  f.write(xml)
  f.close()

# Build the list of genres
def buildGenreList(dom):
  genre_hash = {'various': 1}
  genres = dom.getElementsByTagName("genre")
  for genre in genres:
    genre_name = getText(genre.childNodes)
    for genre_name_single in genre_name.split():
      genre_hash[genre_name_single] = 1
  for k in sorted(genre_hash.keys()):
    addDir(k)

# Add a genre to the list
def addDir(genre_name):
  u = "%s?genre=%s" % (sys.argv[0], genre_name,)
  liz=xbmcgui.ListItem(genre_name, iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

# Build list of links in a given genre
def buildLinkList(dom, genre_name_orig):
  link_hash = {}
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    if genre_name.find(genre_name_orig) > -1 :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      server_name_objects = entry.getElementsByTagName("server_name")
      for server_name_object in server_name_objects:
        server_name = getText(server_name_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      key = "%s@@@%s" % (server_name, listen_url)
      link_hash[key] = 1

  for key in sorted(link_hash.keys()):
    server_name, listen_url = key.split("@@@")
    addLink(server_name,listen_url,bitrate)

# Add a link inside of a genre list
def addLink(server_name,listen_url,bitrate):
  ok=True
  u = "%s?play=%s" % (sys.argv[0], listen_url,)
  liz=xbmcgui.ListItem(server_name, iconImage="DefaultVideo.png", thumbnailImage="")
  liz.setInfo( type="Music", infoLabels={ "Title": server_name ,"Bitrate": bitrate} )
  liz.setProperty("IsPlayable","false");
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  return ok

# Get a search query from keyboard
def readKbd():
  kb = xbmc.Keyboard("", __language__(30092), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    return kb.getText()

# Do a search
def doSearch(dom, query):
  link_hash = {}
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    server_name_objects = entry.getElementsByTagName("server_name")
    for server_name_object in server_name_objects:
      server_name = getText(server_name_object.childNodes)

    if ((genre_name.find(query) > -1) or (server_name.find(query) > -1)) :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      key = "%s@@@%s" % (server_name, listen_url)
      link_hash[key] = 1

  for key in sorted(link_hash.keys()):
    server_name, listen_url = key.split("@@@")
    addLink(server_name,listen_url,bitrate)

# Play a link
def playLink(listen_url):
  log("PLAY URL: %s" % listen_url )   
  xbmc.Player().play(listen_url)

# Read command-line parameters
def getParams():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

# Logging
def log(msg):
  xbmc.output("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGDEBUG )
 
# Sorting
def sort(dir = False):
  if dir:
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
#    try:
#      xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LISTENERS )
#    except: pass
  else:
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X" )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X" )
#    try:
#      xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LISTENERS )
#    except: pass
  xbmcplugin.endOfDirectory(int(sys.argv[1]))        

# MAIN 
params=getParams()

try:
  genre = params["genre"]
except:
  genre = "0";
try:
  initial = params["initial"]
except:
  initial = "0";
try:
  play = params["play"]
except:
  play = "0";

igenre = len(genre)
iplay = len(play)
iinitial = len(initial)

if igenre > 1 :
  xml = readLocalXML()
  dom = parseXML(xml)
  buildLinkList(dom, genre)
  sort()

elif iinitial > 1:
  if initial == "search":
    query = readKbd()
    xml = readRemoteXML()
    dom = parseXML(xml)
    writeLocalXML(xml)
    doSearch(dom, query)
    sort()
  else:
    xml = readRemoteXML()
    dom = parseXML(xml)
    writeLocalXML(xml)
    buildGenreList(dom)
    sort(True)
         
elif iplay > 1:
  playLink(play)
  
#elif isearch > 1:
#  doSearch(srch)
#  sort()
  
else:
  u = "%s?initial=list" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30090), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?initial=search" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30091), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
