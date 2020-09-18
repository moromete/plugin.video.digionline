import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os, urllib, re
import traceback
import requests
from common import *
from resources.digi.digi import Digi

addonId = 'plugin.video.digionline'
addon = xbmcaddon.Addon(id=addonId)
logFile = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), addonId+'.log')
cookieFile = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'cookies.txt')

def addDir(name, url, mode,logo=""):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + '&mode=' + str(mode)
  
  liz = xbmcgui.ListItem(name, thumbnailImage=logo)
  liz.setInfo( type="Video", infoLabels={ "Title": name })
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok

def addLink(name, url, logo, mode):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&name=" + urllib.quote_plus(name) + \
                    "&logo=" + urllib.quote_plus(logo) +'&mode=' + str(mode)

  liz = xbmcgui.ListItem(name, thumbnailImage=logo)
  liz.setInfo( type="Video", infoLabels={ "Title": name} )
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
  #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  return ok

def listCat():
  if(addon.getSetting('reset_login') == 'true'):
    os.remove(cookieFile)
    addon.setSetting(id='reset_login', value='false')

  digi = Digi(cookieFile = cookieFile)
  html = digi.login(addon.getSetting('username'), addon.getSetting('password'))

  #addon_log(html)
  if(html == None):
    addon_log('Login error')
    xbmcgui.Dialog().ok(addon.getLocalizedString(30015), addon.getLocalizedString(30016))
    return
  cats = digi.scrapCats('cats',html,'')

  for cat in cats:
    addDir(name =  cat['name'].encode('utf8'), url=cat['url'], mode=1)    

def listCh(url):
  addon_log(url)
  digi = Digi(cookieFile = cookieFile)
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
    pages = digi.scrapPages(html,url)
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

def play(url, name, logo):
  addon_log(url)

  # quality = None
  # arrQualities = ['abr', 'hq', 'mq', 'lq']
  # if(addon.getSetting('choose_quality') == 'true'):
  #   dialog = xbmcgui.Dialog()
  #   quality = dialog.select(addon.getLocalizedString(30018), arrQualities)
  #   quality = arrQualities[quality]
  #   # addon_log(quality)

  digi = Digi(cookieFile = cookieFile)
  #url = digi.scrapPlayUrl(url, quality)
  url = digi.scrapPlayUrl(url)
  if(url['err'] != None):
    addon_log(url['err'])
    xbmcgui.Dialog().ok(addon.getLocalizedString(30013), url['err'])
  else:
    if '.mpd' in url['url']:
      from inputstreamhelper import Helper  # type: ignore
      listitem = xbmcgui.ListItem(name, thumbnailImage=logo)
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
      osAndroid = xbmc.getCondVisibility('system.platform.android')
      if(osAndroid):
        digi = Digi(cookieFile = cookieFile)
        m3u = digi.getPage(url['url']) # needed for android devices to be accessed as browser before play otherwise we get 401 error
        addon_log(m3u)
      listitem = xbmcgui.ListItem(name, thumbnailImage=logo)
      listitem.setInfo('video', {'Title': name})
    xbmc.Player().play(url['url'], listitem)

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
  url=urllib.unquote_plus(params["url"])
except:
  url=None
try:
  name=urllib.unquote_plus(params["name"])
except:
  name=None
try:
  logo=urllib.unquote_plus(params["logo"])
except:
  logo=None

if (mode==None): #list categories
  listCat()
elif (mode==1):  #list channels movies episodes
  listCh(url = url)
elif (mode==2):  #play stream
  if xbmc.Player().isPlaying():
    xbmc.Player().stop()
  play(url = url, name = name, logo=logo)

xbmcplugin.endOfDirectory(int(sys.argv[1]))