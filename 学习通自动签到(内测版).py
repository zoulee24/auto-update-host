from datetime import datetime
import cv2 as cv
import requests as rq
import re, ctypes, inspect, threading, json, time
import numpy as np
import datetime as dt
from urllib import parse
import tkinter as tk
import os.path
import time


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def first_login():
    finduuid = re.compile(r'<input type = "hidden" value="(.*?)" id = "uuid"/>')
    findenc = re.compile(r'<input type = "hidden" value="(.*?)" id = "enc"/>')
    url = "https://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Ffxlogin.chaoxing.com%2Ffindlogin.jsp%3Fbackurl%3Dhttp%253A%252F%252Fwww.chaoxing.com%252Fchannelcookie%253Ftime%253D1593526769297"
    html = rq.get(url=url).text
    uuid = re.findall(finduuid, html)
    enc = re.findall(findenc, html)
    url = "https://passport2.chaoxing.com/createqr?uuid=" + uuid[0] + "&fid=-1"
    html = rq.get(url=url)

    cookies = rq.utils.dict_from_cookiejar(html.cookies)

    img = cv.imdecode(np.array(bytearray(html.content), dtype='uint8'), cv.IMREAD_UNCHANGED)
    cv.namedWindow('sign-in-windows')

    url = "https://passport2.chaoxing.com/getauthstatus"
    data = {'enc': enc[0], "uuid": uuid[0]}
    cookies = "JSESSIONID:" + cookies["JSESSIONID"] + ";route:" + cookies["route"]
    headers = {"cookies": cookies}
    while True:
        cv.imshow("sign-in-windows", img)
        cv.waitKey(1)
        str = rq.post(url=url, data=data, headers=headers)
        result_login = str.text
        findmes = re.compile(r'"mes":"(.*?)"')
        mes = re.findall(findmes, result_login)
        if mes[0] != "未登录":
            print("mes[0] = {}".format(mes[0]))
            cv.destroyWindow("test")
            break
        time.sleep(0.78)
    time.sleep(0.512)
    while True:
        html = rq.post(url=url, data=data, headers=headers)
        result = html.text
        findmes = re.compile(r'"mes":"(.*?)"')
        cookies = rq.utils.dict_from_cookiejar(html.cookies)
        mes = re.findall(findmes, result)
        if mes[0] == "验证通过":
            print("mes[0] = {}".format(mes[0]))
            break
        time.sleep(0.5)
    cook = ""
    for key in cookies:
        cook = cook + key+"="+cookies[key]+";"
    result_login = json.loads(result_login)
    result_login["cookies"] = cook
    return result_login


def get_courselist(cookies):
    url = "http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&mcode="
    user_agent_list ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38"
    headers = {
        "cookie": cookies,
        "User-Agent": user_agent_list
    }
    html = rq.get(url=url, headers=headers).text
    data_json = json.loads(html)
    print("CourseName     ", "CourseID     ", "ClassID     ")
    datas = [[], [], []]
    for i in range(len(data_json["channelList"])):
        classid = data_json['channelList'][i]['content']["id"]
        if classid < 40000000:
            continue
        courseName = data_json['channelList'][i]['content']["course"]["data"][0]["name"]
        id = data_json['channelList'][i]['content']["course"]["data"][0]["id"]
        print(courseName, "\t", id, "\t", classid)
        datas[0].append(courseName)
        datas[1].append(str(id))
        datas[2].append(str(classid))
        time.sleep(0.1)

    index = len(datas[0])
    course_name = ""
    global qd_count, check_count
    for i in range(index):
        qd_count.append(0)
        check_count.append(0)
    for i in range(index - 1):
        course_name += datas[0][i] + "\n"
    course_name += datas[0][index - 1]
    course0.configure(text=course_name, height=1*index, width=60)
    course0.pack()
    return headers, datas


def get_activeId(headers, datas, index):
    url = "https://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId="\
          + datas[1][index] + "&jclassId=" + datas[2][index]
    str = rq.get(url=url, headers=headers)
    text = str.text
    a = re.compile(r"activeDetail\((.*?),")
    ActiveId_list = re.findall(a, text)
    if len(ActiveId_list) > 0:
        return ActiveId_list
    return []


def finishActive(activeIds, headers, uid, nickname, index):
    for activeId in activeIds:
        url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId=" + activeId + \
              "&uid=" + uid + "&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid=0&name=" + parse.quote(nickname)
        html = rq.get(url=url, headers=headers).text
        now_time = dt.datetime.now().strftime('%F %T')
        global check_count, qd_count
        check_count[index] += 1
        if html == "success":
            qd_count[index] += 1
            print("签到成功" + "\t检测时间：" + now_time)


