import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib import parse
import matplotlib.pyplot as plt # plt 用于显示图片
import matplotlib.image as mpimg # mpimg 用于读取图片
import numpy as np
import datetime as dt
import cv2


def QR_code():
    finduuid = re.compile(r'<input type = "hidden" value="(.*?)" id = "uuid"/>')
    findenc = re.compile(r'<input type = "hidden" value="(.*?)" id = "enc"/>')
    url = "https://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Ffxlogin.chaoxing.com%2Ffindlogin.jsp%3Fbackurl%3Dhttp%253A%252F%252Fwww.chaoxing.com%252Fchannelcookie%253Ftime%253D1593526769297"
    str = requests.get(url= url)
    text = str.text
    uuid = re.findall(finduuid,text)
    enc = re.findall(findenc,text)
    url = "https://passport2.chaoxing.com/createqr?uuid="+ uuid[0]+"&fid=-1"
    str = requests.get(url=url)

    cookies = requests.utils.dict_from_cookiejar(str.cookies)

    img = cv2.imdecode(np.array(bytearray(str.content), dtype='uint8'), cv2.IMREAD_UNCHANGED)
    cv2.imshow("test", img)
    cv2.waitKey(0)
    cv2.destroyWindow("test")

    url = "https://passport2.chaoxing.com/getauthstatus"
    data = {'enc': enc[0], "uuid": uuid[0]}
    cookies = "JSESSIONID:" + cookies["JSESSIONID"] + ";route:" + cookies["route"]
    headers = {"cookies": cookies}
    is_over = "no"
    while is_over =='no':
        str = requests.post(url=url, data=data, headers=headers)
        result_login = str.text
        findmes = re.compile(r'"mes":"(.*?)"')
        mes = re.findall(findmes,result_login)
        if mes[0] != "未登录":
            is_over == 'yes'
            break
        time.sleep(1)
        print(result_login)

    print("请等待两秒后再点击确认登录")
    time.sleep(0.5)
    is_ok="no"
    while is_ok == 'no':
        str = requests.post(url=url, data=data, headers=headers)
        result = str.text
        findmes = re.compile(r'"mes":"(.*?)"')
        cookies = requests.utils.dict_from_cookiejar(str.cookies)
        mes = re.findall(findmes, result)
        if mes[0] == "验证通过":
            is_ok == 'yes'
            break
        time.sleep(1)
        print(result)
    cook = ""
    for key in cookies:
        cook = cook + key+"="+cookies[key]+";"
    result_login = json.loads(result_login)
    result_login["cookies"] = cook
    print(result_login)
    return result_login

def getCourseList(cookies):
    url = "http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&mcode="
    user_agent_list ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
    headers = {
        "cookie": cookies,
        "User-Agent": user_agent_list
    }
    str = requests.get(url= url,headers = headers)
    text = str.text
    data_json = json.loads(text)
    print("CourseName     ", "CourseID     ", "ClassID     ")
    for i in range(len(data_json["channelList"])):
        courseName = data_json['channelList'][i]['content']["course"]["data"][0]["name"]
        id = data_json['channelList'][i]['content']["course"]["data"][0]["id"]
        classid = data_json['channelList'][i]['content']["id"]
        print(courseName,"","","",id,"","","",classid)
    return headers

def getactiveId(headers,CourseId,ClassID):
    url = "https://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId="+CourseId+"&jclassId="+ClassID
    str = requests.get(url= url,headers = headers)
    text = str.text
    a = re.compile(r"activeDetail\((.*?),")
    ActiveId_list = re.findall(a,text)
    new_activeId = ActiveId_list[0]
    return new_activeId
    #print(ActiveId_list,new_activeId)

def finishActive(activeId,headers,uid,nickname):
    url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId="+ activeId+\
          "&uid=" + uid + "&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid=0&name="+ parse.quote(nickname)
    str = requests.get(url=url, headers=headers)
    now_time = dt.datetime.now().strftime('%F %T')
    resule_txt = str.text
    if resule_txt == "success":
        resule_txt = "签到成功"
    print(resule_txt + "  检测时间：" +now_time)



if __name__ == "__main__":
    print("***************************************")
    print("*          欢迎使用学习通签到助手         *")
    print("*  Version:V1.0.0   Author:xiaopang   *")
    print("*           Data:2020-07-08           *")
    print("*      仅供学习测试，所有责任无作者无关     *")
    print("***************************************")
    result = QR_code()
    uid = result["uid"]
    nickname = result["nickname"]
    cookies = result["cookies"]
    headers = getCourseList(cookies)
    CourseId = input("Please input CourseId：")
    ClassID = input("Please input ClassID：")
    x = input("几分钟检测一次(请输入整数)：")
    is_over = 1
    while is_over == 1:
        activeId = getactiveId(headers, CourseId, ClassID)
        finishActive(activeId, headers, uid, nickname)
        time.sleep(60 * int(x)) #60秒 10 分钟
