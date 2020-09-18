import xbmc
from common import addon_log
from resources.digi.digi import Digi

class streamplayer(xbmc.Player):
  def __init__(self, *args, **kwargs):
    self.cookieFile = kwargs.get('cookieFile')
    self.player_status = None
    xbmc.Player.__init__(self)

  def play(self, url, listitem):
    self.player_status = 'play'
    super(streamplayer, self).play(url, listitem)
    self.keep_allive(url)

  def onPlayBackEnded(self):
    addon_log('----------------------->END PLAY')
    self.player_status = 'end'

  def onPlayBackStopped(self):
    addon_log('----------------------->STOP PLAY')
    self.player_status = 'stop'

  def keep_allive(self, url):
    xbmc.sleep(500)

    #KEEP SCRIPT ALLIVE
    while (self.player_status=='play'):
      addon_log('ALLIVE')
      
      digi = Digi(cookieFile = self.cookieFile)
      m3u = digi.getPage(url) # needed for android devices to be accessed as browser before play otherwise we get 401 error
      addon_log(m3u)

      xbmc.sleep(60 * 1000)
      