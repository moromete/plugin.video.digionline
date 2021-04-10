import sys

from resources.digi.digi import Digi

digi = Digi(deviceId = 'xxxxxx', DOSESSV3PRI = 'yyyyyyyy')
# html = digi.login(sys.argv[1], sys.argv[2])
html = digi.getPage(digi.siteUrl)
# print(html)

#cats = digi.scrapCats('cats', html)
#print(cats)
#channels = digi.scrapChannels('/filme')
#print(channels)
# print(channels[0])
# url = digi.scrapPlayUrl('/tematice/bbc-earth')
url = digi.scrapPlayUrl('/tematice/history-channel')
#url = digi.scrapPlayUrl('/filme/hbo')
#url = digi.scrapPlayUrl('/filme/cinemax-2')
print(url)


