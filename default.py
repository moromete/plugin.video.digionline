import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import os, urllib, re
import traceback
import requests
from common import *
from resources.digi.digi import Digi
from resources.digi.digiapi import DigiApi

addonId = 'plugin.video.digionline'
addon = xbmcaddon.Addon(id=addonId)
logFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), addonId+'.log')
# cookieFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), 'cookies.txt')

def addDir(name, url, mode, logo = None, idCat = None):
  u = sys.argv[0] + "?mode=" + str(mode)

  if(url):
    u += "&url=" + urllib.parse.quote_plus(url)
  if(idCat):
    u += "&idCat=" + str(idCat)
    
  liz = xbmcgui.ListItem(name)
  if logo:
    liz.setArt({'thumb': logo})
  liz.setInfo( type="Video", infoLabels={ "Title": name })
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok

def addLink(name, mode, logo, url=None, idCh = None):
  u = sys.argv[0] + "?name=" + urllib.parse.quote_plus(name) + \
                    "&logo=" + urllib.parse.quote_plus(logo) +'&mode=' + str(mode)
  if(url):
    u += "&url=" + urllib.parse.quote_plus(url)
  if(idCh):
    u += "&idCh=" + str(idCh)

  liz = xbmcgui.ListItem(name)
  liz.setArt({'thumb': logo})
  liz.setInfo( type="Video", infoLabels={ "Title": name} )
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
  #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  return ok

def listCat():
  if(addon.getSetting('api') == 'true'):
    deviceIdFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), '.deviceId')
    digi = DigiApi(deviceIdFile = deviceIdFile)
    if(digi.login(addon.getSetting('username'), addon.getSetting('password')) == False):
      xbmcgui.Dialog().ok(addon.getLocalizedString(30013), digi.error)
      return
    cats = digi.getCategories()
  else:
    if(not addon.getSetting('deviceId') or not addon.getSetting('DOSESSV3PRI') ):
      xbmcgui.Dialog().ok(addon.getLocalizedString(30013), addon.getLocalizedString(30014))
      return
    digi = Digi(deviceId=addon.getSetting('deviceId'), DOSESSV3PRI=addon.getSetting('DOSESSV3PRI'))
    html=digi.getPage(digi.siteUrl)
    cats = digi.scrapCats('cats',html,'')

  for cat in cats:
    addDir(name =  cat['name'].encode('utf8'), url=cat.get("url", None), idCat=cat.get("id", None), mode=1)    

def listCh(url, idCat):
  if(idCat != None):
    deviceIdFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), '.deviceId')
    epgFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), '.epg')
    digi = DigiApi(deviceIdFile = deviceIdFile, epgFile=epgFile)
    if(digi.login(addon.getSetting('username'), addon.getSetting('password')) == False):
      xbmcgui.Dialog().ok(addon.getLocalizedString(30013), digi.error)
      return
    channels = digi.getChannels(idCat)
    for ch in channels:
      activeProgram = digi.getChannelActiveEpg(ch['id'])
      addLink(name = ch['name'] + (" - " + activeProgram if activeProgram else ""),
              idCh = ch['id'],
              logo = ch['logo'],
              mode = 2)
  else:
    addon_log(url)
    digi = Digi(deviceId=addon.getSetting('deviceId'), DOSESSV3PRI=addon.getSetting('DOSESSV3PRI'))
    html=digi.getPage(digi.siteUrl+url)
    isdir=0

    subcats = digi.scrapCats('subcats', html, url)

    for cat in subcats:
      if cat['url'].startswith(url) and cat['url'] != url:
        addDir(name =  cat['name'].encode('utf8'), url=cat['url'], mode=1)
        isdir=1

    if isdir == 0:  
      submenus = digi.scrapCats('submenus', html, url)
      for cat in submenus:
        if cat['url'].startswith(url) and cat['url'] != url:
          addDir(name =  cat['name'].encode('utf8'), url=cat['url'], mode=1)  
          isdir=1       

    if isdir == 0:
      pages = digi.scrapPages(html=html, url=url, page_offset=addon.getSetting('titles_per_page'))
      if pages and pages !=None:
        nextPage=pages[0]['next']
        lastPageNr=int(pages[0]['last'].split("=")[-1])
        nextPageNr=int(pages[0]['next'].split("=")[-1])
        series=[]
        for page in pages:
          html=digi.getPage(digi.siteUrl+page['url'])      
          series = series + digi.scrapCats('series', html, page['url'])
        new_series = []
        for elem in series:
          if elem not in new_series:
            new_series.append(elem)
        series = new_series
        for cat in series: 
          if cat['parent'] == url.split("?")[0] and cat['url'] != url.split("?")[0] and 'seriale' in cat['url']: 
            addDir(name =  cat['name'], url=cat['url'], mode=1, logo=cat['logo'])
            isdir=1
        if isdir==1 and lastPageNr>nextPageNr:
          addDir(name =  'Next Page', url=nextPage, mode=1)
        
      else:
        series = digi.scrapCats('series', html, url)
        for cat in series:
          if cat['parent'] == url and cat['url'] != url and 'seriale' in cat['url']:
            addDir(name =  cat['name'], url=cat['url'], mode=1, logo=cat['logo'])           
            isdir=1       

    if isdir == 0:  
      seasons = digi.scrapCats('seasons', html, url)
      for cat in seasons:
        if cat['parent'] == url and cat['url'] != url and 'sezon' in cat['url'] and 'sezon' not in url:
          addDir(name =  cat['name'].replace("-"," ").capitalize().encode('utf8'), url=cat['url'], mode=1)  
          isdir=1       
    
    if isdir == 0:
      if pages and pages !=None:
        nextPage=pages[0]['next']
        lastPageNr=int(pages[0]['last'].split("=")[-1])
        nextPageNr=int(pages[0]['next'].split("=")[-1])
        channels=[]
        for page in pages:
          channels = channels + digi.scrapChannels(page['url'])
        new_channels = []
        for elem in channels:
          if elem not in new_channels:
            new_channels.append(elem)
        channels = new_channels
        for ch in channels:
          addLink(name =  ch['name'].encode('utf8'),
                  url =  ch['url'],
                  logo = ch['logo'],
                  mode = 2)
        if isdir==0 and lastPageNr>nextPageNr:
          addDir(name =  'Next Page', url=nextPage, mode=1)    
      
      else:
        channels = digi.scrapChannels(url)
        for ch in channels:
          addLink(name =  ch['name'].encode('utf8'),
                url =  ch['url'],
                logo = ch['logo'],
                mode = 2)

