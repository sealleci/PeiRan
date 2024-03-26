import json
import urllib.request
import urllib.parse
'''
秦皇岛城区 2021-04-24 ~ 2021-04-30
'''
def get_hist_datum():
  root_dir='./measure_datum/from_api'
  url = 'http://api.k780.com'
  params = {
    'app' : 'weather.history',
    'weaid' : '101091101',
    'date' : '',
    'appkey' : '58852',
    'sign' : '05d8ac4bb5376095aed93a997306e13c',
    'format' : 'json',
  }
  for i in range(24,31):
    params['date']='2021-04-{}'.format(i)
    params_encoded = urllib.parse.urlencode(params)

    f = urllib.request.urlopen('{}?{}'.format(url, params_encoded))
    nowapi_call = f.read()
    a_result = json.loads(nowapi_call,encoding='utf-8')
    if a_result:
      if a_result['success'] != '0':
        print('get hg 2021-04-{}'.format(i))
        with open('{}/qhd_202104{}.json'.format(root_dir,i),'w',encoding='utf-8') as json_file:
          json_file.write(json.dumps(a_result,ensure_ascii=False))
      else:
        print(a_result['msgid']+' '+a_result['msg'])
    else:
      print('Request nowapi fail.')

def get_city_certain():
  root_dir='./measure_datum/from_api'
  url = 'http://api.k780.com'
  params = {
    'app' : 'weather.history',
    'weaid' : '101091101',
    'date' : '2021-05-01',
    'appkey' : '58852',
    'sign' : '05d8ac4bb5376095aed93a997306e13c',
    'format' : 'json',
  }
  params_encoded = urllib.parse.urlencode(params)

  f = urllib.request.urlopen('{}?{}'.format(url, params_encoded))
  nowapi_call = f.read()
  a_result = json.loads(nowapi_call,encoding='utf-8')
  if a_result:
      if a_result['success'] != '0':
        with open('{}/qhd_202105{}.json'.format(root_dir,'01'),'w',encoding='utf-8') as json_file:
          json_file.write(json.dumps(a_result,ensure_ascii=False))

def get_today():
  root_dir='./measure_datum/from_api'
  url = 'http://api.k780.com'
  params = {
    'app' : 'weather.today',
    'weaid' : '101091101',
    'date' : '2021-05-01',
    'appkey' : '58852',
    'sign' : '05d8ac4bb5376095aed93a997306e13c',
    'format' : 'json',
  }
  params_encoded = urllib.parse.urlencode(params)

  f = urllib.request.urlopen('{}?{}'.format(url, params_encoded))
  nowapi_call = f.read()
  a_result = json.loads(nowapi_call,encoding='utf-8')
  if a_result:
      if a_result['success'] != '0':
          print(a_result['result'])

if __name__ == '__main__':
  get_today()
