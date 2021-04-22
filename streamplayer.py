import xbmc
from common import addon_log
from resources.digi.digi import Digi
import requests

class streamplayer(xbmc.Player):

  deviceId = None
  DOSESSV3PRI = None

  fakeRequest = None

  def __init__(self, *args, **kwargs):
    # self.cookieFile = kwargs.get('cookieFile')
    if(kwargs.get('deviceIdFile')):
      self.deviceId = kwargs.get('deviceId')
    if(kwargs.get('DOSESSV3PRI')):  
      self.DOSESSV3PRI = kwargs.get('DOSESSV3PRI')
    if(kwargs.get('fakeRequest')):  
      self.fakeRequest = kwargs.get('fakeRequest')
    
    self.player_status = None
    xbmc.Player.__init__(self)

  def play(self, url, listitem):
    self.player_status = 'play'
    self.digiFakeRequest(url)
    super(streamplayer, self).play(url, listitem)
    self.keep_allive(url)

  def onPlayBackEnded(self):
    addon_log('----------------------->END PLAY')
    self.player_status = 'end'

  def onPlayBackStopped(self):
    addon_log('----------------------->STOP PLAY')
    self.player_status = 'stop'

  def keep_allive(self, url):
    #KEEP SCRIPT ALLIVE
    time = 0 
    interval = 500
    while (self.player_status=='play'):
      addon_log('ALLIVE')
      xbmc.sleep(500)
      time += interval
      if(time > 60 * 1000):
        time = 0
        self.digiFakeRequest(url)
  
  def digiFakeRequest(self, url):
    if(self.deviceId and self.DOSESSV3PRI):
      digi = Digi(deviceId=self.deviceId, DOSESSV3PRI=self.DOSESSV3PRI)
      m3u = digi.getPage(url) # needed for android devices to be accessed as browser before play otherwise we get 401 error
      addon_log(m3u)
    else:
      if (self.fakeRequest):
        response = requests.get(url)
        addon_log(response.text)
