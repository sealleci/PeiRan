import json
import math
import random
import time
import threading
import time
import numpy as np
import socket
import queue
import tkinter as tk

from util_load_cfg import get_center_addr,get_global_addr

'''
中心站线程：
1. 监听地区站点
2. 监听用户
3. 数据处理与预测
'''
lls=[]
btn_flag=False
btn_flag2=False
value_names_list=['temperature','humidity','pressure','direction','velocity','pm2.5']
date_next_list=['2021-04-25','2021-04-26','2021-04-27','2021-04-28','2021-04-29','2021-04-30','2021-05-01','2021-05-02','2021-05-03','2021-05-04','2021-05-05','2021-05-06']

mq_lock=threading.Lock()
meteor_q=queue.Queue(24)

t_lock=threading.Lock()
data_store={}
'''
{
    'zone':{
        'date':{
            'time':{
                'temp':0,
            }
        }
    }
}
'''
pd_lock=threading.Lock()
pred_list={}
'''
{
    'zone':{
        'date':{

        }
    }
}
'''

def get_fut_24_hours(t_date,t_time):
    cur_h=t_time[0:2]
    cur_h=int(cur_h)
    dt_pred=[]
    for i in range(0,24):
        if cur_h+i>24:
            dt_pred.append((
                date_next_list[min(date_next_list.index(t_date),len(date_next_list))],
                '{:02}:00:00'.format((cur_h+i)%24)
            ))
        else:
            dt_pred.append((
                t_date,
                '{:02}:00:00'.format(cur_h+i)
            ))
    # print('hours: {}'.format(dt_pred))
    return dt_pred

def get_fut_5_days(t_date):
    dy_pred=[]
    fidx=date_next_list.index(t_date)
    for di in range(fidx,min(fidx+5,len(date_next_list))):
        dy_pred.append(date_next_list[di])
    # print('days: {}'.format(dy_pred))
    return dy_pred

def interact_to_user():
    global btn_flag2
    host,port = get_global_addr()
    srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_socket.bind((host, port))
    srv_socket.listen(3)
    print('center listen to users...')

    while True:
        clt_socket,addr=srv_socket.accept()
        print('center accepted user from {}:{}'.format(addr[0],addr[1]))
        
        rcv_msg=clt_socket.recv(1024)
        res_msg={'recieved':0}

        if rcv_msg!='':
            print('center received from user')
            while len(lls)!=2:
                time.sleep(1)
            rcv_json=json.loads(rcv_msg,encoding='utf-8')
            lls[1].insert(tk.END,'user,{},{} {}'.format('qhd-city',rcv_json['date'],rcv_json['time'][0:5]))

            t_zid=rcv_json['zone_id']
            t_date=rcv_json['date']
            t_time=rcv_json['time']
            res_msg={
                'recieved':1,
                'success':1,
                'zone_id':t_zid,
                'future_days':[],
                'future_hours':[]
            }

            # 整理未来24小时的日期与时间
            dt_pred=get_fut_24_hours(t_date,t_time)
            t_lock.acquire()
            for dt in dt_pred:
                if (dt[0] in data_store[t_zid]) and (dt[1] in data_store[t_zid][dt[0]]):
                    tjs=data_store[t_zid][dt[0]][dt[1]]
                    # print(tjs)
                    res_msg['future_hours'].append({
                        'date':dt[0],
                        'time':dt[1],
                        'weather_type':random.randint(1,3),
                        'temp_unit':tjs['temp_unit'],
                        'temp':tjs['temp'],
                        'humi':tjs['humi'],
                        'aqi':tjs['aqi'],
                        'wind_dir':tjs['wind_dir'],
                        'wind_frc':tjs['wind_frc']
                    })
                else:
                    res_msg['success']=0
            t_lock.release()
            # 未来五天
            dy_pred=get_fut_5_days(t_date)
            pd_lock.acquire()
            for di in dy_pred:
                if di in pred_list[t_zid]:
                    res_msg['future_days'].append(pred_list[t_zid][di])
                    res_msg['future_days'][-1]['date']=di
            pd_lock.release()
        
        while not btn_flag2:
            time.sleep(1)
        clt_socket.send(json.dumps(res_msg,ensure_ascii=False).encode('utf-8'))
        print('center sended to user')

        clt_socket.close()
        print('center closed user {}:{}'.format(addr[0],addr[1]))

        btn_flag2=False

def interact_to_meteor():
    host,port = get_center_addr()
    srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_socket.bind((host, port))
    srv_socket.listen(3)
    print('center listen to meteor stations...')

    while True:
        clt_socket,addr=srv_socket.accept()
        # print('center accepted meteor from {}:{}'.format(addr[0],addr[1]))

        rcv_msg=clt_socket.recv(2048)
        ctrl_msg={'recieved':0}

        if rcv_msg!='':
            print('center received from meteor')

            mq_lock.acquire()
            meteor_q.put(rcv_msg)
            mq_lock.release()

            ctrl_msg['recieved']=1
        
        clt_socket.send(json.dumps(ctrl_msg,ensure_ascii=False).encode('utf-8'))
        print('center sended to meteor {}'.format(ctrl_msg['recieved']))

        clt_socket.close()
        print('center closed meteor from {}:{}'.format(addr[0],addr[1]))

