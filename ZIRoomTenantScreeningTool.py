#! python3
#需要安装：requests和lxml库
#初始版本，利用该脚本可以对自如合租房屋已入住的人员的性别和职业进行筛选。
#1.完成对应职业，以及性别的筛选功能。
#2.增加一些异常的处理，例如没有职业信息，例如房源过少自动加入其它小区房源。
#3.增加二种模式，用于处理入住人员性别特别少的女性或无女性时进行宽松结果返回。
#4.增加返回房屋内总房间数量功能。
#5.增加返回房屋内已入住女性数量。
#6.解决使用代理时会存在错误问题，默认不使用任何代理。
#7.优化请求次数，现在单个房间网页只会访问一次。
#8.增加显示房间号和入住时间信息

#Bug
#1.根据职业列表筛选有问题
#1.1筛选房间数量会根据职业列表数量增加的BUG，主要是一个职业会循环一次
#1.2如果职业列表中的多个职业同时存在一间房时，可能房间会打印多次
#2.房间要求多数女性时返回存在问题

#方式一：禁用代理
#session = requests.Session()
#session.trust_env = False
#response = session.get('https://www.baidu.com/')

#方式二：禁用代理
# proxies = {
  # "http": None,
  # "https": None,
# }

# # 使用代理
# proxy = '115.203.28.25:16584'
# proxies = {
    # "http": "http://%(proxy)s/" % {'proxy': proxy},
    # "https": "http://%(proxy)s/" % {'proxy': proxy}
# } 
# response = requests.get("https://www.baidu.com/", proxies=proxies)

#引用库
import requests
import sys
import os
from lxml import html

#----------------------------------------------------------------------------------------------------------------------------------
#判断函数区
#----------------------------------------------------------------------------------------------------------------------------------

#判断已入住人员的职业和性别
def CheckOccupationInformation(roominformationdata,gender,occupation):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    numberofoccupations = 0
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        #判断是否存在未填写职业的租客
        if len(individualroominformationdecoding) == 3:
            if(individualroominformationdecoding[0] == gender and individualroominformationdecoding[2] == occupation):
                numberofoccupations += 1
    return numberofoccupations
    