def play(url, name, logo, idCh, retry=False):
  if(idCh != None):
    deviceIdFile = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), '.deviceId')
    digi = DigiApi(deviceIdFile = deviceIdFile)
    if(digi.login(addon.getSetting('username'), addon.getSetting('password')) == False):
      xbmcgui.Dialog().ok(addon.getLocalizedString(30013), digi.error)
      return
    url = digi.getPlayStream(idCh)
    if(url==False): #error
      #Pentru acces la programele transmise prin DigiOnline trebuie sa aveti un serviciu. (303)
      if(retry == True or digi.errorCode != '303'):
        xbmcgui.Dialog().ok(addon.getLocalizedString(30013), digi.error)
      else: #retry by relogin
        os.remove(deviceIdFile)
        play(url, name, logo, idCh, True)
      return
    player =  xbmc.Player()
    osAndroid = xbmc.getCondVisibility('system.platform.android')
    if(osAndroid):
      from streamplayer import streamplayer
      player = streamplayer(fakeRequest=True)
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo('video', {'Title': name})
    player.play(url, listitem)
  else:
    addon_log(url)
    digi = Digi(deviceId=addon.getSetting('deviceId'), DOSESSV3PRI=addon.getSetting('DOSESSV3PRI'))
    url = digi.scrapPlayUrl(url)
    if(url['err'] != None):
      addon_log(url['err'])
      xbmcgui.Dialog().ok(addon.getLocalizedString(30013), url['err'])
    else:
      player = xbmc.Player()
      if '.mpd' in url['url']:
        from inputstreamhelper import Helper  # type: ignore
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'thumb': logo})
        listitem.setInfo('video', {'Title': name})
        KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'
        MIME_TYPE = 'application/dash+xml'
        LICENSE_URL = 'https://wvp-cdn.rcs-rds.ro/proxy'
        license_headers = 'verifypeer=false'
        license_key = LICENSE_URL + '|' + license_headers + '|R{SSM}|'
        is_helper = Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():
            listitem = xbmcgui.ListItem(path=url['url'])
            listitem.setContentLookup(False)
            listitem.setMimeType(MIME_TYPE)
        
        if KODI_VERSION_MAJOR >= 19:
          listitem.setProperty('inputstream', is_helper.inputstream_addon)
          listitem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
          listitem.setProperty('inputstream.adaptive.license_type', DRM)
          listitem.setProperty('inputstream.adaptive.license_key', license_key)
        else:
          listitem.setProperty('inputstreamaddon', is_helper.inputstream_addon) 
          listitem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
          listitem.setProperty('inputstream.adaptive.license_type', DRM)
          listitem.setProperty('inputstream.adaptive.license_key', license_key)
          
          #  inject subtitles
          folder = xbmc.translatePath(addon.getAddonInfo('profile'))
          folder = folder + 'subs' + os.sep
          
          #  if inject subtitles is enable cache direct subtitle links if available and set subtitles from cache
          addon_log("Cache subtitles enabled, downloading and converting subtitles in: " + folder)
          if not os.path.exists(os.path.dirname(folder)):
              try:
                  os.makedirs(os.path.dirname(folder))
              except OSError as exc:  # Guard against race condition
                  if exc.errno != errno.EEXIST:
                      raise
          try:
              files = os.listdir(folder)
              for f in files:
                  os.remove(folder + f)
              subtitles = url['subtitles']
              if len(subtitles) > 0:
                  subs_paths = []
                  for sub in subtitles:
                      addon_log("Processing subtitle language code: " + sub['SubFileName'] + " URL: " + sub['Url'])
                      r = requests.get(sub['Url'])
                      with open(folder + sub['SubFileName'] , 'wb') as f:
                          f.write(r.content)
                      vtt_to_srt(folder + sub['SubFileName'])
                      subs_paths.append(folder + sub['SubFileName'])
                  listitem.setSubtitles(subs_paths)
                  addon_log("Local subtitles set")
              else:
                  addon_log("Inject subtitles error: No subtitles for the media")
          except KeyError:
              addon_log("Inject subtitles error: No subtitles key")
          except Exception:
              addon_log("Unexpected inject subtitles error: " + traceback.format_exc())
          
          xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
          
      else:
        player =  xbmc.Player()
        osAndroid = xbmc.getCondVisibility('system.platform.android')
        if(osAndroid):
          from streamplayer import streamplayer
          player = streamplayer(deviceId=addon.getSetting('deviceId'), DOSESSV3PRI=addon.getSetting('DOSESSV3PRI'))
        listitem = xbmcgui.ListItem(name)
      listitem.setInfo('video', {'Title': name})
      player.play(url['url'], listitem)

