import requests
import os
# from os import path
import hashlib
import time
import uuid
import re
import datetime
import json
from bs4 import BeautifulSoup

class DigiApi():
  protocol = 'https'
  apiUrl = protocol + '://digiapis.rcs-rds.ro/digionline'

  deviceManufacturer = "SAMSUNG"
  deviceModel = "A10"
  deviceOs = "Android"

  deviceIdFile = '.deviceId'
  epgFile = '.epg'

  error = None
  errorCode = None
  
  headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'identity',
    'Accept-Language': 'en-US,en;q=0.5', 
    'Connection': 'keep-alive',
    'referer': 'https://www.digionline.ro',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
    }

  def __init__( self , *args, **kwargs):
    if(kwargs.get('deviceIdFile')):
      self.deviceIdFile=kwargs.get('deviceIdFile')
    if(kwargs.get('epgFile')):
      self.epgFile=kwargs.get('epgFile')

  def login( self, username, password):
    deviceId = self.getStoredDeviceId()
    if(deviceId != None):
      return

    passwordHash = hashlib.md5(password.encode('utf-8')).hexdigest()
    params = {'action': 'registerUser', 
              'user': username, 
              'pass': passwordHash
             }
    url = self.apiUrl + '/api/v13/user.php'
    response = requests.get(url, params=params)
    responseData = response.json()
    if(responseData['result']['code'] != '200'):
      print(responseData['result']['message'])
      self.error = responseData['result']['message']
      return False
    digiOnlineUserHash = responseData['data']['h']
    # print(digiOnlineUserHash)

    return self.registerDevice(username, passwordHash, digiOnlineUserHash)

  def registerDevice(self, username, passwordHash, digiOnlineUserHash):
    deviceId = self.getDeviceId()
    
    generate_md5 = hashlib.md5((username + passwordHash + deviceId + self.deviceManufacturer + self.deviceModel + self.deviceOs + digiOnlineUserHash).encode('utf-8')).hexdigest()
    # print(generate_md5)
    params = {"action": "registerDevice",
              "user": username,
              "pass": passwordHash,
              "i": deviceId,
              "dma": self.deviceManufacturer,
              "dmo": self.deviceModel,
              "o": self.deviceOs,
              "c": generate_md5
             }
    url = self.apiUrl + '/api/v13/devices.php'
    response = requests.get(url, params=params)
    responseData = response.json()
    print(responseData)
    if(responseData['result']['code'] != '200'):
      print(responseData['result']['message'])
      return False
    return True

  def getStoredDeviceId(self):
    if(os.path.exists(self.deviceIdFile)):
      f = open(self.deviceIdFile, "r")
      deviceId = f.read()
      f.close()
      if(len(deviceId) > 0):
        return deviceId 
  
  def setStoredDeviceId(self, deviceId):
    f = open(self.deviceIdFile, "w")
    f.write(deviceId)
    f.close()
  
  def getDeviceId(self):
    deviceId = self.getStoredDeviceId()
    if(deviceId != None):
      return deviceId

    str4 = self.deviceManufacturer + "_" + self.deviceModel + "_" + str(int(time.time()))
    
    replaceAll = (((((((str(uuid.uuid4()) + str(uuid.uuid4())) + str(uuid.uuid4())) + str(uuid.uuid4())) + str(uuid.uuid4())) + str(uuid.uuid4())) + str(uuid.uuid4())) + str(uuid.uuid4())).replace("-", "")
    length = (128 - len(str4)) + -1
    if (length <= 0 or len(replaceAll) < length):
      str2 = str4
    else:
      str2 = str4 + "_" + replaceAll[0:length]
            
    str2 = re.sub("\\W", "_", str2)
    str2 = re.sub("[^\\x00-\\x7F]", "_", str2)
    deviceId = str2

    self.setStoredDeviceId(deviceId)
    
    return deviceId

  def getPlayStream(self, idStream, retry=False):
    url = self.apiUrl + '/api/v13/streams_l_3.php'
    params={'action': "getStream",
            'id_stream': idStream,
            'platform': "Android",
            'version_app': "1.0",
            'i': self.getDeviceId(),
            'sn': "ro.rcsrds.digionline",
            's': "app",
            'quality': "all",
           }
    response = requests.get(url, params=params)
    responseData = response.json()
    print(responseData)
    if(responseData['error']):
      self.error = responseData['error']
      self.errorCode = re.findall(r"\((\d+)\)", self.error)[0]
      return False
 #   return responseData['stream']['abr']
    return {'url': responseData['stream']['abr']
            }

  def getStreamMPD(self,idStream,StreamType):
    id_device = self.getDeviceId()
    ip = requests.get('https://api.ipify.org').text
    if StreamType == "DIGI_PLAY":
      url= self.apiUrl + '/api/v12/play_stream_3.php'
      data = {
        'id_device': id_device,
        'asset_id_play': idStream,
        'ip': ip 
      }
    elif StreamType == "HBO_GO":
      url= self.apiUrl + '/integrationapi/v2/hbogo/hbogo_stream.php'
      data = {
        'id_device': id_device,
        'asset_id_hbo': idStream,
        'ip': ip 
      }
    response = requests.post(url, headers=self.headers, data = data)
    chData=response.json()
    print(chData)
    if(chData['error']['error_code'] != 0):
      self.error = chData['error']['error_message']
      self.errorCode = chData['error']['error_code']
      return False
    err = None 
    url=None
    subtitles = []
    url = chData['data']['content']['stream.manifest.url']
    rooturl=url.replace(url.split("/")[-1],'')
    moviename=url.split("/")[-1]
    movienameroot = moviename.replace(moviename.split(".")[-1],'')
    subfilename=""
    response = requests.get(url)
    jsonStr = response.text
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
       
        subtitles.append({'Url': rooturl + sub, 
                        'SubName': subname, 
                        'SubFileName': subfilename
                        })       
    return {'url': url,
            'err': err,
            'subtitles':subtitles}    
     
  def getCategories(self):
    url = self.apiUrl + '/api/v13/categorieschannels.php'
    response = requests.get(url)
    responseData = response.json()
    cats = []
    for cat in responseData['data']['categories_list']:
      cats.append({'name': cat['category_desc'],
                   'StreamType': "LiveTV",
                   'id': cat['id_category'],
                  })
    cats.append({'name': "DIGI PLAY",
                   'StreamType': "DIGI_PLAY",
                   'id': "root",
                  })
    cats.append({'name': "HBO GO",
                   'StreamType': "HBO_GO",
                   'id': "root",
                  })
    return cats

  def GetSubMenus(self, idCategory, StreamType):
    menus = []
    if StreamType == "DIGI_PLAY":
        url = self.apiUrl + '/api/v13/play_categories.php'
        response = requests.get(url)
        responseData = response.json()
        for menu in responseData['data']['menu_play']:
            if menu['menu_name'] != "PLAY":
                menus.append({'name': menu['menu_name'],
                            'StreamType': StreamType,
                            'id': menu['menu_id'],
                            'Parentid': idCategory,
                            })
    if StreamType == "HBO_GO":                            
        url = self.apiUrl + '/api/v13/hbogo_categories.php'
        response = requests.get(url)
        responseData = response.json()
        for menu in responseData['data']['menu_hbogo']:
            menus.append({'name': menu['menu_name'],
                        'StreamType': StreamType,
                        'id': menu['menu_id'],
                        'Parentid': idCategory,
                        })                         
    return menus  

  def GetSubCats(self, idCategory, StreamType):
    subcats = []
    if StreamType == "DIGI_PLAY":
        url = self.apiUrl + '/api/v13/play_categories.php'
        response = requests.get(url)
        responseData = response.json()
        for subcat in responseData['data']['menu_play']:
                for option in subcat['menu_options']:
                  if subcat['menu_id'] == idCategory:
                    subcats.append({'name': option['category_name'],
                                    'StreamType': StreamType,
                                    'id': option['category_id'],
                                    'Parentid': idCategory,
                                    })           
    if StreamType == "HBO_GO":                            
        url = self.apiUrl + '/api/v13/hbogo_categories.php'
        response = requests.get(url)
        responseData = response.json()
        for subcat in responseData['data']['menu_hbogo']:
                for option in subcat['menu_options']:
                  if subcat['menu_id'] == idCategory:
                    subcats.append({'name': option['category_name'],
                                    'StreamType': StreamType,
                                    'id': option['category_id'],
                                    'Parentid': idCategory,
                                    })
    return subcats

  def GetSeries(self, idCategory, StreamType):
    series = []
    if StreamType == "DIGI_PLAY":
        url = self.apiUrl + '/api/v13/play_list_series.php?id_category=' + idCategory
        response = requests.get(url)
        responseData = response.json()
        for serie in responseData['data']['list_series']:
         series.append({'name': serie['metadata']['title_ro'],
                      'StreamType': StreamType,
                      'id': serie['series_id'],
                      'Parentid': idCategory,
                      'logo': serie['media']['poster_hq'],
                      })       
                     
    if StreamType == "HBO_GO":                            
        url = self.apiUrl + '/api/v13/hbogo_list_series.php?id_category=' + idCategory
        response = requests.get(url)
        responseData = response.json()
        for serie in responseData['data']['list_series']:
         series.append({'name': serie['metadata']['title_ro'],
                      'StreamType': StreamType,
                      'id': serie['series_id'],
                      'Parentid': idCategory,
                      'logo': serie['media']['poster_hq'],
                      })  
    return series

  def GetSeasons(self, idCategory, StreamType):
    seasons = []
    if StreamType == "DIGI_PLAY":
        url = self.apiUrl + '/api/v13/play_series.php?asset_id=' + idCategory
        response = requests.get(url)
        responseData = response.json()
        for season in responseData['data']['series']['list_seasons']:
         seasons.append({'name': season['metadata']['title_ro']+" - "+season['slug'].split("/")[-1].replace("-"," ").upper(),
                      'StreamType': StreamType,
                      'id': season['season_id'],
                      'Parentid': idCategory,
                      'logo': season['media']['poster_hq'],
                      })       
                     
    if StreamType == "HBO_GO":                            
        url = self.apiUrl + '/api/v13/hbogo_series.php?asset_id=' + idCategory
        response = requests.get(url)
        responseData = response.json()
        for season in responseData['data']['series']['list_seasons']:
         seasons.append({'name': season['metadata']['title_ro']+" - "+season['slug'].split("/")[-1].replace("-"," ").upper(),
                      'StreamType': StreamType,
                      'id': season['season_id'],
                      'Parentid': idCategory,
                      'logo': season['media']['poster_hq'],
                      })  
    return seasons


  def GetKidsList(self, idCategory, StreamType):
    kids = []                                        
    url = self.apiUrl + '/api/v13/hbogo_list_kids.php?id_category=hbogo-kids'
    response = requests.get(url)
    responseData = response.json()

    for kid in responseData['data']['list_kids']:
        if kid['type'] == "movie":
            kids.append({'name': kid['metadata']['title_ro'],
                        'StreamType': StreamType,
                        'id': kid['asset_id'],
                        'Parentid': idCategory,
                        'logo': kid['media']['poster_hq'],
                        'plot': kid['metadata']['summary_ro'],
                        'DirType': "1"
                        })
        if kid['type'] == "series":
            kids.append({'name': kid['metadata']['title_ro'],
                        'StreamType': StreamType,
                        'id': kid['series_id'],
                        'Parentid': idCategory,
                        'logo': kid['media']['poster_hq'],
                        'DirType': "3"
                        })                          
    return kids


  def getChannels(self, idCategory, StreamType, DirType):
    url = self.apiUrl + '/api/v13/categorieschannels.php'
    
    if StreamType == "LiveTV":
        url = self.apiUrl + '/api/v13/categorieschannels.php'

    if StreamType == "DIGI_PLAY":
          if DirType == "1":
            url = self.apiUrl + '/api/v13/play_list_movies.php?id_category=' + idCategory 
          if DirType == "4":
            url = self.apiUrl + '/api/v13/play_series.php?asset_id=' + idCategory.split("-")[0]

    if StreamType == "HBO_GO":
        if DirType == "1":
            url = self.apiUrl + '/api/v13/hbogo_list_movies.php?id_category=' + idCategory
        if DirType == "4":
            url = self.apiUrl + '/api/v13/hbogo_series.php?asset_id=' + idCategory.split("-")[0]            
    response = requests.get(url)
    responseData = response.json()
    channels = []

    if StreamType == "LiveTV":
      for ch in responseData['data']['channels_list']:
        if(str(idCategory) in ch['channel_categories']):
          channels.append({'name': ch['channel_desc'],
                          'id': ch['id_channel'],
                          'logo': ch['media_channel']['channel_logo_url'],
                          'plot': ""
                          })
    if StreamType == "DIGI_PLAY":
        if DirType == "1":#Movies
            for ch in responseData['data']['list_movies']:
                channels.append({'name': ch['metadata']['title_ro'],
                                'id': ch['asset_id'],
                                'logo': ch['media']['thumbnail_hq'],
                                'plot': ch['metadata']['summary_ro']
                                })
        if DirType == "4":#Episodes
            for season in responseData['data']['series']['list_seasons']:
                if season['season_id']==idCategory:
                    for episode in season['list_episodes']:
                      channels.append({'name': episode['metadata']['title_ro'] + " - " + "Sezonul " + episode['metadata']['season_number'] + ", " + "Episodul " + episode['metadata']['episode_number'] ,
                                      'id': episode['asset_id'],
                                      'logo': episode['media']['thumbnail_hq'],
                                      'plot': episode['metadata']['summary_ro']
                                      })
                                
    if StreamType == "HBO_GO":
      if DirType == "1":#Movies
        for ch in responseData['data']['list_movies']:
          channels.append({'name': ch['metadata']['title_ro'],
                          'id': ch['asset_id'],
                          'logo': ch['media']['thumbnail_hq'],
                          'plot': ch['metadata']['summary_ro']
                          })
      if DirType == "4":#Episodes
          for season in responseData['data']['series']['list_seasons']:
              if season['season_id']==idCategory:
                  for episode in season['list_episodes']:
                    channels.append({'name': episode['metadata']['title_ro'],
                                    'id': episode['asset_id'],
                                    'logo': episode['media']['thumbnail_hq'],
                                    'plot': episode['metadata']['summary_ro']
                                    })                        
    return channels

  def getStoredEpg(self):
    if(os.path.exists(self.epgFile)):
      f = open(self.epgFile, "r")
      epg = f.read()
      f.close()
      if(len(epg) > 0):
        try:
          jsonEpg = json.loads(epg) 
          return jsonEpg
        except:
          print('error decoding stored epg')
          return None
  
  def setStoredEpg(self, epg):
    f = open(self.epgFile, "w")
    f.write(epg)
    f.close()
  
  def getEpg(self):
    epg = self.getStoredEpg()
    if(epg and epg['data']['date'] == str(datetime.date.today())):
      return epg

    url = self.apiUrl + '/api/v13/epg.php'
    params={'date': datetime.date.today(),
            'duration': 1,
           }
    response = requests.get(url, params=params)
    
    self.setStoredEpg(response.text)

    epg = response.json()
    return epg
  
  def getChannelEpg(self, idChannel):
    epg = self.getEpg()
    if(epg):
      for ch in epg['data']['channels']:
        if(str(idChannel) == ch['id_channel']):
          return ch['epg']

  def getChannelActiveEpg(self, idChannel):
    now = int(time.time())
    chEpg = self.getChannelEpg(idChannel)
    if(chEpg):
      for programItem in chEpg:
        if(programItem['start_ts'] !=  None and programItem['end_ts'] !=  None and now >= int(programItem['start_ts']) and now <= int(programItem['end_ts'])):
          ActiveEpg= []
          ActiveEpg.append({'name': programItem['program_name'],
                            'description': programItem['program_description'] + "\n" + programItem['program_description_l'] 
                        })
          return ActiveEpg