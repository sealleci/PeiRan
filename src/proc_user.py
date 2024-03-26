import json
import math
import random
import time
import threading
import time
import numpy as np
import socket
import tkinter as tk
import matplotlib.pyplot as plt 
from scipy.interpolate import make_interp_spline
from matplotlib.pylab import mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from util_load_cfg import get_global_addr,get_zone_id

'''
用户进程
1. 界面
2. 向中心站互动
'''
zone_id=get_zone_id()
wls=[]
fls=[]
tplot=[]

pre_time=''

def interact_to_center():
    global gjs,pre_time
    host,port=get_global_addr()
    while len(wls)!=2 and len(fls)!=2:
        time.sleep(1)
    while True:
        tmpd=wls[0].get()
        tmpt=wls[1].get()

        if tmpd!='date' and tmpt!='time':
            if pre_time==tmpt:
                continue
            else:
                pre_time=tmpt
            req_msg={
                'user_id':1,
                'zone_id':zone_id,
                'date':tmpd,
                'time':'{}:00'.format(tmpt)
            }
            cent_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cent_socket.connect((host,port))

            cent_socket.send(json.dumps(req_msg,ensure_ascii=False).encode('utf-8'))
            print('user send request to center')

            recv_msg=cent_socket.recv(80000)
            # print(recv_msg)

            recv_json=json.loads(recv_msg,encoding='utf-8')
            print('success:{}'.format(recv_json['success']))

            if recv_json['recieved']==1 and recv_json['success']==1:
                gjs=recv_json
                # print('user recieved from center: {}'.format(recv_json))
                asm_update(fls[0])
                create_hours(fls[1])

            cent_socket.close()
        
        time.sleep(1)

gjs={}

def load_default():
    global gjs
    root_dir='./measure_datum/user'
    with open('{}/{}.json'.format(root_dir,'default'),'r',encoding='utf-8') as jsf:
        jsd=json.load(jsf)
        gjs=jsd
        # dt1=[]
        # dt2=[]
        # for di in jsd['future_days']:
        #     dt1.append(di['temps'][0])
        #     dt2.append(di['temps'][1])
        # x=np.array(list(range(1,len(dt1)+1)))
        # dt1=np.array(dt1)
        # dt2=np.array(dt2)

        # xnew=np.linspace(x.min(), x.max(),50)
        # dt1new=make_interp_spline(x,dt1)(xnew)
        # dt2new=make_interp_spline(x,dt2)(xnew)

        # plt.figure(figsize=(3.6,3))
        # plt.plot(xnew,dt1new,color='orange')
        # plt.plot(xnew,dt2new,color='cyan')

        # for i in x:
        #     plt.text(i,dt1[i-1]+1,'{}°'.format(dt1[i-1]),fontsize=10)
        #     plt.text(i,dt2[i-1]-2.2,'{}°'.format(dt2[i-1]),fontsize=10)

        # plt.xticks([])
        # plt.yticks([])
        # plt.axis('off')
        # plt.show()
        # print(jsd)

def create_hours(master):
    for widget in master.winfo_children():
        widget.destroy()
    wd={1:'晴',2:'多云',3:'阴'}
    hs=[]
    ws=[]
    ts=[]
    for di in gjs['future_hours']:
        hs.append(di['time'][0:2])
        ws.append(di['weather_type'])
        ts.append(round(di['temp']))
    # print(hs)
    for i in range(0,6):
        tf=tk.Frame(master,bg='white')
        for j in range(0,4):
            tl=tk.Label(tf,text='{}时\n{}\n  {}°'.format(hs[i*4+j],wd[ws[i*4+j]],ts[i*4+j]),bg='white')
            if i==0 and j==0:
                tl.config(bg='darkorange',fg='white')
            tl.config(font=('黑体',12,'normal'))
            tl.pack(side='left',padx=16,pady=10)
        tf.pack()

def create_date_text(master):
    for widget in master.winfo_children():
        widget.destroy()
    wd={1:'晴',2:'多云',3:'阴'}
    for i,di in enumerate(gjs['future_days']):
        w1=di['weather_types'][0]
        w2=di['weather_types'][1]
        ttxt=''
        if w1==w2:
            ttxt=wd[w1]
        else:
            ttxt='{}转{}'.format(wd[w1],wd[w2])
        tl=tk.Label(master,text='{}\n{}'.format(di['date'][5:],ttxt),bg='white')
        tl.pack(side='left',padx=12)

def create_wind_text(master):
    for widget in master.winfo_children():
        widget.destroy()
    wd={
        0:'微风',
        1:'东北风',
        2:'东风',
        3:'东南风',
        4:'南风',
        5:'西南风',
        6:'西风',
        7:'西北风',
        8:'北风'
    }
    for i,di in enumerate(gjs['future_days']):
        w1=di['wind_frcs'][0]
        w2=di['wind_frcs'][1]
        ttxt=''
        if w1==w2:
            ttxt='{}级'.format(w1)
        else:
            ttxt='{}-{}级'.format(min(w1,w2),max(w1,w2))
        tl=tk.Label(master,text='{}\n{}'.format(wd[di['wind_dirs'][0]],ttxt),bg='white')
        tl.pack(side='left',padx=16)

