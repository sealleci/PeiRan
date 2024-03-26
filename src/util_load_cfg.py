import json

def get_meteor_addr():
    host='127.0.0.1'
    port=1919
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        host=json_data['meteor_host']
        port=json_data['meteor_port']
    return (host,port)

def get_center_addr():
    host='127.0.0.1'
    port=810
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        host=json_data['center_host']
        port=json_data['center_port']
    return (host,port)

def get_global_addr():
    host='127.0.0.1'
    port=514
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        host=json_data['global_host']
        port=json_data['global_port']
    return (host,port)

def get_inst_action_args():
    send_thre=6
    max_days=1
    max_times=24
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        send_thre=json_data['inst_send_thre']
        max_days=json_data['inst_max_days']
        max_times=json_data['inst_max_times']
    return (send_thre,max_days,max_times)

def get_meteor_station_info():
    station_name='qhd-city'
    station_id=1
    zone_id=101091101
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        station_name=json_data['meteor_station_name']
        station_id=json_data['meteor_station_id']
        zone_id=json_data['meteor_zone_id']
    return (station_name,station_id,zone_id)

def get_zone_id():
    zone_id=101091101
    with open('./config.json','r') as cfg_file:
        json_data=json.load(cfg_file)
        zone_id=json_data['meteor_zone_id']
    return zone_id

if __name__ == '__main__':
    print(get_inst_action_args(),get_meteor_addr())