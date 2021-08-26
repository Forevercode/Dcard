import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import bs4
from bs4 import BeautifulSoup
from variable import *
from counter import Counter
from errorhandle import *
import re
from threading import Thread
import time



class DcardSpider:

    def __init__(self,drivepath=r"C:\Users\user\OneDrive\桌面\Forever\python\chromedriver.exe",url=r"https://www.dcard.tw/f"):
        self.driver = None
        self.drivepath=drivepath

        self.url=url
        self.urlbase = r"https://www.dcard.tw"

        self.scroll_counter=Counter(start=0,step=2000)
        self.scroll_counter_iter=iter(self.scroll_counter)


    def __show_information(gender, identify,category, article_title, outline, number_of_comments,link,post_time,setted_to_top):
        information_of_remark=[setted_to_top]

        print(f"時間 :{post_time}  卡稱學校 :{identify}  分類 :{category}   ({gender.text if gender is not None else '##'})")
        print(f"title :{article_title}")
        print(f"      {outline}")
        print(f"留言數: {number_of_comments} --{link}")
        if not None in information_of_remark:
            remark=" ".join(information_of_remark)
            print(f"其它備注 :{remark}")
        print("\n\n")

    def __gathering_information(self,souptagobject):

        if souptagobject==None:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')
        if type(souptagobject)!=bs4.element.Tag:
            raise Exception('Arguments "souptagobject" expect a tag object in Beautifulsoup passed')

       # gender,identify,category,settotop
        gender =souptagobject.find("title")
        identify_catogery=souptagobject.find(class_=class_identify_and_category_in_mainpage)


        if len(identify_catogery.contents)==2:             #The situation happen when scraping in all-webpage
            identify=identify_catogery.contents[1].text
        elif len(identify_catogery.contents)==1:           #The situation happen when scraping in specific-category-page
            identify=identify_catogery.contents[0].text
        else:                                              #The situation that the developer of dcard scraper have never expected
            raise Exception("Some situations that the developer of dcard scraper have never expected happened ")



        if not souptagobject.find(class_=class_setted_to_top) is None:
           setted_to_top=souptagobject.find(class_=class_setted_to_top).text
        else :
           setted_to_top=None


       #link
        link = "".join([self.urlbase, souptagobject.a["href"]])

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
            raise CommentNotFoundError(f"comment not found in post :{article_title}")





       # ..getting from post webpage..  time,category
        post = requests.get(link)
        soup_for_post = BeautifulSoup(post.text, "lxml")

        category,time_post = soup_for_post.find_all(class_=class_time_and_classification_in_postpage)
        time_post=time_post.text
        category=category.a.text

      # post id
        post_id = souptagobject.parent["data-key"]
        return {"gender":gender,"identify":identify,"category":category,"article title":article_title,"outline":outline,"link":link,"post id":post_id,"post time":time_post,"number of comments":number_of_comments,"setted to top":setted_to_top}




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

                gender=information.get(key_gender)
                identify=information.get(key_idenfity)
                category=information.get(key_category)

                article_title = information.get(key_articletitle)
                outline = information.get(key_outline)

                post_time=information.get(key_posttime)
                post_id=information.get(key_postid)
                link=information.get(key_link)

                number_of_comments=information.get(key_numberofcomments)

                setted_to_top=information.get(key_settedtotop)

                # recording article
                article_record["now"].append(post_id)

                if post_id in article_record["previous"]:
                    continue
                DcardSpider.__show_information(gender=gender,identify=identify,category=category,article_title=article_title,
                                 outline=outline, number_of_comments=number_of_comments,link=link,post_time=post_time,setted_to_top=setted_to_top)

            # update record
            article_record["previous"]=article_record["previous"]+article_record["now"]
            article_record["now"].clear()

        #close driver
        self.driver.close()
        self.driver=None


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




if __name__=="__main__":

    dsp = DcardSpider(url=ctg_female_sex)

    dsp.init_driver(hidediver=True)
    dsp.scraping(scrollingtime=30)
