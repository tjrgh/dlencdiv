import datetime

from ubold.stocks.models import FinancialStatement
from ubold.pages import common_util

price_list = FinancialStatement.objects.filter(code="A000020").all()

def date_m(date, day):
    origin_date = common_util.iso_to_datetime(date)
    result_date = date - datetime.timedelta(days=day)
    return common_util.datetime_to_iso(result_date)
def date_p(date, day):
    origin_date = common_util.iso_to_datetime(date)
    result_date = date + datetime.timedelta(days=day)
    return common_util.datetime_to_iso(result_date)

def S(date): # 시가
    result = price_list.filter(date=date).get().open_price
    return result

def H(date): # 고가
    result = price_list.filter(date=date).get().high_price
    return result

def L(date): # 저가
    result = price_list.filter(date=date).get().low_price
    return result

def E(date): # 종가
    result = price_list.filter(date=date).get().close_price
    return result

def G(date): # 갭등락폭
    return S(date) - S(date_m(date, 1))

def Gp(date): # 갭등락률
    return (G(date)/E(date_m(date, 1))) * 100

def HLk(k): # 당일고저변동폭
    return H(k) - L(k)

def HLk3d(k): #당일고저변동폭 전3일 이평
    sum = 0
    for i in range(1, 3):
        sum = sum + HLk(date_m(k, i))
    return sum/3

def HLk5d(k):
    sum = 0
    for i in range(1, 5):
        sum = sum + HLk(date_m(k, i))
    return sum/5

def HLk10d(k):
    sum = 0
    for i in range(1, 10):
        sum = sum + HLk(date_m(k, i))
    return sum/10

def HLk20d(k):
    sum = 0
    for i in range(1, 20):
        sum = sum + HLk(date_m(k, i))
    return sum/20
def HLpk(k):
    return (HLk(k)/L(k))* 100
def HLpk3d(k):
    sum = 0
    for i in range(1, 3):
        sum = sum + HLpk(date_m(k, i))
    return sum/3
def HLpk5d(k):
    sum = 0
    for i in range(1, 5):
        sum = sum + HLpk(date_m(k, i))
    return sum / 5
def HLpk10(k):
    sum = 0
    for i in range(1, 10):
        sum = sum + HLpk(date_m(k, i))
    return sum / 10
def HLpk20(k):
    sum = 0
    for i in range(1, 20):
        sum = sum + HLpk(date_m(k, i))
    return sum / 20
def HSk(k):
    return H(k)-S(k)
def HSk3d(k):
    sum = 0
    for i in range(1, 3):
        sum = sum + HSk(date_m(k, i))
    return sum / 3
def HSk5d(k):
    sum = 0
    for i in range(1, 5):
        sum = sum + HSk(date_m(k, i))
    return sum / 5
def HSk10d(k):
    sum = 0
    for i in range(1, 10):
        sum = sum + HSk(date_m(k, i))
    return sum / 10
def HSk20d(k):
    sum = 0
    for i in range(1, 20):
        sum = sum + HSk(date_m(k, i))
    return sum / 20
def SLk(k):
    sum = 0



