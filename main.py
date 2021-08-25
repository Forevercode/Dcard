import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import bs4
from bs4 import BeautifulSoup
from variable import *
from counter import Counter
from threading import Thread
import time
import copy


class DcardSpider:

    def __init__(self,drivepath=r"C:\Users\user\OneDrive\桌面\Forever\python\chromedriver.exe",url=r"https://www.dcard.tw/f"):

        self.drivepath=drivepath
        self.url=url
        self.driver=None

        if self.url==r"https://www.dcard.tw/f":
            self.urlbase=r"https://www.dcard.tw"

        self.scroll_counter=Counter(start=0,step=2000)
        self.scroll_counter_iter=iter(self.scroll_counter)



    def __show_information(gender, school,classification, article_title, outline, number_of_comments,link,time_post):
        print(f"時間 :{time_post}  卡稱學校 :{school}  分類 :{classification}   ({gender.text if gender is not None else '##'})")
        print(f"title :{article_title}")
        print(f"      {outline}")
        print(f"留言數: {number_of_comments} --{link}")
        print()

    def __gathering_information(self,souptagobject):

        if souptagobject==None:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')
        if type(souptagobject)!=bs4.element.Tag:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')

       # gender,school
        gender =souptagobject.find("title")
        school = souptagobject.find_all(class_=class_school_and_classification_in_mainpage)[1]
        school = school.text

       # article title
        article_title = souptagobject.find(class_=class_article_title).text

       # outline
        outline = souptagobject.find(class_=class_outline)
        if outline is not None:
           outline = outline.text

       # number of comments,link
        number_of_comments = souptagobject.find(class_=class_number_of_comments).span.text
        link = "".join([self.urlbase,souptagobject.a["href"]])

       # ..getting from post webpage..  time,classification
        post = requests.get(link)
        soup_for_post = BeautifulSoup(post.text, "lxml")

        classification,time_post = soup_for_post.find_all(class_=class_time_and_classification_in_postpage)
        time_post=time_post.text
        classification=classification.a.text

      # post id
        post_id = souptagobject.parent["data-key"]
        return {"gender":gender,"school":school,"classification":classification,"article title":article_title,"outline":outline,"link":link,"post id":post_id,"time post":time_post,"number of comments":number_of_comments}



    def init_driver(self,hidediver=False):
        if self.driver!=None:
           raise Exception("The driver is expected to be closed before initialized again ")

        if hidediver==True:
           opt=ChromeOptions()
           opt.add_argument("--headless")
           self.driver=webdriver.Chrome(self.drivepath,options=opt)

        elif hidediver==False:
           self.driver = webdriver.Chrome(self.drivepath)

        else:
            raise TypeError('Argument "hidedriver" except boolean object')

        self.driver.get(self.url)

    def close_driver(self):
        self.driver.close()
        self.driver=None

    def scraping(self,scrollingtime="infinite"):
        if self.driver ==None:
            raise Exception("The driver need to be inited before scraping.To init driver, call the method 'scraping'")
        if scrollingtime!="infinite" and type(scrollingtime) != int:
            raise TypeError('Arguments "scrollingtime"  only accept int object or string"infinite" passed"')

        #make the counter for scraping
        scrolltime_counter=Counter(start=0,end=scrollingtime,step=1)



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

                #gathering information
                information=self.__gathering_information(souptagobject=article)

                gender=information.get(genderkey)
                school=information.get(schoolkey)
                classification=information.get(classificationkey)

                article_title = information.get(articletitlekey)
                outline = information.get(outlinekey)

                time_post=information.get(timepostkey)
                post_id=information.get(postidkey)
                link=information.get(linkkey)

                number_of_comments=information.get(numberofcommentskey)


                # recording article
                article_record["now"].append(post_id)

                if post_id in article_record["previous"]:
                    continue
                DcardSpider.__show_information(gender=gender, school=school, classification=classification, article_title=article_title,
                                 outline=outline, number_of_comments=number_of_comments,link=link,time_post=time_post)

            # update record
            article_record["previous"]=article_record["previous"]+article_record["now"]
            article_record["now"].clear()

        #close driver
        self.driver.close()
        self.driver=None



if __name__=="__main__":

    dsp = DcardSpider()

    dsp.init_driver(hidediver=True)
    dsp.scraping(scrollingtime=4)
