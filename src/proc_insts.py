import json
import socket
import sys
import threading
import time
import math
import tkinter as tk
import random

import class_instruments as inst
from util_load_cfg import get_inst_action_args, get_meteor_addr

'''
仪器线程：
6个
每个仪器两个子线程：
1. 测量
2. 传输
'''

m_dir = './measure_datum/inst'
lls=[]
btn_flag=False
cur_rdy=0
cr_lock=threading.Lock()
nmd={
    'thermometer':0,
    'hygrometer':1,
    'barometer':2,
    'vane':3,
    'anemometer':4,
    'dustmeter':5,
}

class inst_wrap(threading.Thread):
    def __init__(self, m_inst):
        threading.Thread.__init__(self)
        self.m_inst = m_inst # 仪器
        self.m_socket = None # 仪器线程的socket
        self.m_json = [] # 测量的数据
        self.t_lock = threading.Lock() # 临时存储锁
        self.m_host, self.m_port = get_meteor_addr() # 地区气象站地址
        self.send_thre,self.max_day,self.max_times = get_inst_action_args()

    def open_measure_file(self):
        with open('{}/{}.json'.format(m_dir, self.m_inst.instrument_type), 'r') as jsf:
            return json.load(jsf)

    def interact_to_meteor(self):
        global btn_flag,cur_rdy
        # for i in range(0,math.ceil(self.max_times/self.send_thre)):
        # while not self.send_to_metero_flag:
        #     pass
        while not btn_flag:
            time.sleep(1)
        # self.f_lock.acquire()
        # 连接至气象站

        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_socket.connect((self.m_host, self.m_port))
        print('inst {}({}) connected'.format(
            self.m_inst.instrument_type, self.m_inst.instrument_id))

        # 获取临时存储的锁，要发送数据了
        self.t_lock.acquire()
        send_m_msg=self.m_inst.send(self.send_thre).encode('utf-8')
        # print(send_m_msg)
        
        self.m_socket.send(send_m_msg)
        self.t_lock.release()

        # 发送完毕
        print('inst {}({}) sended'.format(
            self.m_inst.instrument_type, self.m_inst.instrument_id))

        # 接收地区气象站的回信
        recv_msg = self.m_socket.recv(1024)
        self.t_lock.acquire()
        self.m_inst.receive(recv_msg.decode('utf-8'))
        self.t_lock.release()
        print('inst {}({}) recieved'.format(
            self.m_inst.instrument_type, self.m_inst.instrument_id))

        # 关闭连接
        self.m_socket.close()
        print('inst {}({}) closed'.format(
            self.m_inst.instrument_type, self.m_inst.instrument_id))
        
        lls[nmd[self.m_inst.instrument_type]].delete(0, tk.END)
        cr_lock.acquire()
        cur_rdy+=1
        cr_lock.release()

        while cur_rdy!=6:
            time.sleep(1)
        
        btn_flag=False
        
        # self.send_to_metero_flag=False
        # self.f_lock.release()
        # print('okay...')

    def run(self):
        global lls
        # self.send_thread.setDaemon(True)
        # self.send_thread.start()
        
        self.m_json = self.open_measure_file()['datum']
        for day_i in range(0, self.max_day):
            for times_i in range(0, self.max_times):
                
                while len(lls)!=6:
                    time.sleep(0.5)
                    pass

                self.t_lock.acquire()
                self.m_inst.measure(
                    self.m_json[day_i]['values'][times_i]['value'],
                    self.m_json[day_i]['date'],
                    self.m_json[day_i]['values'][times_i]['time']
                )
                self.t_lock.release()
                lls[nmd[self.m_inst.instrument_type]].insert(tk.END,'{},{} {}'.format(round(self.m_json[day_i]['values'][times_i]['value'],1),self.m_json[day_i]['date'],self.m_json[day_i]['values'][times_i]['time'][0:5]))

                if (times_i+1) % self.send_thre == 0:
                    # print('{}: day {},times {}'.format(self.m_inst.instrument_type,day_i, times_i))
                    # self.f_lock.acquire()
                    # self.send_to_metero_flag=True
                    # self.f_lock.release()
                    send_thread=threading.Thread(
                        target=inst_wrap.interact_to_meteor, args=(self,))
                    send_thread.setDaemon(True)
                    send_thread.start()
                    send_thread.join()
                    # self.interact_to_meteor()
                    
                time.sleep(0.05)
        # self.send_thread.join()
def ui():
    global lls
    vmc=['温度计','湿度计','气压计','风向标','风速计','粉尘仪']
    w = tk.Tk()
    w.iconbitmap('./imgs/cld.ico')
    w.title('仪器')
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
            # for k in range(0,6):
            #     tls.insert(tk.END,'{},2015-04-25 00:{:02}'.format(random.randint(7,15),k*5))
            pass
    
    def clk_to_send(event):
        global btn_flag,cur_rdy
        btn_flag=True
        cur_rdy=0
    
    btn1=tk.Button(w,text='发送至地区站点')
    btn1.bind('<Button-1>',clk_to_send)
    btn1.grid(row=2,column=0)

    w.mainloop()

insts = [
    threading.Thread(target=ui),
    inst_wrap(inst.thermometer(1)),
    inst_wrap(inst.hygrometer(2)),
    inst_wrap(inst.barometer(3)),
    inst_wrap(inst.anemometer(4)),
    inst_wrap(inst.vane(5)),
    inst_wrap(inst.dustmeter(6))
]

if __name__ == '__main__':
    for inst_thread in insts:
        inst_thread.setDaemon(True)
        inst_thread.start()

    for inst_thread in insts:
        inst_thread.join()
