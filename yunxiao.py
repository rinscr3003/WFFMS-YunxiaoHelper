import time
import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests.cookies import RequestsCookieJar as CJar
import json as J
import sys

class YunXiaoHelper(object):
    session=requests.session()
    username = ""
    password = ""
    cookieJar = CJar()
    headers={
        "Host":"account.wffms.com",
        "Origin":"http://account.wffms.com",
        "Referer":"http://account.wffms.com/partner?service=http://yunxiao.wffms.com/Portal/LayoutD/Login.aspx",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
    }
    headers2={
        "Host":"yunxiao.wffms.com",
        "Origin":"http://yunxiao.wffms.com",
        "Referer":"http://yunxiao.wffms.com/Portal/LayoutD/Login.aspx",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
    }
    # this url is for WFFMS in default
    loginUrl="http://account.wffms.com/"
    indexUrl="http://yunxiao.wffms.com/Portal/LayoutD/Default.aspx"
    def __init__(self, username, password):
        self.username = username
        self.password = password
        postdata = {
            'loginName': self.username,
            'password': self.password,
            'domain': 'yunxiao',
            'captchaCode': '',
            'rememberMe': 'false',
            'service':'http://yunxiao.wffms.com/Portal/LayoutD/Login.aspx',
        }
        r = self.session.post(self.loginUrl, data=postdata,allow_redirects=False,headers=self.headers)
        #print(r.text)
        if "service" in r.text:
            # success
            jo=J.loads(r.text)
            cookurl=jo['service'].replace("http://www.yunxiao.com?","http://yunxiao.wffms.com/Portal/LayoutD/Login.aspx?")
            # 我也不知道为什么要替换但是服务器就是很见鬼的返回主服务器要换地址才能抢到cookie
            # QwQ
            print(cookurl)
            cook=self.session.get(cookurl,allow_redirects=False)
            #print(cook.status_code)
            r=self.session.get(self.indexUrl,allow_redirects=False)
            #print(r.text)
        else:
            raise Exception(r.text)

    def GetCourse(self):
        funcUrl="http://yunxiao.wffms.com/BaseInfos/MyActivity"
        xPath="//*[@id=\"metroaqui\"]/div"
        res=self.session.get(funcUrl,headers=self.headers2)
        #print(res.text)
        html = etree.HTML(res.text)
        cours=html.xpath(xPath)
        courses_list=[]
        for i in cours:
            #print(i.text)
            items=i.xpath("div")[0].items()
            course_name="[N/A]"
            course_time=-1
            course_isstart=False
            course_outdate=False
            course_acid="[N/A]"
            for j in items:
                if j[0]=="actname":
                    course_name=j[1]
                if j[0]=="actid":
                    course_acid=j[1]
                if j[0]=="timetoend":
                    if float(j[1])<0:
                        course_outdate=True
                if j[0]=="timetostart":
                    if float(j[1])<0:
                        course_isstart=True
                    course_time=int(float(j[1]))+int(time.time())
                    if course_time<0:
                        course_time=0
            #print("获取到 活动名="+course_name+", 活动ID="+course_acid+", 开始TS="+str(course_time)+".")
            courses_list.append((course_name,course_acid,course_time,course_isstart,course_outdate))
        #print(courses_list)
        return courses_list

    def GetCourseItems(self,csi):
        funcUrl="http://yunxiao.wffms.com/BaseInfos/WishPeriodCourse/Optional?ax=1&ActId="+csi
        xPath="body/div[1]/table[2]/tr/td/div[not(contains(@class,'metro-wished'))]"
        res=self.session.get(funcUrl,headers=self.headers2)
#        print(res.text)
        html = etree.HTML(res.text)
        cours=html.xpath(xPath)
        cit_list=[]
        for i in cours:
            cit_name="[N/A]"
            cit_info="[N/A]"
            cit_crid="[N/A]"
            for j in i.items():
                if j[0]=="groupid":
                    cit_crid=j[1]
            cit_name=i.xpath("table/tr/td[@class='content']")[0].text
            cit_info=i.xpath("table/tr/td[@class='title']")[0].text
            cit_list.append((cit_name,cit_info,cit_crid))
        #print(cit_list)
        return cit_list

    def WishCourse(self,acid,crid):
        funcUrl="http://yunxiao.wffms.com/BaseInfos/WishPeriodCourse/WishGroup"
        postdata = {
            'Id': crid,
            'ActId': acid,
            'ax': 1,
        }
        wishheaders={
            "Host": "yunxiao.wffms.com",
            "Origin": "http://yunxiao.wffms.com",
            "Referer": "http://yunxiao.wffms.com/BaseInfos/WishPeriodCourse/Optional?ax=1&ActId="+acid,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74",
            "X-Requested-With": "XMLHttpRequest",
        }
        r = self.session.post(funcUrl, data=postdata,allow_redirects=False,headers=wishheaders)
        #print(r.text)
        if "Result" in r.text:
            jo=J.loads(r.text)
            restext=[
                "成功。",
                "您已经选过该课程！",
                "选课失败，超过人数上限！",
                "该科目下只能同时选择指定门数课程，如需重选，请先退选已选课程！",
                "本课程上课时间与已选课程上课时间冲突！",
                "您已经选择过该课程下的教学班级！",
                "超过该课程每天最多允许选择的节数！",
                "该课程只能选择连堂课！",
                "总课时数超出了系统设置上限，无法继续选择，请退选其它课程后再试！"
            ]
            if jo["Result"]==-1:
                return None,"系统故障，操作失败。"
            else:
                return jo,restext[jo["Result"]]
        else:
            return None,"联网过程出错。"

