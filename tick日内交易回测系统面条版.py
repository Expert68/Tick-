'-----------------tick日内策略回测系统------------------'

'-----------------------------------------------------------------------------------------------------------------------'
"""
一、策略逻辑
    1、开多仓策略:当最新价格突破开盘价longN个点时开多仓
    2、开空仓策略：当最新价格低于开盘价shortM个点时开空仓
    3、止盈止损策略：当收益大于winX时止盈，当损失大于lossX时止损
    4、强平策略：收盘的时候强行平仓，可以在配置文件中修改闭市时间
"""

"""
二、行情字段
    FutureData: tick行情字段定义
        {
            string instID //合约代码
            string date
            string time
            double buy1price
            int buy1vol
            double new1
            double sell1price
            int sell1vol
            double vol
            double openinterest //持仓量
        }
            

    持仓字段定义：
    holding字段：
        {
            string instID  //合约代码
            string date_open //开仓日期
            string time_open //开仓时间
            string open_kind //开仓方向，多仓：long，空仓：short
            int open_num //开仓量，默认1手
            double price_open //开仓价格
            double price_close //平仓价格
            double close_profit //平仓盈亏
            double price_highest_lowest //开仓后的最高和最低价格
            double close_y_n //是否已经平仓，是'yes',否'no’
            string date_close //平仓日期
            string time_close //平仓时间
            string cause_close //平仓原因
            double win_percent //盈利百分比
            double earning_all //累计盈亏
        }
        
三、代码基础架构：
    1、全局变量、保存数据的容器初始化
    2、读取并保存历史数据
    3、策略主逻辑的计算和交易记录的输出    
"""
'-----------------------------------------------------------------------------------------------------------------------'

import glob
import re
import os

log_func = open(r'output\trading_record_log.txt','a')  #写日志

list_file_name = []

history_file_name = []

historydata_list = []

close_time = '15:10:00' #强平时间

end_open_time = '15:05:00' #开仓截止时间

MIND_DIFF = 0.2  #最小变动价位

OPEN_NUM = 1 #每次开仓手数

'-----------------------------------------------------------------------------------------------------------------------'

#读取行情文件txt

for filename in glob.glob(r'input\*.txt'):
    print(filename)
    log_func.write(filename+'\n')
    list_file_name.append(filename)
    # ['input\\IF1204_20120418.txt', 'input\\IF1205_20120418.txt', 'input\\IF1206_20120418.txt',
    #  'input\\IF1209_20120418.txt']
print(list_file_name)

#保存全部txt数据到historydata_list

for txt_name in list_file_name:
    print('当前读取文件'+txt_name)
    log_func.write('当前读取文件：'+txt_name+'\n')

    m = re.findall(r'(\w*[0-9].txt+)\w*',txt_name)
    instID_date = m[0]
    log_func.write(instID_date+'\n')
    # print(instID_date)

    instID = instID_date[0:6] #获取合约代码
    # print(instID)
    log_func.write(instID+'\n')

    with open(txt_name) as f:
        for line in f:
            data = line.split('\t')
            date_time = data[1].split(' ')
            # print(date_time)
            dic = {}
            dic['instID'] = data[0]
            dic['date'] = date_time[0]
            dic['time'] = date_time[1]
            dic['buy1price'] = float(data[2])
            dic['buy1vol'] = int(data[3])
            dic['new1'] = float(data[4])
            dic['sell1price'] = float(data[5])
            dic['sell1vol'] = int(data[6])
            dic['vol'] = float(data[7])
            dic['openinterest'] = float(data[8])
            # print(dic)
            if (dic['time'] >= '09:14' and dic['time'] <= '11:30') or (dic['time'] >= '13:00' and dic['time'] <= '15:15'):
                historydata_list.append(dic)

    print('数据总条数：'+str(len(historydata_list))+'数据保存结束')
    log_func.write('数据总条数：'+str(len(historydata_list))+'数据保存结束')

'-----------------------------------------------------------------------------------------------------------------------'

#------------------参数优化模块

