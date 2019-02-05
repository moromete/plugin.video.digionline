import sys

from resources.digi.digi import Digi

digi = Digi()
html = digi.login(sys.argv[1], sys.argv[2])

# digi.digiFilm()

cats = digi.scrapCats(html)
print(cats)
channels = digi.scrapChannels('/tematice')
print(channels)
print(channels[0])
url = digi.scrapPlayUrl('/tematice/bbc-earth')
print(url)