if __name__=="__main__":
    print("STEP1:正在登录……")
    yx=YunXiaoHelper(sys.argv[1],sys.argv[2])
    cs=[]
    csflag=True
    while csflag:
        time.sleep(0.2)
        print("STEP2:正在获取活动列表……\n若获取失败超过5秒，请停止运行再重新运行。")
        cs=yx.GetCourse()
        if cs==[]:
            print("获取活动列表失败，正在重新获取。")
        else:
            csflag=False
    csiflag=True
    sel=-1
    while csiflag:
        for i in range(len(cs)):
            csi=cs[i]
            print("="*24+"活动%02d"%(i)+"="*24)
            print(" "*4+"活动名：  "+csi[0])
            print(" "*4+"活动ID：  "+csi[1])
            print(" "*4+"开始时间："+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(csi[2])))
            print(" "*4+"已开始：  "+str(csi[3]))
            print(" "*4+"已结束：  "+str(csi[4]))
            print()
        print()
        sel=int(input("请选择活动编号：").strip())
        if sel in range(len(cs)) and cs[sel][4]==False:
            csiflag=False
        else:
            print("输入有误或活动已结束，请重新选择。")
    citflag=True
    citems=[]
    citCount=10
    while citflag:
        if citCount<=0:
            print("获取课程列表失败超过10次，正在返回活动列表...")
            csiflag=True
            sel=-1
            while csiflag:
                for i in range(len(cs)):
                    csi=cs[i]
                    print("="*24+"活动%02d"%(i)+"="*24)
                    print(" "*4+"活动名：  "+csi[0])
                    print(" "*4+"活动ID：  "+csi[1])
                    print(" "*4+"开始时间："+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(csi[2])))
                    print(" "*4+"已开始：  "+str(csi[3]))
                    print(" "*4+"已结束：  "+str(csi[4]))
                    print()
                print()
                sel=int(input("请选择活动编号：").strip())
                if sel in range(len(cs)) and cs[sel][4]==False:
                    csiflag=False
                else:
                    print("输入有误或活动已结束，请重新选择。")
            citflag=True
            citems=[]
            citCount=10
            continue
        print("STEP3:正在获取课程列表……")
        citems=yx.GetCourseItems(cs[sel][1])
        if citems==[]:
            print("获取课程列表失败，正在重新获取。")
            citCount-=1
        else:
            citflag=False
    citsflag=True
    sel2=-1
    citems2=[]
    while citsflag:
        if citems2==[]:
            citems2=citems.copy()
        for i in range(len(citems2)):
            csi=citems2[i]
            print("="*24+"课程%02d"%(i)+"="*24)
            print(" "*4+"课程名：  "+csi[0])
            print(" "*4+"信息：    "+csi[1])
            print(" "*4+"课程ID：  "+csi[2])
            print()
        print()
        sel2str=(input("请选择课程编号，直接回车进入关键字搜索：").strip())
        if sel2str=="":
            citems2=[]
            keyword=input("请输入课程关键字：").strip()
            for i in citems:
                if keyword in i[0]:
                    citems2.append(i)
            continue
        else:
            sel2=int(sel2str)
        if sel2 in range(len(citems2)):
            citsflag=False
        else:
            print("输入有误，请重新选择。")
    jo=None
    resText=""
    wcflag=True
    wcCount=20
    while wcflag:
        if wcCount<=0:
            print("选课请求失败超过20次，正在返回课程列表...")
            citsflag=True
            sel2=-1
            citems2=[]
            while citsflag:
                if citems2==[]:
                    citems2=citems.copy()
                for i in range(len(citems2)):
                    csi=citems2[i]
                    print("="*24+"课程%02d"%(i)+"="*24)
                    print(" "*4+"课程名：  "+csi[0])
                    print(" "*4+"信息：    "+csi[1])
                    print(" "*4+"课程ID：  "+csi[2])
                    print()
                print()
                sel2str=(input("请选择课程编号，直接回车进入关键字搜索：").strip())
                if sel2str=="":
                    citems2=[]
                    keyword=input("请输入课程关键字：").strip()
                    for i in citems:
                        if keyword in i[0]:
                            citems2.append(i)
                    continue
                else:
                    sel2=int(sel2str)
                if sel2 in range(len(citems2)):
                    citsflag=False
                else:
                    print("输入有误，请重新选择。")
            jo=None
            resText=""
            wcflag=True
            wcCount=20
            continue
        try:
            time.sleep(0.2)
            print("STEP4:正在选课……若持续出现严重错误，请直接关闭窗口再重新运行。")
            jo,resText=yx.WishCourse(cs[sel][1],citems2[sel2][2])
            if jo==None:
                print("选课失败（"+resText+"），正在重新尝试。")
            elif jo["Result"]!=0:
                print("选课失败（"+resText+"），正在重新尝试。")
            else:
                wcflag=False
                print("选课成功！当前课程有"+str(jo["Results"][0]["CurrentWishedCount"])+"人，其中男生"+str(jo["Results"][0]["CurrentWishedBoyCount"])+"人，女生"+str(jo["Results"][0]["CurrentWishedGirlCount"])+"人。")
                print("附加消息："+str(jo["Results"][0]["Msg"]))
        except KeyboardInterrupt:
            wcflag=False
            print("选课失败（您已终止程序运行）。")
        except:
            print("选课失败（通信失败），正在重新尝试。")
