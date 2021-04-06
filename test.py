from datetime import datetime, timedelta

curDate = datetime.now()
temp = curDate + timedelta(days=3)
temp = max(curDate, temp)
print(temp)

a = '1'
b = int(a)
print(b)