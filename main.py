import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import bs4
from bs4 import BeautifulSoup

from variable import *
from counter import Counter
from errorhandle import *
from fileholding import FileHolding

import json
import re
import os
from threading import Thread
import time



class DcardSpider:

    def __init__(self,scrollstep,drivepath=r"C:\Users\user\OneDrive\桌面\Forever\python\chromedriver.exe",url=r"https://www.dcard.tw/f"):

        self.driver = None
        self.drivepath=drivepath

        self.urlbase = r"https://www.dcard.tw"

        self.scroll_counter=Counter(start=0,step=scrollstep)
        self.scroll_counter_iter=iter(self.scroll_counter)

        self.lasturl=None






    def __show_information(gender, identify,category, article_title, outline, number_of_comments,link,post_time,setted_to_top):
        if setted_to_top!=None:
           print(f"<<{setted_to_top}>>時間 :{post_time}  卡稱學校 :{identify}  分類 :{category}   ({gender.text if gender is not None else '##'})")
        else:
           print(f"時間 :{post_time}  卡稱學校 :{identify}  分類 :{category}   ({gender.text if gender is not None else '##'})")
        print(f"title :{article_title}")
        print(f"      {outline}")
        print(f"留言數: {number_of_comments} --{link}")
        print("\n\n")

    def __gathering_information(self,souptagobject):

        if souptagobject==None:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')
        if type(souptagobject)!=bs4.element.Tag:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')


        # link
        link = "".join([self.urlbase, souptagobject.a["href"]])
        post = requests.get(link)
        soup_for_post = BeautifulSoup(post.text, "lxml")

        # ..getting from post webpage..  time,category,exist_status                -Checking the post exists now
        if len(soup_for_post.find_all(class_=class_time_and_classification_in_postpage))==0:
            time_post=None
            category=None
            exist_status=False
        else:
            category, time_post = soup_for_post.find_all(class_=class_time_and_classification_in_postpage)
            time_post = time_post.text
            category = category.a.text
            exist_status=True

       # gender,identify,category,settotop
        if souptagobject.title!=None:
           gender=souptagobject.title.text
        else:
           gender=None


        identify_catogery=souptagobject.find(class_=class_identify_and_category_in_mainpage)
        if len(identify_catogery.contents)==2:             #The situation happen when scraping in all-webpage
            identify=identify_catogery.contents[1].text
        elif len(identify_catogery.contents)==1:           #The situation happen when scraping in specific-category-page
            identify=identify_catogery.contents[0].text
        else:                                              #The situation that the developer of dcard scraper have never expected
            raise Exception("Some situations that the developer of dcard scraper have never expected happened ")

        if not souptagobject.find(class_=class_setted_to_top) is None:
           setted_to_top=True
        else :
           setted_to_top=False

        # article title,outline
        article_title = souptagobject.find(class_=class_article_title).text
        outline = souptagobject.find(class_=class_outline)
        if outline is not None:
           outline = outline.text

        # number of comments,link
        if  souptagobject.find(class_=class_number_of_comments)!=None:
            number_of_comments=souptagobject.find(class_=class_number_of_comments).span.text

        elif len(souptagobject.find_all(class_=class_number_of_comments_when_on_one_comments))>0:
            number_of_comments=souptagobject.find_all(class_=class_number_of_comments_when_on_one_comments)[1].span.text
        else:
            raise UnExceptedError(f"comment not found in post :{article_title}")


        return {"gender":gender,"identify":identify,"category":category,"article title":article_title,"outline":outline,"link":link,"post time":time_post,"number of comments":number_of_comments,"setted to top":setted_to_top,"exist status":exist_status}


    def __log_information(data_exist, data_not_exist,dbpath_ex,dbpath_nex):
        if dbpath_ex == dbpath_nex:
            raise ValueError("dbpath_ex should not equal to dbpath_nex")

       #create files for database if files for database dosen't exist
        FileHolding.having_file_exist(dbpath_ex,dbpath_nex)


        with open(dbpath_ex,"r",encoding="utf-8") as jsonexistdatafile_r:
            alreadycontent = jsonexistdatafile_r.read()
            with open(dbpath_ex,"w",encoding="utf-8") as jsonexistdatafile_w:
             if alreadycontent!="":
                 data_exist.update(json.loads(alreadycontent))
                 jsonexistdatafile_w.write(json.dumps(data_exist,ensure_ascii=False))
             else:
                 jsonexistdatafile_w.write(json.dumps(data_exist,ensure_ascii=False))


        with open(dbpath_nex,"r",encoding="utf-8") as json_not_exist_datafile_r:
            alreadycontent = json_not_exist_datafile_r.read()
            with open(dbpath_nex,"w",encoding="utf-8") as json_not_exist_datafile_w:
             if alreadycontent!="":
                 data_not_exist.update(json.loads(alreadycontent))
                 json_not_exist_datafile_w.write(json.dumps(data_not_exist,ensure_ascii=False))
             else:
                 json_not_exist_datafile_w.write(json.dumps(data_not_exist,ensure_ascii=False))


    def scraping(self,url,dbpath_ex,dbpath_nex,scrollingtime=100):
        if url==None:
            raise ValueError('Arguments "url" must be string-like object')
        if self.driver ==None:
            raise Exception("The driver need to be inited before scraping.To init driver, call the method 'scraping'")
        if scrollingtime!="infinite" and type(scrollingtime) != int:
            raise TypeError('Arguments "scrollingtime"  only accept int object or string"infinite" passed"')

        #set up
        if url==self.lasturl:
            pass
        elif url!=self.lasturl:
            self.driver.get(url)
            self.lasturl=url

        dbpath_ex=dbpath_ex
        dbpath_nex=dbpath_nex
        scrolltime_counter=Counter(start=0,end=scrollingtime,step=1)
        data_exist_store = {}
        data_not_exist_store={}
        article_record = {"now": [], "previous": []}

        for i in (scrolltime_counter):
            # scrolling the webpage
            self.driver.execute_script(f"window.scrollTo(0,{next(self.scroll_counter_iter)})")

            # waiting for  new articles
            time.sleep(0.5)
            soup = bs4.BeautifulSoup(self.driver.page_source, "lxml")

            # get all article for this scroll
            articles = soup.find_all(class_=class_article)
            for i in range(len(articles)):
                article = articles[i]

                # #gathering information
                information = self.__gathering_information(souptagobject=article)

                #make sure if the article have been scraped
                post_id=(re.findall("\d+",article.parent["data-key"])[0])
                if post_id in article_record["previous"]:
                    continue

                gender=information.get(key_gender)
                identify=information.get(key_idenfity)
                category=information.get(key_category)
                article_title = information.get(key_articletitle)
                outline = information.get(key_outline)
                post_time=information.get(key_posttime)
                link=information.get(key_link)
                number_of_comments=information.get(key_numberofcomments)
                setted_to_top=information.get(key_settedtotop)
                exist_status=information.get(key_existstatus)

                # recording article
                article_record["now"].append(post_id)


                #storing data

                data = {"post info":{"post id": post_id, "post time": post_time, "category": category,"setted to top": setted_to_top, "number of comments": number_of_comments,"link": link},
                        "article info": {"article_title": article_title, "outline": outline},
                         "user info": {"identify": identify, "gender": gender}}
                if exist_status==True:
                   data_exist_store[article_title]=data
                elif exist_status==False:
                   data_not_exist_store[article_title]=data


            # update record
            article_record["previous"]=article_record["previous"]+article_record["now"]
            article_record["now"].clear()


        #log the result
        DcardSpider.__log_information(data_exist=data_exist_store,data_not_exist=data_not_exist_store,dbpath_ex=dbpath_ex,dbpath_nex=dbpath_nex)



    def init_driver(self,hidediver=False):
        if self.driver!=None:
           raise Exception("The driver is expected to be closed before initialized again ")
        if not  hidediver in [True,False]:
            raise TypeError('Argument "hidedriver" except boolean-like object')

        opt=ChromeOptions()
        if hidediver == True:
           opt.add_argument("--headless")

        self.driver=webdriver.Chrome(self.drivepath,options=opt)


    def close_driver(self):
        self.driver.close()
        self.driver=None




