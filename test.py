import sys

from resources.digi.digi import Digi
from resources.digi.digiapi import DigiApi

# digi = Digi(deviceId = 'xxxxxx', DOSESSV3PRI = 'yyyyyyyy')
# html = digi.getPage(digi.siteUrl)
# print(html)

#cats = digi.scrapCats('cats', html)
#print(cats)
#channels = digi.scrapChannels('/filme')
#print(channels)
# print(channels[0])
# url = digi.scrapPlayUrl('/tematice/bbc-earth')
# url = digi.scrapPlayUrl('/tematice/history-channel')
#url = digi.scrapPlayUrl('/filme/hbo')
#url = digi.scrapPlayUrl('/filme/cinemax-2')
# print(url)

digi = DigiApi()
digi.login(sys.argv[1], sys.argv[2])
# print(digi.getCategories())
# print(digi.getChannels(3))
#filme
# print(digi.getChannels(4, "LiveTV", None))  
#HBO
# print(digi.getStreamMPD(68, None))
#print(digi.getPlayStream(68))


# print(digi.getPlayStream(20))
# print(digi.getEpg())
#print(digi.getChannelActiveEpg(20))
#print(digi.getChannelEpg(43))
#print(digi.getChannelActiveEpg(43))

# print(digi.GetSeries("root", "DIGI_PLAY"))
print(digi.getChannels("World_on_F-1", "DIGI_PLAY", "4"))