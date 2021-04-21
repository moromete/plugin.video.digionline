import urllib
# , urllib2
import http.cookiejar
# import cookielib
import os
import re
from bs4 import BeautifulSoup
import json
import requests.utils
import requests

class Digi():
  protocol = 'https'
  siteUrl = protocol + '://www.digionline.ro'
  apiUrl = protocol + '://digiapis.rcs-rds.ro/digionline'
  
  headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'identity',
    'Accept-Language': 'en-US,en;q=0.5', 
    'Connection': 'keep-alive',
    # 'Host': 'www.digionline.ro',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
  }
  
  def __init__( self , *args, **kwargs):
    if(kwargs.get('deviceId')):
      self.deviceId=kwargs.get('deviceId')
    if(kwargs.get('DOSESSV3PRI')):      
      self.DOSESSV3PRI=kwargs.get('DOSESSV3PRI')

    self.cookies = {'deviceId': self.deviceId,
                    'DOSESSV3PRI' : self.DOSESSV3PRI}

  def getPage(self, url, data=None, xhr=False, json=False):
    if (data != None):
      if(xhr):
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
      else:
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
      response = requests.post(url, cookies=self.cookies, headers=self.headers, data = data)
    else:
      response = requests.get(url, cookies=self.cookies, headers=self.headers)
    if(json):
      return response.json()
    else:
      return response.text

  def scrapCats(self, list_type, html, url=None):
    soup = BeautifulSoup(html, "html.parser")

    if list_type == 'cats':
      categories = soup.findAll("a", {"class": "nav-menu-item-link"})
      cats = []
      for link in categories:
          cats.append({'name': link['title'],
                       'url': link['href'],
                       'parent': url
                      })

    elif list_type == 'subcats':
      sub_cats = soup.findAll("a", {"class": "nav-submenu-item-link"})
      subcats = []
      for link in sub_cats:
        if 'Kids' in link['title']:
          subcats.append({'name': link['title'],
                       'url': link['href']+'/filme',
                       'parent': url
                      })
        else:
          subcats.append({'name': link['title'],
                       'url': link['href'],
                       'parent': url
                      })          

    elif list_type == 'submenus':
      sub_menus = soup.findAll("a", {"class": "nav-submenu-sublist-item-link"})
      submenus = []
      wrong_title=''
      for link in sub_menus:
        if link['href'] == '/hbo-go/filme/actiune-aventura':
          wrong_title = 'Actiune, aventura'
        else:
          wrong_title = link['title']      
        submenus.append({'name': wrong_title,##Hbo filme actiune-aventura are titlul gresit Drama
                      'url': link['href'],
                     'parent': url
                      })

    elif list_type == 'series':
      series_ = soup.find_all(class_="box box-portrait box-hbo")
      series = [] 
      if series_:
        for box in series_:
          for cnt in box.contents:
            cntString = cnt.encode('utf-8-sig')
            soup = BeautifulSoup(cntString, "html.parser")
            Link = soup.find('a', class_="box-link", href=True)
            if(Link):
              LinkUrl = Link['href']
            NameNode = soup.find('h5')
            if(NameNode):
              Name = NameNode.string
            logo = soup.find('div', class_='box-background')
            if(logo):
              get_style = logo['style']
              break_url=get_style.split("'")
              logoUrl=break_url[1]
              
          series.append({'name': Name,
                             'url': LinkUrl,
                             'parent': url.replace('?'+url.split("?")[-1],''),
                           'logo': logoUrl
                          })

    elif list_type == 'seasons':
      seasons_ = soup.find("ul", {"class": "seasons-nav-menu"})
      seasons = []
      if seasons_:
        seasons_2 = seasons_.findAll("a", {"href": True}) 
        for link in seasons_2:
          seasons.append({'name': link['href'].split("/")[-1],
                       'url': link['href'],
                       'parent': url
                      })

    if list_type == 'cats':
      return cats
    elif list_type == 'subcats':
      return subcats
    elif list_type == 'submenus':
      return submenus
    elif list_type == 'series':
      return series
    elif list_type == 'seasons':
      return seasons

  def scrapChannels(self, url):
    html = self.getPage(self.siteUrl + url)
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    HBOPLAYboxs = soup.find_all(class_="box")
    boxs = soup.find_all(class_="box-content")
    channels = []
    
    if('/hbo-go' not in url) and ('/play' not in url):
      for box in boxs:
        for cnt in box.contents:
          cntString = cnt.encode('utf-8-sig')
          soup = BeautifulSoup(cntString, "html.parser")
      
          # url
          chLink = soup.find('a', class_="box-link", href=True)
          if(chLink):
            chUrl = chLink['href']

          # name
          chNameNode = soup.find('h2')
          if(chNameNode):
            chName = chNameNode.string
            chName = chName.replace('\\n', '')
            chName = re.sub('\s+', ' ', chName)
            chName = re.sub('&period', '.', chName)
            chName = re.sub('&colon', ':', chName)
            chName = re.sub('&comma', ',', chName)
            chName = re.sub('&lpar', '(', chName)
            chName = re.sub('&rpar', ')', chName)
            chName = re.sub('&quest', '?', chName)
            chName = re.sub('&excl', '!', chName)
            chName = re.sub('&abreve', 'a', chName)
          
          # logo
          logo = soup.find('img', alt="logo", src=True)
          if(logo):
            logoUrl = logo['src']

        channels.append({'name': chName,
                         'url': chUrl,
                         'logo': logoUrl
                        })
    
    for box in HBOPLAYboxs:
      if('/hbo-go' in url) or ('/play' in url):
        for cnt in box.contents:
          cntString = cnt.encode('utf-8-sig')
          soup = BeautifulSoup(cntString, "html.parser")
      
          # url
          chLink = soup.find('a', class_="box-link", href=True)
          if(chLink):
            chUrl = chLink['href'].replace("https://www.digionline.ro","")

          # name
          chNameNode = soup.find('h5')
          if(chNameNode):
            chName = chNameNode.string
            chName = chName.replace('\\n', '')
            chName = re.sub('\s+', ' ', chName)
            chName = re.sub('&period', '.', chName)
            chName = re.sub('&colon', ':', chName)
            chName = re.sub('&comma', ',', chName)
            chName = re.sub('&lpar', '(', chName)
            chName = re.sub('&rpar', ')', chName)
            chName = re.sub('&quest', '?', chName)
            chName = re.sub('&excl', '!', chName)
            chName = re.sub('&abreve', 'a', chName)
            
          else:
            chNameNode = soup.find('h6')
            if(chNameNode):
              chName = chNameNode.string
              chName = chName.replace('\\n', '')
              chName = re.sub('\s+', ' ', chName)
              chName = re.sub('&period', '.', chName)
              chName = re.sub('&colon', ':', chName)
              chName = re.sub('&comma', ',', chName)
              chName = re.sub('&lpar', '(', chName)
              chName = re.sub('&rpar', ')', chName)
              chName = re.sub('&quest', '?', chName)
              chName = re.sub('&excl', '!', chName)
              chName = re.sub('&abreve', 'a', chName)
            
          # logo
          logo = soup.find('div', class_='box-background')
          if(logo):
            get_style = logo['style']
            break_url=get_style.split("'")
            logoUrl=break_url[1]
            
        channels.append({'name': chName,
                         'url': chUrl,
                         'logo': logoUrl
                        })
    return channels

  def getCookie(self, name):
    cookies = self.cookies
    try:
      return cookies[name]
    except:
      return None

  def scrapPlayUrl(self, url, quality = None):
    html = self.getPage(self.siteUrl + url)
    #print(html)
    soup = BeautifulSoup(html, "html.parser")
    player = soup.select("[class*=video] > script")
    if(len(player) == 0):
      return
    jsonStr = player[0].string.strip()
    chData = json.loads(jsonStr)
    url = chData['new-info']['meta']['streamUrl']
    chId = chData['new-info']['meta']['streamId']
    shortcode = chData['shortcode']
    id_device_full=self.getCookie('deviceId').split(".")
    id_device=id_device_full[1]

    if(chData['shortcode'] == 'livestream'):
      data = {
        'id_stream': chId,
        'quality': None 
      }
    elif(chData['shortcode'] == 'nagra-livestream'):
      data = {
        'id_device': self.getCookie('deviceId'),
        'id_stream': chId,
        'quality': None 
      }
    elif(chData['shortcode'] == 'play'):
      ip = chData['new-info']['meta']['ip']
      url2='/api/v12/play_stream_3.php'
      data = {
        'id_device': id_device,
        'asset_id_play': chId,
        'ip': ip 
      }
    elif(chData['shortcode'] == 'hbogo'):
      ip = chData['new-info']['meta']['ip']
      url2='/integrationapi/v2/hbogo/hbogo_stream.php'
      data = {
        'id_device': id_device,
        'asset_id_hbo': chId,
        'ip': ip 
      }
   
    #for q in arrQuality:
    # data['quality'] = q
    data['quality'] = 'abr'
    if(shortcode == 'livestream') or (shortcode == 'nagra-livestream'):
      chData = self.getPage(self.siteUrl + url, data=data, xhr=True, json=True)
    elif(shortcode == 'play') or (shortcode == 'hbogo'): 
      self.headers.update({'Referer': self.siteUrl + url})
      chData = self.getPage(self.apiUrl + url2, data=data, json=True)
      
    err = None 
    url=None
    subtitles = []
    if 'stream_url' in chData and chData['stream_url']:
      url = chData['stream_url']
    else:
      if 'data' in  chData and 'content' in chData['data'] and  'stream.manifest.url' in chData['data']['content'] and chData['data']['content']['stream.manifest.url']:
        url = chData['data']['content']['stream.manifest.url']
        rooturl=url.replace(url.split("/")[-1],'')
        moviename=url.split("/")[-1]
        movienameroot = moviename.replace(moviename.split(".")[-1],'')
        subfilename=""
        jsonStr = self.getPage(url)
        soup = BeautifulSoup(jsonStr, "html.parser")
        for el in soup.find_all('baseurl'):
          sub = ''.join(el.findAll(text=True))
          if('.vtt' in sub):
            subname = sub.split("/")[-1]
            if('ROM' in sub):
              subfilename = movienameroot +'ro.srt'
            elif('HUN' in sub):
              subfilename = movienameroot +'hu.srt'
            elif('ENG' in sub):
              subfilename = movienameroot +'en.srt'
            else:
              subfilename = subname             
           
            subtitles.append({'Url': rooturl + sub, 'SubName': subname, 'SubFileName': subfilename})
      else:
        err = chData['error']['error_message']
        soup = BeautifulSoup(err)
        err = soup.get_text()
    return {'url': url,
            'err': err,
            'subtitles':subtitles}

  def scrapPages(self, html, url, page_offset = 'All'):
    soup = BeautifulSoup(html, "html.parser")
    if page_offset == 'All':
      page_offset = "1200"
    page_offset=int(page_offset)/12
    pages_nav = soup.find("nav", {"class": "pagination-wrapper"})
    pages = []
    if pages_nav:
      active_page = pages_nav.find("li", {"class": "active"}).find("a", {"href": True})
      active_page_nr = active_page['href'].split("=")[-1]
      last_page = pages_nav.find("li", {"class": "last-page"}).find("a", {"href": True})
      last_page_nr = int(last_page['href'].split("=")[-1])
      if '=' not in url:
        url=url +'?p='+'1'
        url_page_nr = int(url.split("=")[-1])
      else:
        url_page_nr = int(url.split("=")[-1])
      for i in range(url_page_nr,min(last_page_nr+1,url_page_nr+page_offset)):
        pages.append({'name': str(i),
                     'url': last_page['href'].split("=")[0]+'='+str(i),
                     'parent': last_page['href'].split("?")[0],
                     'next': url.split("=")[0]+'='+str(min(last_page_nr,int(url.split("=")[-1])+ page_offset)),
                     'last': last_page['href']
                    })
    return pages
  