def vtt_to_srt(file):
  # Read VTT file
  with open(file) as f:
      lines = f.readlines()
  
  # Find a dot in a string matching e.g. 12:34:56.789
  # and replace it with a comma
  regex = r"(?<=\d\d:\d\d)\.(?=\d\d\d)"
  lines = [re.sub(regex, ",", i.rstrip()) for i in lines]
  
  regex = r"(?<=\d\d:\d\d:\d\d)\.(?=\d\d\d)"
  lines = [re.sub(regex, ",", i.rstrip()) for i in lines]
  
  # Find everything in line after a string matching e.g. 12:34:56,789
  # and delete it
  regex = r"(?<=--> \d\d:\d\d\,\d\d\d).*"
  lines = [re.sub(regex, "", i.rstrip()) for i in lines]
  
  regex = r"(?<=--> \d\d:\d\d:\d\d\,\d\d\d).*"
  lines = [re.sub(regex, "", i.rstrip()) for i in lines]

  regex = r"(?=^\d\d:\d\d\,\d\d\d)"
  lines = [re.sub(regex, "00:", i.rstrip()) for i in lines]

  regex = r"(?<=-->)\s(?=\d\d:\d\d\,\d\d\d)"
  lines = [re.sub(regex, " 00:", i.rstrip()) for i in lines]

  # Replace multiple blank lines with a single blank line
  sbl = []
  for i in range(len(lines[:-1])):
      if lines[i] == "" and lines[i+1] == "":
          continue
      else:
          sbl.append(lines[i])
  if lines[-1] != "":
      sbl.append(lines[-1])
  
  # Place a number before each time code (number empty lines)
  enum = enumerate(sbl)
  next(enum)
  nel = [str(i) or "\n" + str(next(enum)[0]) for i in sbl]
  
  # Remove WebVTT headers if any
  for i, item in enumerate(nel):
      if item == "\n1":
          break
  
  # Write SRT file
  with open(file, "w") as f:
      f.write("\n".join(nel[i:]))

#read params
params=getParams()
try:
  mode=int(params["mode"])
except:
  mode=None
try:
  url=urllib.parse.unquote_plus(params["url"])
except:
  url=None
try:
  idCat=urllib.parse.unquote_plus(params["idCat"])
except:
  idCat=None
try:
  idCh=urllib.parse.unquote_plus(params["idCh"])
except:
  idCh=None
try:
  name=urllib.parse.unquote_plus(params["name"])
except:
  name=None
try:
  logo=urllib.parse.unquote_plus(params["logo"])
except:
  logo=None

if (mode==None): #list categories
  listCat()
elif (mode==1):  #list channels movies episodes
  listCh(url = url, idCat=idCat)
elif (mode==2):  #play stream
  if xbmc.Player().isPlaying():
    xbmc.Player().stop()
  play(url = url, name = name, logo=logo, idCh=idCh)

try:
  deviceId = params["deviceId"]
except:
  deviceId = None
try:
  DOSESSV3PRI = params["DOSESSV3PRI"]
except:
  DOSESSV3PRI = None
if(deviceId and DOSESSV3PRI) :
  addon.setSetting('deviceId', deviceId)
  addon.setSetting('DOSESSV3PRI', DOSESSV3PRI)
  xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30020), "", 5000))
  listCat()

xbmcplugin.endOfDirectory(int(sys.argv[1]))