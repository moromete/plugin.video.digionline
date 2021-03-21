try:
  import xbmc, xbmcaddon
except ImportError:
  xbmcaddon = None
  addon = None
  pass

import sys

if (xbmcaddon):
  addonId = 'plugin.video.digionline'
  addon = xbmcaddon.Addon(id=addonId)

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

def addon_log(string):
  if addon and addon.getSetting('debug') == 'true':
    # if isinstance(string, unicode):
    #   string = string.encode('utf-8')
    xbmc.log("[%s-%s]: %s" %(addonId, addon.getAddonInfo('version'), string))