#判断所有已入住人员的性别中是否有女  
def RoomScreening_Woman(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    if(len(roominformation) == 0):
        return False
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        if(len(individualroominformationdecoding) == 0):
            return False
        if(individualroominformationdecoding[0] == "女"):
            return True
    return False
    
#判断所有已入住人员的性别是否不为男
def RoomScreening_Man(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    if(len(roominformation) == 0):
        return False
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        if(len(individualroominformationdecoding) == 0):
            return False
        if(individualroominformationdecoding[0] == "男"):
            return False
    return True

# 判断已入住人员女性是否大于等于男性
def MajorityGender(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    if(len(roominformation) == 0):
        return False
    Gender_Man = 0
    Gender_Woman = 0
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        if(len(individualroominformationdecoding) == 0):
            return False
        if(individualroominformationdecoding[0] == "男"):
            Gender_Man += 1
        if(individualroominformationdecoding[0] == "女"):
            Gender_Woman += 1     
    if(Gender_Woman >= Gender_Man):
        return True
    return False

#----------------------------------------------------------------------------------------------------------------------------------
#获取函数区
#----------------------------------------------------------------------------------------------------------------------------------

#获取指定小区所有房屋信息URL
def GetMultiPageCellScreening(areacode, communityname):
    i = 1
    houseurls=[]
    while True:
        houseurl = GetSinglePageCellScreening("http://" + areacode + ".ziroom.com/z/p" + str(i) + "/?qwd=" + communityname, communityname)
        if len(houseurl) == 0:
            break
        houseurls.extend(houseurl)
        i += 1
    return houseurls

#获取指定小区单页所有房屋信息URL
def GetSinglePageCellScreening(url, communityname):
    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
    sessionobj = requests.Session()
    sessionobj.trust_env = False
    page = sessionobj.get(url, headers=header)
    fromobj = html.fromstring(page.text)
    #判断是否未空页面，空页面直接返回空数组
    if len(fromobj.xpath('//div[@class="Z_list-stat Z_list-empty"]')) != 0:
        return []  
    #防止搜索的房屋过少自动将其它小区房屋信息加入
    housename = fromobj.xpath('//div[@class="info-box"]//a/text()')
    houseinformation = fromobj.xpath('//div[@class="info-box"]//a/@href')
    houseurl = []
    for i in range(len(housename)):
        name = housename[i]
        if name.find(communityname) != -1:
            houseurl.append(houseinformation[i])
    return houseurl

#获取完整的单套房屋信息URL
def GetRoominPathProcessing(path):
    path = "https:" + path
    return path

#获取单套房屋信息
def GetRoomInformation(url):
    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
    sessionobj = requests.Session()
    sessionobj.trust_env = False
    page = sessionobj.get(url, headers=header)
    fromobj = html.fromstring(page.text)
    return fromobj

# 获取单套房屋已入住女性人数
def GetRoomNumber_Woman(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    if(len(roominformation) == 0):
        return 0
    Gender_Woman = 0
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        if(len(individualroominformationdecoding) == 0):
            return 0
        if(individualroominformationdecoding[0] == "女"):
            Gender_Woman += 1     
    return Gender_Woman

#获取单套房屋的总房间数量
def GetTotalNumberOfRooms(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    return len(roominformation)

#获取单套房屋的空余房间数量
def GetEmptyRoom(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rent"]')
    return len(roominformation)

#获取指定房间已入住人员职业信息
def GetJobInformation(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    jobinformation = []
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person mt10"]/span/text()')
        #判断是否存在未填写职业的租客
        if len(individualroominformationdecoding) != 3:
            jobinformation.append("未知")
        else:
            jobinformation.append(individualroominformationdecoding[2])
    return jobinformation

#获取指定房间已入住人员房间号信息
def GetRoomNumberInformation(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    jobinformation = []
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person"]/span/text()')
        jobinformation.append(individualroominformationdecoding[0])
    return jobinformation

#获取指定房间已入住人员已住时间信息
def GetElapsedTimeInformation(roominformationdata):
    roominformation = roominformationdata.xpath('//li[@class="rented clearfix"]')
    jobinformation = []
    for i in roominformation:
        roominformationdecoding = html.tostring(i, encoding="utf-8").decode('utf-8')
        individualroominformation = html.fromstring(roominformationdecoding)
        individualroominformationdecoding = individualroominformation.xpath('//p[@class="person"]/span/text()')
        jobinformation.append(individualroominformationdecoding[1])
    return jobinformation

#主函数
def Main():
    #设置自动筛选的小区
    cellname = ["万润家园"]
    #设置那个城市 北京是www开头
    city = "www"
    #设置自动筛选的职业
    occupation =["银行","设计规划"]
    #设置清空控制台
    os.system('cls')
    print("\033[36m自如租客筛选工具 V1.0\033[0m")
    #默认参数
    if len(sys.argv) < 2:
        sys.argv.append("-?")
    #模式一（已入住人员必须全部是女性或空房间）
    #根据指定小区名筛选
    if(sys.argv[1] == "-m"):
        cellpath = GetMultiPageCellScreening(city, sys.argv[2])
        print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (sys.argv[2], len(cellpath)))
        numberofnoncomplianthouses = 0
        for i in cellpath:
            roominpath = GetRoominPathProcessing(i)
            roominformationdata= GetRoomInformation(roominpath)
            if(RoomScreening_Man(roominformationdata)):
                #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
            else:
                numberofnoncomplianthouses += 1
        print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据列表小区名筛选
    elif(sys.argv[1] == "-a"):
        for i in cellname:
            cellpath = GetMultiPageCellScreening(city, i)
            print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (i, len(cellpath)))
            numberofnoncomplianthouses = 0
            for i in cellpath:
                roominpath = GetRoominPathProcessing(i)
                roominformationdata= GetRoomInformation(roominpath)
                if(RoomScreening_Man(roominformationdata)):
                    #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                else:
                    numberofnoncomplianthouses += 1
            print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据指定小区名和指定职业筛选（任意一间已入住的人员信息符合即返回）
    elif(sys.argv[1] == "-mo"):
        cellpath = GetMultiPageCellScreening(city, sys.argv[2])
        print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (sys.argv[2], len(cellpath)))
        numberofnoncomplianthouses = 0
        for i in cellpath:
            roominpath = GetRoominPathProcessing(i)
            roominformationdata= GetRoomInformation(roominpath)
            if(CheckOccupationInformation(roominformationdata,"女",sys.argv[3])):
                    #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[01m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
            else:
                numberofnoncomplianthouses += 1
        print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据指定小区名和列表职业筛选（任意一间已入住的人员信息符合即返回）
    elif(sys.argv[1] == "-ms"):
        cellpath = GetMultiPageCellScreening(city, sys.argv[2])
        print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (sys.argv[2], len(cellpath)))
        numberofnoncomplianthouses = 0
        for i in cellpath:
            roominpath = GetRoominPathProcessing(i)
            roominformationdata= GetRoomInformation(roominpath)
            for i in occupation:
                if(CheckOccupationInformation(roominformationdata,"女",i)):
                    #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[01m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                else:
                    numberofnoncomplianthouses += 1
        print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据列表小区名和指定职业筛选（任意一间已入住的人员信息符合即返回）
    elif(sys.argv[1] == "-ao"):
        for i in cellname:
            cellpath = GetMultiPageCellScreening(city, i)
            print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (i, len(cellpath)))
            numberofnoncomplianthouses = 0
            for i in cellpath:
                roominpath = GetRoominPathProcessing(i)
                roominformationdata= GetRoomInformation(roominpath)
                if(CheckOccupationInformation(roominformationdata,"女",sys.argv[2])):
                    #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                else:
                    numberofnoncomplianthouses += 1
            print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据列表小区名和列表职业筛选（任意一间已入住的人员信息符合即返回）
    elif(sys.argv[1] == "-as"):
        for i in cellname:
            cellpath = GetMultiPageCellScreening(city, i)
            print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (i, len(cellpath)))
            numberofnoncomplianthouses = 0
            for i in cellpath:
                roominpath = GetRoominPathProcessing(i)
                roominformationdata= GetRoomInformation(roominpath)
                for i in occupation:
                    if(CheckOccupationInformation(roominformationdata,"女",i)):
                        #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                        print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    else:
                        numberofnoncomplianthouses += 1
            print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #模式二（已入住人员女性比例要大于或等于男性）
    #根据列表小区筛选
    elif(sys.argv[1] == "-ae"):
        for i in cellname:
            cellpath = GetMultiPageCellScreening(city, i)
            print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (i, len(cellpath)))
            numberofnoncomplianthouses = 0
            for i in cellpath:
                roominpath = GetRoominPathProcessing(i)
                roominformationdata= GetRoomInformation(roominpath)
                if(MajorityGender(roominformationdata)):
                    #print("\033[0m[\033[32m+\033[0m]总房间数量:\033[31m%d\033[0m间 剩余空房间数量:\033[31m%d\033[0m间 已入住女性人数:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetTotalNumberOfRooms(roominformationdata), GetEmptyRoom(roominformationdata), GetRoomNumber_Woman(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                else:
                    numberofnoncomplianthouses += 1
            print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据指定小区名筛选
    elif(sys.argv[1] == "-me"):
        cellpath = GetMultiPageCellScreening(city, sys.argv[2])
        print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (sys.argv[2], len(cellpath)))
        numberofnoncomplianthouses = 0
        for i in cellpath:
            roominpath = GetRoominPathProcessing(i)
            roominformationdata= GetRoomInformation(roominpath)
            if(MajorityGender(roominformationdata)):
                #print("\033[0m[\033[32m+\033[0m]总房间数量:\033[31m%d\033[0m间 剩余空房间数量:\033[31m%d\033[0m间 已入住女性人数:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetTotalNumberOfRooms(roominformationdata), GetEmptyRoom(roominformationdata), GetRoomNumber_Woman(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
            else:
                numberofnoncomplianthouses += 1
        print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #模式三（已入住人员必须有女性）
    #根据列表小区筛选
    elif(sys.argv[1] == "-aw"):
        for i in cellname:
            cellpath = GetMultiPageCellScreening(city, i)
            print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (i, len(cellpath)))
            numberofnoncomplianthouses = 0
            for i in cellpath:
                roominpath = GetRoominPathProcessing(i)
                roominformationdata= GetRoomInformation(roominpath)
                if(RoomScreening_Woman(roominformationdata)):
                    #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                    print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
                else:
                    numberofnoncomplianthouses += 1
            print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #根据指定小区名筛选
    elif(sys.argv[1] == "-mw"):
        cellpath = GetMultiPageCellScreening(city, sys.argv[2])
        print("\033[0m[\033[36m%s\033[0m]共有:\033[31m%d\033[0m间" % (sys.argv[2], len(cellpath)))
        numberofnoncomplianthouses = 0
        for i in cellpath:
            roominpath = GetRoominPathProcessing(i)
            roominformationdata= GetRoomInformation(roominpath)
            if(RoomScreening_Woman(roominformationdata)):
                #print("\033[0m[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata), ",".join(GetJobInformation(roominformationdata)), roominpath))
                print("[\033[32m+\033[0m]剩余空房间数量:\033[31m%d\033[0m间 房间号:[\033[35m%s\033[0m] 入住时间:[\033[33m%s\033[0m] 职业:[\033[32m%s\033[0m] 房屋链接:\033[36m%s\033[0m" % (GetEmptyRoom(roominformationdata),",".join(GetRoomNumberInformation(roominformationdata)) , ",".join(GetElapsedTimeInformation(roominformationdata)), ",".join(GetJobInformation(roominformationdata)), roominpath))
            else:
                numberofnoncomplianthouses += 1
        print("\033[0m[\033[32m+\033[0m]已过滤:\033[31m%d\033[0m间\n" % numberofnoncomplianthouses)
    #功能提示
    elif(sys.argv[1] == "-?"):
        print("模式一:已入住人员必须全部是女性或空房间")
        print("[-a] 使用内置小区名")
        print("[-as] 使用内置小区名和内置职业")
        print("[-ao xxx] 使用内置小区名和自定义职业")
        print("[-m xxx] 使用自定义小区名")
        print("[-ms xxx] 使用自定义小区名和内置职业")
        print("[-mo xxx xxx] 使用自定义小区名和自定义职业")
        print("模式二:已入住人员女性比例要大于或等于男性")
        print("[-ae] 使用内置小区名")
        print("[-me] 使用自定义内置小区名")
        print("模式三:已入住人员必须有女性")
        print("[-aw] 使用内置小区名")
        print("[-mw] 使用自定义内置小区名")

#测试函数
def TestFun(): 
    return
    
#脚本起始处
if __name__ == '__main__':
    #TestFun()
    Main()