for longN in range(10,20,5):
    for shortM in range(10,20,5):
        for winX1 in range(35,40,3):
            for lossX2 in range(55,60,4):

                longN_str = str(longN)
                shortM_str = str(shortM)
                winX1_str = str(winX1)
                lossX2_str = str(lossX2)

                para_combination = longN_str + '_' + shortM_str + '_' + winX1_str + '_' + lossX2_str
                print('当前参数组合：',para_combination)

                #初始化各个列表，参数(一组参数初始化一次)
                holding_num = 0 #当前持仓量
                holding_list = [] #持仓表，一组参数跑完要清空一下
                earnings_all = 0 #累计盈亏
                haveopen = False #是否已经开仓
                open_price = 0 #当天开盘价

                #开始编写策略逻辑，遍历所有tick数据
                for tick_key in range(len(historydata_list)):
                    if (historydata_list[tick_key]['time'] >= '09:14' and historydata_list[tick_key]['time'] <= '11:30') or (
                            historydata_list[tick_key]['time'] >= '13:00' and historydata_list[tick_key]['time'] <= '15:15'):

                        if historydata_list[tick_key]['time']=='09:14':
                            open_price = historydata_list[tick_key]['new1']
                            print('当天开盘价：'+open_price)
                            log_func.write('当天开盘价：'+open_price+'\n')

        #-----------------------------平仓模块，包含强平模块和止盈止损模块
                        if historydata_list[tick_key]['time'] >= close_time:
                            haveopen = False  #手中无仓位，下一个交易日需要再开仓

                            for holding_key in range(len(holding_list)):
                                #未平仓，进行收盘强平
                                if holding_list[holding_key]['close_y_n'] == 'no':
                                    log_func.write('收盘强平'+'\n')

                                    if holding_list[holding_key]['open_kind'] == 'long':  #多仓平仓
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['buy1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_close'] - holding_list[holding_key]['price_open']

                                    else:
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['sell1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_open'] - holding_list[holding_key]['price_close']

                                    holding_list[holding_key]['close_y_n'] = 'yes'
                                    holding_list[holding_key]['date_close'] = historydata_list[tick_key]['date']
                                    holding_list[holding_key]['time_close'] = historydata_list[tick_key]['time']

                                    earnings_all += holding_list[holding_key]['close_profit']
                                    holding_list[holding_key]['earnings_all'] = earnings_all

                                    holding_num = holding_num - OPEN_NUM

        #-----------------------------止盈止损模块
                        else:
                            for holding_key in range(len(holding_list)):
                                if holding_list[holding_key]['close_y_n'] == 'no' and holding_list[holding_key]['open_kind'] == 'long':
                                    if historydata_list[tick_key]['buy1price'] - holding_list[holding_key]['price_open'] >= winX1*MIND_DIFF:
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['buy1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_close'] - holding_list[holding_key]['price_open']
                                        holding_list[holding_key]['close_y_n'] = 'yes'
                                        holding_list[holding_key]['date_close'] = historydata_list[tick_key]['date']
                                        holding_list[holding_key]['time_close'] = historydata_list[tick_key]['time']
                                        holding_list[holding_key]['cause_close'] = '止盈'

                                        earnings_all += holding_list[holding_key]['close_profit']
                                        holding_list[holding_key]['earnings_all'] = earnings_all

                                        haveopen = False
                                        holding_num = holding_num - OPEN_NUM
                                        #print('多单止盈')
                                        log_func.write('多单止盈'+'\n')

                                    elif holding_list[holding_key]['price_open'] - historydata_list[tick_key]['buy1price'] >= lossX2*MIND_DIFF:
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['buy1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_close'] - holding_list[holding_key]['price_open']
                                        holding_list[holding_key]['close_y_n'] = 'yes'
                                        holding_list[holding_key]['date_close'] = historydata_list[tick_key]['date']
                                        holding_list[holding_key]['time_close'] = historydata_list[tick_key]['time']
                                        holding_list[holding_key]['cause_close'] = '止损'

                                        earnings_all += holding_list[holding_key]['close_profit']
                                        holding_list[holding_key]['earnings_all'] = earnings_all

                                        haveopen = False
                                        holding_num = holding_num - OPEN_NUM
                                        #print('多单止损')
                                        log_func.write('多单止损'+'\n')

                                elif holding_list[holding_key]['close_y_n'] == 'no' and holding_list[holding_key]['open_kind'] == 'short':
                                    if holding_list[holding_key]['price_open'] - historydata_list[tick_key]['sell1price'] >= winX1*MIND_DIFF:
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['sell1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_open'] - holding_list[holding_key]['price_close']
                                        holding_list[holding_key]['close_y_n'] = 'yes'
                                        holding_list[holding_key]['date_close'] = historydata_list[tick_key]['date']
                                        holding_list[holding_key]['time_close'] = historydata_list[tick_key]['time']
                                        holding_list[holding_key]['cause_close'] = '止盈'

                                        earnings_all += holding_list[holding_key]['close_profit']
                                        holding_list[holding_key]['earnings_all'] = earnings_all

                                        haveopen = False
                                        holding_num = holding_num - OPEN_NUM
                                        #print('空单止盈')
                                        log_func.write('空单止盈'+'\n')

                                    elif historydata_list[tick_key]['sell1price'] - holding_list[holding_key]['price_open'] >= lossX2*MIND_DIFF:
                                        holding_list[holding_key]['price_close'] = historydata_list[tick_key]['sell1price']
                                        holding_list[holding_key]['close_profit'] = holding_list[holding_key]['price_open'] - holding_list[holding_key]['price_close']
                                        holding_list[holding_key]['close_y_n'] = 'yes'
                                        holding_list[holding_key]['date_close'] = historydata_list[tick_key]['date']
                                        holding_list[holding_key]['time_close'] = historydata_list[tick_key]['time']
                                        holding_list[holding_key]['cause_close'] = '止盈'

                                        earnings_all += holding_list[holding_key]['close_profit']
                                        holding_list[holding_key]['earnings_all'] = earnings_all

                                        haveopen = False
                                        holding_num = holding_num - OPEN_NUM
                                        #print('空单止损')
                                        log_func.write('空单止损'+'\n')

        # -----------------------------开仓模块

                        if historydata_list[tick_key]['time'] > '09:14' and historydata_list[tick_key]['time'] <= end_open_time:
                            if historydata_list[tick_key]['new1'] >= open_price+longN*MIND_DIFF and historydata_list[tick_key-1]['new1'] < open_price+longN*MIND_DIFF and haveopen==False:
                                print('开多')

                                log_func.write('开多'+'\n')
                                haveopen = True

                                holding_num = holding_num + OPEN_NUM

                                holding_dic = {}
                                holding_dic['instID'] = historydata_list[tick_key]['instID']
                                holding_dic['date_open'] = historydata_list[tick_key]['date']
                                holding_dic['time_open'] = historydata_list[tick_key]['time']
                                holding_dic['open_kind'] = 'long'
                                holding_dic['open_num'] = OPEN_NUM
                                holding_dic['price_open'] = historydata_list[tick_key]['sell1price']
                                holding_dic['close_y_n'] = 'no'

                                holding_list.append(holding_dic)

                            elif historydata_list[tick_key]['new1'] <= open_price - shortM * MIND_DIFF and \
                                    historydata_list[tick_key - 1][
                                        'new1'] > open_price - shortM * MIND_DIFF and haveopen == False:
                                print('开空')

                                log_func.write('开空' + '\n')
                                haveopen = True

                                holding_num = holding_num + OPEN_NUM

                                holding_dic = {}
                                holding_dic['instID'] = historydata_list[tick_key]['instID']
                                holding_dic['date_open'] = historydata_list[tick_key]['date']
                                holding_dic['time_open'] = historydata_list[tick_key]['time']
                                holding_dic['open_kind'] = 'short'
                                holding_dic['open_num'] = OPEN_NUM
                                holding_dic['price_open'] = historydata_list[tick_key]['buy1price']
                                holding_dic['close_y_n'] = 'no'

                                holding_list.append(holding_dic)


                path = os.path.join(r'output',('trading_record'+para_combination+'.txt'))
                with open(path,'a',encoding='utf-8') as f:
                    for holding_key in range(len(holding_list)):
                        f.write(holding_list[holding_key]['instID']+','+holding_list[holding_key]['date_open']+','+holding_list[holding_key]['time_open']
                                +','+holding_list[holding_key]['open_kind']+','+str(holding_list[holding_key]['open_num'])+','+str(holding_list[holding_key]['price_open'])
                                +','+str(holding_list[holding_key]['price_close'])+',' + str(holding_list[holding_key]['close_profit']) + ',' + holding_list[holding_key]['close_y_n']
                                +','+holding_list[holding_key]['date_close'] + ',' + holding_list[holding_key]['time_close'] + ',' + holding_list[holding_key]['cause_close']
                                +','+str(holding_list[holding_key]['earnings_all']) + '\n')


                print('-------------------------遍历完全部数据，策略逻辑结束，参数组合：' + para_combination)
                log_func.write("-------------------------遍历完全部数据，策略逻辑结束，参数组合：" + para_combination + '\n')
log_func.close()















