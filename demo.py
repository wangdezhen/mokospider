# -*- coding: UTF-8 -*-
import requests
import random
import re
import time
import threading
import pymongo as pm

 # 获取连接
client = pm.MongoClient('localhost', 21111)  # 端口号是数值型

# 连接目标数据库
db = client.moko

# 数据库用户验证
db.authenticate("moko", "moko")

urls = ["http://www.moko.cc/subscribe/chenhaoalex/1.html"]
index = 0
get_index = 0
g_lock = threading.Lock()  #初始化一个锁  

class Config():
    def getHeaders(self):
        user_agent_list = [ \
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1" \
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11", \
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6", \
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6", \
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1", \
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5", \
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5", \
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3", \
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24", \
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]
        UserAgent=random.choice(user_agent_list)
        headers = {'User-Agent': UserAgent}
        return headers



#生产者
class Producer(threading.Thread):
    
    def run(self):
        print("线程启动...")
        headers = Config().getHeaders()
        print(headers)
        global urls
        global index 
        while True:
            g_lock.acquire() 
            if len(urls)==0:
                g_lock.release() 
                continue
            page_url = urls.pop()
            g_lock.release() #使用完成之后及时把锁给释放，方便其他线程使用
            response = ""
            try:
                response = requests.get(page_url,headers=headers,timeout=5)
                
            except Exception as http:
                print("生产者异常")
                print(http)
                continue       
            content = response.text 
            #如果是第一页，那么需要判断一下
            #print(page_url)
            is_home =re.search(r'(\d*?)\.html',page_url).group(1)
            if is_home == str(1):
                pages = re.findall(r'onfocus=\"this\.blur\(\)\">(\d*?)<',content,re.S)   #获取总页数
                #xunhuan tianjia  jinru 
                page_size = 1
                if pages:
                    page_size = int(max(pages))   #获取最大页数
                    if page_size > 1:
                        url_arr = []
                        threading_links_1 = []
                        for page in range(2,page_size+1):
                            url =  re.sub(r'(\d*?)\.html',str(page)+".html",page_url)  
                            threading_links_1.append(url)
                            g_lock.acquire()
                            index += 1 
                            g_lock.release()
                            url_arr.append({ "index":index, "link": url})

                        g_lock.acquire()
                        urls += threading_links_1  #  URL数据添加
                        g_lock.release()
                        try:
                            db.text.insert_many(url_arr,ordered=False )
                        except Exception as e:
                            print("数据库输入异常")
                            print (e)
                            continue
                        
                    else:
                        pass
                else:
                    pass
            rc = re.compile(r'<a class=\"imgBorder\" href=\"\/(.*?)\" hidefocus=\"true\">')
            follows = rc.findall(content)
            print(follows)
            fo_url = []
            threading_links_2 = []
            for u in follows:   
                this_url = "http://www.moko.cc/subscribe/%s/1.html" % u 
                g_lock.acquire()
                index += 1 
                g_lock.release()
                fo_url.append({"index":index,"link":this_url})
                threading_links_2.append(this_url)
           
            g_lock.acquire()
            urls += threading_links_2
            g_lock.release()
            print(fo_url)
            
            try:
                db.text.insert_many(fo_url,ordered=False )
            except:
                continue
#xiaofei zhe
class Consumer(threading.Thread):
    
    def run(self):
        headers = Config().getHeaders()

        global get_index 
        while True:
            
            g_lock.acquire() 
            get_index += 1
            g_lock.release()

            link = db.links.find_one_and_delete({"index":get_index})
            page_url = ""
            if link:
                page_url = link["link"]
                print(page_url+">>>网页分析中...")
            else:
                continue

            response = ""
            try:
                response = requests.get(page_url,headers=headers,timeout=5)
                
            except Exception as http:
                print("消费者有异常")
                print(http)
                continue
            
            content = response.text 
            rc = re.compile(r'divEditOperate_(?P<ID>\d*)[\"] .*>[\s\S]*?<p class=\"state\">.*?(?P<级别>\w*P).*</span></span>(?P<是否认证><br/>)?.*?</p>[\s\S]*?<div class=\"info clearfix\">[\s\S]*?<a class=\"imgBorder\" href=\"\/(?P<主页>.*?)\" hidefocus=\"true\">[\s\S]*?<img .*?src=\"(?P<头像>.*?)\".*?alt=\".*?\" title=\"(?P<昵称>.*?)\" />[\s\S]*?<p class=\"font12 lesserColor\">(?P<地点>.*?)&nbsp.*?<span class=\"font12 mainColor\">(?P<粉丝数目>\d*?)</span>')
            user_info = rc.findall(content)
            print(">>>>>>>>>>>>>>>>>>>>")
            users = []
            for user in user_info:
                post = {
                    "id": user[0],
                    "level": user[1],
                    "real":user[2],
                    "profile": user[3],
                    'thumb':user[4],
                    'nikename':user[5],
                    'address':user[6],
                    'follows':user[7]
                }

                users.append(post)
            print(users)
           
            try:
                db.mkusers.insert_many(users,ordered=False )
            except Exception as e:
                print("数据库输入异常")
                print (e)
                continue

            time.sleep(1)

            print("<<<<<<<<<<<<<<<<<<<<")
if __name__ == "__main__":
    for i in range(5):
        p = Producer()
        p.start()

    for i in range(7):
        c = Consumer()
        c.start()


