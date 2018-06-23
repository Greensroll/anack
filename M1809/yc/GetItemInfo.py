﻿# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 01:44:29 2018

@author: yinchao
"""

 
# 远程数据库访问
import pandas as pd
import tushare as ts
import re
import urllib.request
import numpy as np
np.set_printoptions(suppress=True)
import Config


'''
list 对照表
0   总资产
1   净资产
2   资产负债比
3   流动资产
4   一年内到期的长期负债
5   应收账款
6   预收账款
7   存货

8   营业收入
9   营业成本
10  营业税金及附加
11  财务费用
12  营业外收入
13  净利润
14  除非净利润
15  每股收益

16  经营净额
17  投资净额
18  筹资净额
19  汇率影响
20  现金净增加额
21  期末现金余额

22  流动比率
23  资产周转率
24  存货周转率

25  总市值/净资
26  市盈率
27  市净率
28  名义净资产收益率
29  真实净资产收益率
30  毛利率
31  营收增长率
32  除非净利润增长率
'''
def GetSingleItem(para, stock_id, year):
    '''
    返回一个series，
    '''
    
    #
    p_len = len(para) #自动计算参数列表长度
    info = []   #实际待填充的字段，最后用于生成Series的value部分
  
    for s in range(p_len):
        info.append(-1) #初始化为-1，代表还未填充
        
    cur = Config.Connect_sql()
    
    #资产负债表中查询与填充
    cmd = "select * from zichanfuzai where h79 = \'"+stock_id+"\' and h80 = \'"+str(year)+"-12-31\';"
    cur.execute(cmd)
    result = cur.fetchall()
    result = list(result[0])
    # 此处需要把 -- 的选项替换成 0
    for i in range(len(result)):
        if result[i] == '--':
            result[i] = '0'
    
    
    data1 = result #获得资产负债表信息
    info[0] = float(data1[37].replace(',','')) #总资产
    debt = float(data1[65].replace(',','')) #总负债
    info[2] = round((debt / info[0]),2)     #资产负债比
    info[1] = info[0] - debt #净资产
    info[3] = float(data1[16].replace(',','')) #流动资产
    info[4] = float(data1[52].replace(',','')) #一年内到期的长期负债
    info[5] = float(data1[4].replace(',',''))  #应收账款
    info[6] = float(data1[42].replace(',',''))  #预收账款
    info[7] = float(data1[10].replace(',',''))  #存货
    CurrentLiabilities = float(data1[54].replace(',',''))  #预收账款
    
     #去年的资产负载表
    data1_last = result #获得去年年末资产负债表信息
    AssetLastYear = float(data1_last[37].replace(',','')) #总资产
    InventoryLastYear = float(data1_last[10].replace(',',''))  #去年存货
    
    #利润表查询与填充
    cmd = "select * from Profit where h29 = \'"+stock_id+"\' and h30 = \'"+str(year)+"-12-31\';"
    cur.execute(cmd)
    result = cur.fetchall()
    result = list(result[0])
    # 此处需要把 -- 的选项替换成 0
    for i in range(len(result)):
        if result[i] == '--':
            result[i] = '0'
    data2 = result #获得资产负债表信息
#    print(data)
    info[8] = float(data2[0].replace(',',''))  #营业收入
    info[9] = float(data2[2].replace(',',''))  #营业成本
    info[10] = float(data2[4].replace(',',''))  #营业税金及附加
    info[11] = float(data2[7].replace(',',''))  #财务费用
    LossFromAssetDevaluation = float(data2[8].replace(',',''))  #资产减值损失
    IncomeFromInvestment = float(data2[10].replace(',','')) #投资收益
    info[12] = float(data2[14].replace(',',''))  #营业外收入
    NonbusinessExpenditure = float(data2[15].replace(',',''))  #营业外支出
    info[13] = float(data2[19].replace(',',''))  #净利润
    
    #非经常性盈利损失（此处只计算了前4项，会对计算除非净利润带来不准确）
    NonRecurringProfitAndLoss = NonbusinessExpenditure + IncomeFromInvestment + LossFromAssetDevaluation
    #除非净利润=净利润-非经常性盈利损失
    info[14] = info[13] - NonRecurringProfitAndLoss  #除非净利润
    info[15] = float(data2[22].replace(',',''))  #每股收益
    stock_num = info[13]/ info[15] #股份数量
    #上一年度利润表
    cmd = "select * from Profit where h29 = \'"+stock_id+"\' and h30 = \'"+str(year-1)+"-12-31\';"
    cur.execute(cmd)
    result = cur.fetchall()
    data2_last = result[0] #获得资产负债表信息
    RevenueLast = float(data2_last[1].replace(',',''))  #营业收入
    NonbusinessIncomeLast = float(data2_last[14].replace(',',''))  #营业外收入
    IncomeFromInvestmentLast = float(data2_last[10].replace(',','')) #投资收益
    NonbusinessExpenditureLast = float(data2_last[15].replace(',',''))  #营业外支出
    LossFromAssetDevaluationLast = float(data2_last[8].replace(',',''))  #资产减值损失
    NonRecurringProfitAndLossLast = NonbusinessIncomeLast + IncomeFromInvestmentLast - NonbusinessExpenditureLast - LossFromAssetDevaluationLast
    NetProfit = float(data2_last[19].replace(',',''))  #净利润
    NullNetProfit = NetProfit - NonRecurringProfitAndLossLast
    
    #现金流量表查询与填充
    cmd = "select * from cashFlow where h72 = \'"+stock_id+"\' and h73 = \'"+str(year)+"-12-31\';"
    cur.execute(cmd)
    result = cur.fetchall()
    result = list(result[0])
    # 此处需要把 -- 的选项替换成 0
    for i in range(len(result)):
        if result[i] == '--':
            result[i] = '0'
    data3 = result #获得资产负债表信息
    info[16] = float(data3[9].replace(',','')) #经营净额
    info[17] = float(data3[21].replace(',','')) #投资净额
    info[18] = float(data3[33].replace(',','')) #筹资净额
    info[19] = float(data3[34].replace(',','')) #汇率影响
    
    #现金净增加额=现金的期末余额-现金的期初余额
    info[20] = float(data3[67].replace(',','')) - float(data3[66].replace(',',''))  #现金净增加额
    info[21] = float(data3[67].replace(',','')) #期末现金余额
    
        
    #指标计算，可能还需要获取额外的数据如实时股价等。。。
    
    #流动比率＝流动资产（3）/流动负债（h55）x100%
    info[22] = round(info[3] / CurrentLiabilities,2) #流动比率
    
    #资金周转率=本期销售收入净额（营业收入）*2/（资产总额期初余额+资产总额期末余额），期末期初按一年计算
    info[23] = round(info[8] * 2 / (info[0] + AssetLastYear),2)
    
    #存货周转率 = 营业成本 / 平均存货 ，平均存货=（期初存贷余额+期末存贷余额)/2,按一年期进行计算
    info[24] = round(info[9] * 2 / (info[7] + InventoryLastYear),2)
    
    #tushare实时数据
    '''
    per:市盈率
    pb:市净率
    mktcap:总市值
    nmc:流通市值
    '''
        
    base = 'http://hq.sinajs.cn/list='
    flag = int(stock_id)
    if flag >= 600000:
        bios = 'sh' + stock_id
    else:
        bios = 'sz' + stock_id
    inputstr = base + bios
    page = urllib.request.urlopen(inputstr).read()
    if len(page) < 30:
        print('error, invalid id')
    s = page[30:]
    s = str(s)
    
    pattern_data = '\d+\.*\d*(?=,)'
    reobj = re.compile(pattern_data)
    data = reobj.findall(s)
    cur_price = float(data[2])
    info[25] = round(cur_price * stock_num / info[0],2)
    info[26] = round(cur_price / info[15],2) #静态市盈率
    info[27] = round(info[1] / stock_num,2) #市净率
    
#    DataTushare =  (ts.get_today_all().values)[0]
#    per = DataTushare[11]
#    pb = DataTushare[12]
#    mktcap = DataTushare[13]
#    info[25] =  round(mktcap / info[1],2) #总市值/净资
#    info[26] =  per #市盈率
#    info[27] = pb #市净率
    
    #真实净资产收益率 = 净利润 * 2 / (本年期初净资产+本年期末净资产)
    NetAssetEnd = info[0] - debt
    NetAssetBegin = float(data1_last[37].replace(',','')) - float(data1_last[65].replace(',',''))
    info[28] = round(info[13] * 2 / (NetAssetEnd + NetAssetBegin),2)
    #名义净资产收益率 = 真实净资产收益率 * 市净率
#    info[29] = round(info[28] * pb,2)
    
#    #毛利率 = （营业收入 - 营业成本） / 营业成本 * 100%
    info[30] = round((info[8] - info[9]) / info[9],2)
    
#    #营收增长率 = (本年度营业收入 - 上年度营业收入) /上年度营业收入 *100%
    info[31] = round((info[8] - RevenueLast) / RevenueLast,2)
#    
#    #除非净利润增长率 = (年末 - 年初)/ 年初 * 100%
    info[32] = round((info[14] - NullNetProfit) / NullNetProfit,2)
    
    return pd.Series(info,index = para)


###############################################################################
if __name__ =='__main__':
    parameter,company_id = Config.M1809_config() #获取配置信息
    #s = GetSingleItem(parameter,company_id[0],2017)
    s = GetSingleItem(parameter,'601012',2017)
    print(s)