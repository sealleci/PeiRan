import queue
import socket
import sys
import threading
import time
import numpy as np
import json
import tkinter as tk

from util_load_cfg import get_meteor_addr,get_center_addr,get_meteor_station_info

'''
气象站线程：
1. 监听连接 
2. 处理数据
3. 向中心站点发送
'''
lls=[]
nmd={
    'thermometer':0,
    'hygrometer':1,
    'barometer':2,
    'vane':3,
    'anemometer':4,
    'dustmeter':5,
}
btn_flag=False
cur_rdy=0
cr_lock=threading.Lock()

host,port=get_meteor_addr()
station_name,station_id,zone_id=get_meteor_station_info()

t_lock=threading.Lock()
q_lock=threading.Lock()
msg_q=queue.Queue(48)
value_names_list=['temperature','humidity','pressure','direction','velocity','pm2.5']
data_store=[]
'''
{
    'date':'1900-01-01',
    'time':'00:00:00',
    'temperature':{
        'unit': 'unit',
        'values':[]
    }
}
'''
send_to_center_json={}
send_to_center_flag=False

def handle_datum():
    global send_to_center_json,send_to_center_flag
    while True:
        q_lock.acquire()
        if not msg_q.empty():
            tmp_msg=msg_q.get()
            q_lock.release()

            while len(lls)!=6:
                time.sleep(1)
            
            tmp_json=json.loads(tmp_msg,encoding='utf-8')
            print('{}({}) recieved from {}'.format(station_name,station_id,tmp_json['instrument']))

            lls[nmd[tmp_json['instrument']]].insert(tk.END,'{}条,{} {}'.format(len(tmp_json['values']),tmp_json['date'],tmp_json['time'][1][0:5]))

            idx=-1
            for i,d_i in enumerate(data_store):
                if d_i['date']==tmp_json['date'] and d_i['time']=='{}:00:00'.format(tmp_json['time'][0][0:2]):
                    idx=i
                    break
            
            if idx==-1:
                data_store.append({
                    'date':tmp_json['date'],
                    'time':'{}:00:00'.format(tmp_json['time'][0][0:2]),
                })
                idx=len(data_store)-1
            
            if tmp_json['value_name'] in data_store[idx]:
                data_store[idx][tmp_json['value_name']]['values'].extend(tmp_json['values'])
            else:
                data_store[idx][tmp_json['value_name']]={
                    'unit':tmp_json['unit'],
                    'values':tmp_json['values']
                }
        else:
            q_lock.release()
        
        if len(data_store)!=0 :
            cnt_of_ready=0
            for arg_i in value_names_list:
                if (arg_i in data_store[0]) and (len(data_store[0][arg_i]['values'])==12):
                    cnt_of_ready+=1
            
            # print('count:{}'.format(cnt_of_ready))
            if cnt_of_ready == len(value_names_list):
                send_to_center_json={
                    'station_name':station_name,
                    'station_id':station_id,
                    'zone_id':zone_id,
                    'date':data_store[0]['date'],
                    'time':data_store[0]['time']
                }

                for arg_i in value_names_list:
                    send_to_center_json[arg_i]={
                        'unit':data_store[0][arg_i]['unit'],
                        'value':round(np.mean(data_store[0][arg_i]['values']),2)
                    }
                
                data_store.pop(0)
                send_to_center_flag=True

def interact_to_center():
    global send_to_center_json,send_to_center_flag,btn_flag,cur_rdy
    center_host,center_port=get_center_addr()

    while True:
        while not send_to_center_flag:
            time.sleep(1)
            pass

        if send_to_center_json!={}:
            while not btn_flag:
                time.sleep(1)
            
            cent_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cent_socket.connect((center_host,center_port))

            cent_socket.send(json.dumps(send_to_center_json,ensure_ascii=False).encode('utf-8'))
            print('{}({}) sended to center'.format(station_name,station_id))

            recv_msg=cent_socket.recv(1024)
            tmp_json=json.loads(recv_msg,encoding='utf-8')

            if tmp_json['recieved']==1:
                send_to_center_flag=False
                send_to_center_json={}
            print('{}({}) recieved from center: {}'.format(station_name,station_id,tmp_json['recieved']))

            cent_socket.close()

            for llsi in lls:
                llsi.delete(0, tk.END)
        
            btn_flag=False

            # print(json.dumps(send_to_center_json,ensure_ascii=False))
            # send_to_center_flag=False
            # send_to_center_json={}

def interact_to_insts():
    global send_to_center_json,send_to_center_flag
    server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((host,port))
    server_socket.listen(6)
    print('meteor station listening...')

    while True:
        client_socket,addr=server_socket.accept()
        print('{}({}) accepted from {}:{}'.format(station_name,station_id,addr[0],addr[1]))

        recived_message=client_socket.recv(2048)
        ctrl_msg={'recieved':0}

        if recived_message!='':
            # print('{}({}) recieved\n{}'.format(station_name,station_id,recived_message))
            print('{}({}) recieved'.format(station_name,station_id))
            
            q_lock.acquire()
            msg_q.put(recived_message)
            q_lock.release()

            ctrl_msg['recieved']=1
        
        client_socket.send(json.dumps(ctrl_msg,ensure_ascii=False).encode('utf-8'))
        print('{}({}) sended {}'.format(station_name,station_id,ctrl_msg['recieved']))
        
        client_socket.close()
        print('{}({}) closed from {}:{}'.format(station_name,station_id,addr[0],addr[1]))

def ui():
    vmc=['温度计','湿度计','气压计','风向标','风速计','粉尘仪']
    w = tk.Tk()
    w.iconbitmap('./imgs/cld.ico')
    w.title('地区站点-秦皇岛城区')
    w.geometry('500x400')
    w.config(bg='white')

    for i in range(0,2):
        tf=tk.Frame(w,bg='white',padx=20)
        tf.grid(row=i,column=0)
        for j in range(0,3):
            tl=tk.Label(tf,text=vmc[i*3+j],bg='white')
            tl.grid(row=0,column=j)
            tls=tk.Listbox(tf,width=20,height=8)
            tls.grid(row=1,column=j)
            lls.append(tls)
            pass
    
    def clk_to_send(event):
        global btn_flag,cur_rdy
        btn_flag=True
        cur_rdy=0
    btn1=tk.Button(w,text='发送至中点站')
    btn1.bind('<Button-1>',clk_to_send)
    btn1.grid(row=2,column=0)

    w.mainloop()

t_list=[
    threading.Thread(target=interact_to_insts),
    threading.Thread(target=handle_datum),
    threading.Thread(target=interact_to_center),
    threading.Thread(target=ui)
]

if __name__ == '__main__':
    for t_i in t_list:
        t_i.setDaemon(True)
        t_i.start()
    
    for t_i in t_list:
        t_i.join()