def create_plot(fig_plot):
    dt1=[]
    dt2=[]
    for di in gjs['future_days']:
        dt1.append(di['temps'][0])
        dt2.append(di['temps'][1])
    print('t: {}'.format(dt1))
    x=np.array(list(range(1,len(dt1)+1)))
    dt1=np.array(dt1)
    dt2=np.array(dt2)

    xnew=np.linspace(x.min(), x.max(),50)
    dt1new=make_interp_spline(x,dt1)(xnew)
    dt2new=make_interp_spline(x,dt2)(xnew)
    
    # fig_plot=fig.add_subplot(111)
    fig_plot.clear()
    fig_plot.plot(xnew,dt1new,color='orange')
    fig_plot.plot(xnew,dt2new,color='cyan')

    for i in x:
        fig_plot.text(i-0.1,dt1[i-1]-1.4,'{}°'.format(dt1[i-1]),fontsize=10)
        fig_plot.text(i-0.1,dt2[i-1]+0.8,'{}°'.format(dt2[i-1]),fontsize=10)
    fig_plot.axis('off')
    # cvn.draw()

img_t=None
def asm_update(master):
    global img_t
    # print('len',len(master.winfo_children()))
    for widget in master.winfo_children():
        widget.destroy()
    
    f_dtext=tk.Frame(master,bg='white')
    create_date_text(f_dtext)

    f_wdtext=tk.Frame(master,bg='white')
    create_wind_text(f_wdtext)

    f_dtext.pack()

    fig=Figure(figsize=(3.6,3.6))
    fig_plot=fig.add_subplot(111)
    fig.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0)
    fig.gca().xaxis.set_major_locator(plt.NullLocator())
    fig.gca().yaxis.set_major_locator(plt.NullLocator()) 
    # fig.patch.set_alpha(0.)
    # cvn=FigureCanvasTkAgg(fig,master=master)
    create_plot(fig_plot)
    # cvn.draw()
    # cvn.get_tk_widget().pack()
    fig.savefig('./imgs/t.png')
    img_t=tk.PhotoImage(file='./imgs/t.png')
    imgl=tk.Label(master=master,image=img_t,bg='white')
    imgl.pack()
    f_wdtext.pack()

def ui():
    global gjs
    w = tk.Tk()
    w.iconbitmap('./imgs/cld.ico')
    w.title('Celecloud')
    w.geometry('360x640')
    w.config(bg='white')
    
    f_h1=tk.Frame(w,bg='white')
    f_h2=tk.Frame(w,bg='white')
    f_fd=tk.Frame(w,bg='white')
    f_fh=tk.Frame(w,bg='white')

    cur_d=tk.StringVar(w)
    cur_d.set('date')
    cur_t=tk.StringVar(w)
    cur_t.set('time')
    
    op_d=tk.OptionMenu(f_h1,cur_d,'2021-04-25')
    op_d.config(bg='white',border=0)
    op_t=tk.OptionMenu(f_h1,cur_t,*[ti for ti in map(lambda x:'{:02}:00'.format(x),range(0,7))])
    op_t.config(bg='white',border=0)

    def click_switch(event):
        btn_text=event.widget['text']
        if btn_text=='近日天气':
            f_fd.pack(pady=30)
            f_fh.pack_forget()
            d_btn.config(bg='deeppink',fg='white')
            h_btn.config(fg='black',bg='white')
        else:
            f_fd.pack_forget()
            f_fh.pack(pady=40)
            h_btn.config(bg='deeppink',fg='white')
            d_btn.config(fg='black',bg='white')

    fig=Figure(figsize=(3.6,3.6))
    
    d_btn=tk.Button(f_h2,text='近日天气',bg='deeppink',fg='white',relief=tk.GROOVE,border=0,activebackground='grey')
    h_btn=tk.Button(f_h2,text='逐时预报',bg='white',relief=tk.GROOVE,border=0,activebackground='grey')

    d_btn.bind('<Button-1>',click_switch)
    h_btn.bind('<Button-1>',click_switch)
    
    l1=tk.Label(f_fd,text='days')
    l2=tk.Label(f_fh,text='hours')



    # f_dtext=tk.Frame(f_fd,bg='white')

    # create_date_text(f_dtext)

    # f_wdtext=tk.Frame(f_fd,bg='white')

    # create_wind_text(f_wdtext)
    asm_update(f_fd)
    create_hours(f_fh)

    f_h1.pack(pady=5)
    f_h2.pack()
    f_fd.pack(pady=10)
    f_fh.pack_forget()

    # f_dtext.pack()

    op_d.pack(side=tk.LEFT)
    op_t.pack()
    d_btn.pack(side=tk.LEFT)
    h_btn.pack()
    # l1.pack()
    # l2.pack()
    
    # cvn=FigureCanvasTkAgg(fig,master=f_fd)
    # create_plot(fig,cvn)
    # cvn.get_tk_widget().pack()
    # f_wdtext.pack()

    wls.append(cur_d)
    wls.append(cur_t)

    # fls.append(f_dtext)
    # fls.append(f_wdtext)
    fls.append(f_fd)
    fls.append(f_fh)

    # tplot.append(fig)
    # tplot.append(cvn)

    w.mainloop()

t_list=[
    threading.Thread(target=interact_to_center),
    threading.Thread(target=ui)
]

if __name__ == '__main__':
    load_default()
    for t_i in t_list:
        t_i.setDaemon(True)
        t_i.start()
    
    for t_i in t_list:
        t_i.join()
    pass