def check_loop(headers, datas):
    end = time.time()
    start = end - 120
    uid = result["uid"]
    nickname = result["nickname"]
    lens = len(datas[0])

    while True:
        hours = int(datetime.now().strftime("%H"))
        if hours < 7 or hours >= 21:
            time.sleep(600)
            continue
        elif hours == 7:
            time.sleep(50)
            continue
        while qd_stuats == "开始自动签到" and end - start > 120:
            ck_str = "检测次数= "
            qd_str = "签到次数= "
            start = time.time()
            for i in range(lens):
                activeId = get_activeId(headers, datas, i)
                finishActive(activeId, headers, uid, nickname, i)
                ck_str += str(check_count[i]) + "\t"
                qd_str += str(qd_count[i]) + "\t"
            course0_dt.configure(text=ck_str+"\n"+qd_str, height=4, width=10*lens)
            course0_dt.pack()
        time.sleep(0.5)
        end = time.time()


def main_loop():
    cookies = result["cookies"]
    headers, data = get_courselist(cookies)
    check_loop(headers, data)


def wt_cookia(nok):
    global result
    if os.path.isfile("user_cookies.txt") and nok:
        with open("user_cookies.txt", "r") as f:
            result["uid"] = f.readline()
            if int(result['uid']) > 10:
                result["mes"] = f.readline()
                result["type"] = f.readline()
                res = f.readline()
                if res == "False":
                    result["status"] = False
                else:
                    result["status"] = True
                result["cookies"] = f.readline()
                nok = False
    else:
        with open("user_cookies.txt", "w") as f:
                f.write(result["uid"])
                f.write("\n")
                if int(result['uid']) > 10:
                    f.write(result["mes"])
                    f.write("\n")
                    f.write(result["type"])
                    f.write("\n")
                    f.write(str(result["status"]))
                    f.write("\n")
                    f.write(result["cookies"])
    f.close()
    return nok


def gui_callback():
    global qd_stuats
    if qd_stuats == "停止自动签到":
        qd_stuats = "开始自动签到"
    else:
        qd_stuats = "停止自动签到"
    print("状态：{}".format(qd_stuats))
    bt_label.configure(text=qd_stuats)
    bt_label.pack()


def gui_cfg():
    bt_label.configure(text=qd_stuats, height=2, width=30)
    bt.configure(text="切换自动签到状态", height=2, width=30, command=gui_callback)
    bt_label.pack()
    bt.pack()
    gui.mainloop()


qd_stuats = "停止自动签到"
gui = tk.Tk()
qd_count = []
check_count = []
course0 = tk.Label(gui)
course0_dt = tk.Label(gui)
bt_label = tk.Label(gui)
bt = tk.Button(gui)
result = {'uid': "0",
          'nickname': '邹冠宇',
          'mes': '已扫描',
          'type': '4',
          'status': False,
          'cookies': 'DSSTASH_LOG=C_38-UN_146-US_126825712-T_1633340991302;UID=126825712;_d=1633340991300;_uid=126825712;fid=1864;lv=2;uf=b2d2c93beefa90dcecf45c61ec982f6b631189dd5a2868adedda4593e746ece4fb486a60705ad240e41e73c284109c7b913b662843f1f4ad6d92e371d7fdf644d19cfe10affb40b7fd68be96b6183b1a06f6a395fbf381201b5681d818e1b6eef3cda998cbe68d2c;vc=AB4D91C2B91A29F04B6A25770326E998;vc2=340B65E6DE91075FDE38E14A0F240243;vc3=MkQFth9v2%2BPxDl6AFc3xwObM%2FDN8eob500DbFyVKSaOiNkQsvXM6iIBQ0aloMTt0fpO7EMUujdcgvrc2MgvT6pocEyUeA1Cu7%2FyiuBKPKKtLz8YlUplQq7YC2EofeUmxeTTFbAz54TWMwHkg1Htz3sV1O94wGk3sm953YD8p4NM%3Da8816d0852abe3c9f5f1a5654a347bca;xxtenc=630b20ebf10ceb0e63378a1e408dfac9;JSESSIONID=98502B715AF71C8980DF2E43FCBDBC16;route=fb0878d2b253f576b9614a77ccc901db;'
          }


if __name__ == '__main__':
    try:
        nok = wt_cookia(True)
        if nok:
            result = first_login()
            wt_cookia(False)
    except Exception as e:
        print("Error : {}".format(e))
    if int(result['uid']) > 10:
        main = threading.Thread(target=main_loop)
        main.start()
        gui_cfg()
        stop_thread(main)
        print("程序结束")
