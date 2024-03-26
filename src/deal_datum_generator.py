import random
import numpy
import json
import math
import numpy as np

root_dir = './measure_datum/inst'
inst_names=[
    'thermometer', 
    'hygrometer', 
    'barometer', 
    'anemometer', 
    'vane', 
    'dustmeter'
]

def pre_gen():
    data_args = {
        'thermometer': (-40.0, 85.0, 0.01), 
        'hygrometer': (0.0, 100.0, 0.024), 
        'barometer': (300.0, 1100.0,  0.01), 
        'anemometer': (0.0, 30.0, 0.1), 
        'vane': (0.0, 360.0, 45.0), 
        'dustmeter': (0.0, 1000.0, 1.0)
    }
    generate_count=30

    for (name, arg) in data_args.items():
        with open(root_dir+name+'.json','w') as json_file:
            data_list=list(map(lambda x:arg[0]+x*arg[2],numpy.random.randint(0,math.ceil((arg[1]-arg[0])/arg[2])+1,size=generate_count)))
            # print(data_list)
            json.dump({'datum':data_list},json_file)

def cur_gen(seed):
    random.seed(seed)
    api_dir='./measure_datum/from_api'
    mondays=['0425','0426','0427','0428','0429','0430','0501']
    data_args={
        # (api字段,单位,扩增系数,[最小值,最大值],[浮动下限,浮动上限,步长],缺少时的默认值,保留位数)
        'thermometer': ('temperature','℃',1,[-99.0,99.0],[-0.4,0.4,0.1],12.0,1), 
        'hygrometer': ('humidity','%',1,[0,100],[-2,2,1],54,1), 
        'anemometer': ('winpid','',2.5,[0.0,32.0],[-0.6,0.6,0.1],5.0,1), # 一级:1...，缺少:-1
        'vane': ('windid','',45,[0,360],[-22.5,22.5,0.5],45.0,1), # 东北:1 -顺时针-> 北:8，微风:0，缺少:-1
        'dustmeter': ('aqi','',1,[0,300],[-2,2,1],37,0)
    }
    for (name,arg) in data_args.items():
        rdata=[]
        for di in mondays:
            with open('{}/qhd_2021{}.json'.format(api_dir,di),'r',encoding='utf-8') as jsf:
                jsread=json.load(jsf)
                for hi in jsread['result']:
                    vi=0.0
                    if hi[arg[0]]!='':
                        if arg[1]=='':
                            vi=hi[arg[0]]
                            vi=float(vi)*arg[2]
                        else :
                            fi=hi[arg[0]].find(arg[1])
                            vi=hi[arg[0]][0:fi]
                            vi=float(vi)*arg[2]
                    else :
                        vi=arg[5]
                    rdata.append(vi)

        with open('{}/{}.json'.format(root_dir,name),'w',encoding='utf-8') as jsf:
            jsdata={'datum':[]}
            for ei,di in enumerate(mondays):
                tdata={
                    "date":'2021-{}-{}'.format(di[0:2],di[2:4]),
                    "values":[]
                }
                for hi in range(0,24):
                    rnd_arr=np.linspace(arg[4][0],arg[4][1] ,num=math.ceil((arg[4][1]-arg[4][0]+1)/arg[4][2]))
                    for mi in range(0,12):
                        vi=random.choice(rnd_arr)+rdata[(ei-1)*24+hi]
                        if name=='vane':
                            vi=(vi+360)%360
                        tdata['values'].append({
                                "value": round(max(min(vi,arg[3][1]), arg[3][0]),arg[6]),
                                "time":'{:02}:{:02}:{:02}'.format(hi,mi*5,random.randint(0, 59))
                            }
                        )
                jsdata['datum'].append(tdata)
            jsf.write(json.dumps(jsdata,ensure_ascii=False))

def pres_gen(seed):
    random.seed(seed)
    mondays=['0425','0426','0427','0428','0429','0430','0501']
    with open('{}/{}.json'.format(root_dir,'barometer'),'w',encoding='utf-8') as jsf:
        jsdata={'datum':[]}
        for ei,di in enumerate(mondays):
            tdata={
                "date":'2021-{}-{}'.format(di[0:2],di[2:4]),
                "values":[]
            }
            for hi in range(0,24):
                vi=random.randint(980, 1010)
                rnd_arr=np.linspace(-2,2,5)
                for mi in range(0,12):
                    tdata['values'].append({
                            "value": math.floor(vi+random.choice(rnd_arr)),
                            "time":'{:02}:{:02}:{:02}'.format(hi,mi*5,random.randint(0, 59))
                        }
                    )
            jsdata['datum'].append(tdata)
        jsf.write(json.dumps(jsdata,ensure_ascii=False))

if __name__ == '__main__':
    cur_gen(114514)