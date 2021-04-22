import requests
import os
# from os import path
import hashlib
import time
import uuid
import re
import datetime
import json

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
      self.errorCode = re.findall("\((\d+)\)", self.error)[0]
      return False

    return responseData['stream']['abr']

  def getCategories(self):
    url = self.apiUrl + '/api/v13/categorieschannels.php'
    response = requests.get(url)
    responseData = response.json()
    cats = []
    for cat in responseData['data']['categories_list']:
      cats.append({'name': cat['category_desc'],
                   'id': cat['id_category'],
                  })
    return cats

  def getChannels(self, idCategory):
    url = self.apiUrl + '/api/v13/categorieschannels.php'
    response = requests.get(url)
    responseData = response.json()
    channels = []
    for ch in responseData['data']['channels_list']:
      if(str(idCategory) in ch['channel_categories']):
        channels.append({'name': ch['channel_desc'],
                        'id': ch['id_channel'],
                        'logo': ch['media_channel']['channel_logo_url']
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
        if(now >= int(programItem['start_ts']) and now <= int(programItem['end_ts'])):
          return programItem['program_name'] + " " + programItem['program_description']