import time
import json

# 数据格式
class measured_data:
    def __init__(self, name: str, unit: str, value,measure_date:str, measure_time: str):
        self.name = name  # 名字
        self.unit = unit  # 单位
        self.value = value  # 数值
        self.measure_date = measure_date
        self.measure_time = measure_time  # 测量的时间

    def __str__(self) -> str:
        return '{}({}): {:.3}, at {} {}'.format(self.name, self.unit, self.value,self.measure_date, self.measure_time)

# 气象仪器基类
class meteorologist_instrument(object):
    def __init__(self, instrument_type: str, instrument_id: int, value_name: str, value_unit: str, toggle: bool, send_cycle: int, measure_cycle: int):
        self._instrument_type = instrument_type  # 设备种类，字符串
        self._instrument_id = instrument_id  # 设备序号，整数
        self._value_name = value_name  # 测量数值名称
        self._value_unit = value_unit  # 测量数值单位
        self._toggle = toggle  # 仪器启动状态，布尔
        self._send_cycle = send_cycle  # 发送数据周期，毫秒
        self._measure_cycle = measure_cycle  # 测量数据周期，毫秒
        self._datum = []  # 一段时间内测量的数据列表，list
        self._last_tail = -1  # 上一次发送列表时最后一项的索引，闭区间

    @property
    def instrument_type(self) -> str:
        return self._instrument_type

    @property
    def instrument_id(self) -> int:
        return self._instrument_id

    @property
    def value_name(self) -> str:
        return self._value_name

    @property
    def value_unit(self) -> str:
        return self._value_unit

    @property
    def toggle(self) -> bool:
        return self._toggle

    @toggle.setter
    def toggle(self, state: bool):
        self._toggle = state

    @property
    def send_cycle(self) -> int:
        return self._send_cycle

    @send_cycle.setter
    def send_cycle(self, cycle: int):
        self._send_cycle = cycle

    @property
    def measure_cycle(self) -> int:
        return self._measure_cycle

    @measure_cycle.setter
    def measure_cycle(self, cycle: int):
        self._measure_cycle = cycle

    def measure(self, value,measure_date:str, measure_time: str):  # 测量数据，装入列表
        self._datum.append(measured_data(
            self._value_name, self._value_unit, value,measure_date, measure_time))

    def send(self,count) -> str:  # 发送数据
        '''
        report
        # instrument(id)
        1. name(unit): value, at 19xx-01-01 00:00:00
        '''
        # report = 'report\n# {}({})\n'.format(
        #     self._instrument_type, self._instrument_id)
        # for (i, data) in enumerate(self._datum):
        #     report = report+'{}. {}\n'.format(i+1, data)
        # print('{}: len{}'.format(self._instrument_type,len(self._datum)))
        report = {
            'instrument': self._instrument_type,
            'inst_id': self._instrument_id,
            'value_name': self._value_name,
            'unit': self._value_unit,
            'date':self._datum[0].measure_date,
            'time':[self._datum[0].measure_time,self._datum[-1].measure_time],
            'values': [],
        }
        for i in range(0,count):
            report['values'].append(self._datum[i].value)
        
        self._last_tail = count-1

        return json.dumps(report, ensure_ascii=False)

    def receive(self, control:str):  # 发送成功，清空列表
        control=json.loads(control,encoding='utf-8')
        if control['recieved'] == 1:
            self._datum = self._datum[self._last_tail+1:]
            self._last_tail = -1

# 温度计
class thermometer(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(thermometer, self).__init__(
            'thermometer', instrument_id, 'temperature', 'oC', False, 600, 100)

# 湿度计
class hygrometer(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(hygrometer, self).__init__(
            'hygrometer', instrument_id, 'humidity', 'RH', False, 600, 100)

# 气压计
class barometer(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(barometer, self).__init__(
            'barometer', instrument_id, 'pressure', 'hPa', False, 600, 100)

# 风速计
class anemometer(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(anemometer, self).__init__(
            'anemometer', instrument_id, 'velocity', 'm/s', False, 600, 100)

# 风向标
class vane(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(vane, self).__init__('vane', instrument_id,
                                   'direction', 'o', False, 600, 100)

# 粉尘计
class dustmeter(meteorologist_instrument):
    def __init__(self, instrument_id: int):
        super(dustmeter, self).__init__(
            'dustmeter', instrument_id, 'pm2.5', 'ug/m3', False, 600, 100)


class meteorological_station(object):
    def __init__(self, station_id: int):
        self.station_id = station_id
        self._instruments = []
        self._server = None

    def add_instrument(self, instrument):
        self._instruments.append(instrument)