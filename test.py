import sys

from resources.digi.digi import Digi

digi = Digi()
html = digi.login(sys.argv[1], sys.argv[2])

#cats = digi.scrapCats(html)
#print(cats)

#cats = digi.scrapCatsPlay('/play')
#print(cats)

#channels = digi.scrapChannels('/play/filme')
#channels = digi.scrapMovies('/play/filme')
#print(channels)

#print(channels[0])
url = digi.scrapPlayUrl('/tematice/bbc-earth')
#url = digi.scrapPlayUrl('/filme/hbo')
#url = digi.scrapPlayUrl('/filme/cinemax-2')
print(url)