def predict(tmp_json):
    global btn_flag
    while not btn_flag:
        time.sleep(1)
    # 预测未来24小时
    t_zid=tmp_json['zone_id']  
    t_date=tmp_json['date']   
    t_time=tmp_json['time']
    # 找现在最大时间
    cur_h=t_time[0:2]
    
    # 整理未来24小时的日期与时间
    dt_pred=get_fut_24_hours(t_date,t_time)

    # 开始预测24小时
    t_lock.acquire()
    for dt in dt_pred:
        if  (dt[0] not in data_store[t_zid]) or (dt[1] not in data_store[t_zid][dt[0]]):
            # print('predict {} {}'.format(dt[0],dt[1]))
            data_store[t_zid][dt[0]][dt[1]]={                
                'temp_unit':tmp_json['temperature']['unit'],
                'temp':math.ceil(tmp_json['temperature']['value']+random.choice(np.linspace(-6.0,6.0,13))),
                'humi':math.ceil(tmp_json['humidity']['value']+random.choice(np.linspace(-8,8,17))),
                'wind_dir':random.randint(1, 8),
                'wind_frc':random.randint(1, 5),
                'aqi':random.randint(1, 5),
                'pres':math.ceil(tmp_json['pressure']['value'])
            }
    t_lock.release()
    
    # 整理未来5天的日期
    dy_pred=get_fut_5_days(t_date)
    
    # 预测未来五天日期
    pd_lock.acquire()
    if not t_zid in pred_list:
        pred_list[t_zid]={}
    for di in dy_pred:
        # if not di in pred_list[t_zid]:
        pred_list[t_zid][di]={
            'weather_types':[random.randint(1, 3),random.randint(1, 3)],
            'temps':[random.randint(18,24),random.randint(9, 14)],
            'temp_unit':tmp_json['temperature']['unit'],
            'humis':[random.randint(45,85),random.randint(45, 85)],
            'wind_dirs':[random.randint(1, 8),random.randint(1, 8)],
            'wind_frcs':[random.randint(1, 5),random.randint(1, 5)],
            'air_idx':random.randint(1, 5),
            'wear_idx':random.randint(1, 3)
        }
    pd_lock.release()
    lls[0].insert(tk.END,'center predicted')
    btn_flag=False

def handle_datum():
    while True:
        mq_lock.acquire()
        if not meteor_q.empty():
            tmp_msg=meteor_q.get()
            mq_lock.release()

            while len(lls)!=2:
                time.sleep(1)
            
            tmp_json=json.loads(tmp_msg,encoding='utf-8')
            lls[0].insert(tk.END,'{},{} {}'.format(tmp_json['station_name'],tmp_json['date'],tmp_json['time'][0:5]))

            t_lock.acquire()
            t_zid=tmp_json['zone_id']
            if not t_zid in data_store:
                data_store[t_zid]={}
            
            t_date=tmp_json['date']
            if not t_date in data_store[t_zid]:
                data_store[t_zid][t_date]={}
            
            t_time=tmp_json['time']
            t_add={
                'temp_unit':tmp_json['temperature']['unit'],
                'temp':round(tmp_json['temperature']['value'],1),
                'humi':math.ceil(tmp_json['humidity']['value']),
                'wind_dir':math.ceil(tmp_json['direction']['value']/45.0),
                'wind_frc':math.ceil(tmp_json['velocity']['value']/2.5),
                'aqi':math.ceil(tmp_json['pm2.5']['value']/50.0),
                'pres':math.ceil(tmp_json['pressure']['value'])
            }

            data_store[t_zid][t_date][t_time]=t_add
            t_lock.release()

            # 每8小时，更新预测信息
            # if int(t_time[0:2])%8==0:
            print('center predict')
            pd_thread=threading.Thread(target=predict,args=(tmp_json,))
            pd_thread.setDaemon(True)
            pd_thread.start()
            pd_thread.join()

            
            print('center recieved from meteor {}'.format(tmp_json['station_name']))

        else :
            mq_lock.release()
def ui():
    w = tk.Tk()
    w.iconbitmap('./imgs/cld.ico')
    w.title('中心站')
    w.geometry('500x300')
    w.config(bg='white')
    f1=tk.Frame(w,bg='white')
    f1.grid(row=0,column=0,padx=30,pady=20)
    f2=tk.Frame(w,bg='white')
    f2.grid(row=0,column=1,padx=30,pady=20)

    l1=tk.Label(f1,text='来自地区站点',bg='white')
    l1.grid(row=0,column=0)
    l2=tk.Label(f2,text='来自用户',bg='white')
    l2.grid(row=0,column=0)

    ls1=tk.Listbox(f1,width=24)
    ls1.grid(row=1,column=0)
    ls2=tk.Listbox(f2,width=26)
    ls2.grid(row=1,column=0)
    # for i in range(0,8):
    #     ls1.insert(tk.END,'qhd-city,2021-04-25 {:02}:00'.format(i))
    
    # ls2.insert(tk.END,'user,qhd-city,2021-04-25 00:00')

    def clk_to_send(event):
        global btn_flag
        btn_flag=True

    def clk_to_send2(event):
        global btn_flag2
        btn_flag2=True

    btn1=tk.Button(f1,text='执行预测')
    btn1.bind('<Button-1>',clk_to_send)
    btn1.grid(row=2,column=0)

    btn2=tk.Button(f2,text='响应请求')
    btn2.bind('<Button-1>',clk_to_send2)
    btn2.grid(row=2,column=0)

    lls.append(ls1)
    lls.append(ls2)

    w.mainloop()

t_list=[
    threading.Thread(target=handle_datum),
    threading.Thread(target=interact_to_user),
    threading.Thread(target=interact_to_meteor),
    threading.Thread(target=ui)
]

if __name__ == '__main__':
    for t_i in t_list:
        t_i.setDaemon(True)
        t_i.start()
    
    for t_i in t_list:
        t_i.join()