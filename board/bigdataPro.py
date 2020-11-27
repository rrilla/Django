from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import os
import pandas as pd
import numpy as np
import requests
from pyBoard.settings import STATIC_DIR, TEMPLATE_DIR

from collections import Counter # 단어들을 집계하기 위해서 사용
from konlpy.tag import Okt # 형태소 분석기
import pytagcloud #pygame 패키지에 의존적, pygame 설치 요구
import folium
from folium import plugins


def movie_crawling(data):
    for i in range(1, 50):
        url = "https://movie.naver.com/movie/point/af/list.nhn?&page="
        url = url + str(i)
        req = requests.get(url)
        if req.ok :
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            titles = soup.select('.title a.movie')
            points = soup.select('.title em')
            contents = soup.select('.title')
            n = len(titles)
            
            for i in range(n):
                title = titles[i].text
                point = points[i].text
                contentarr = contents[i].text.replace('신고', '').split('\n\n')
                content = contentarr[2].replace("\t",'').replace('\n',"")
                data.append([title,point,content])
                
def make_graph(titles, points):
    font_location = "C:/Windows/Fonts/gulim.ttc" 
    font_name = font_manager.FontProperties(fname=font_location).get_name()
    rc('font', family=font_name)
    
    plt.xlabel('영화제목')
    plt.ylabel('평균평점')
    plt.grid(True)
    #'int(), float() df['필드명'].astype(float32)'    
    plt.bar(range(len(titles)), points, align='center')
    plt.xticks(range(len(titles)), list(titles), rotation='70')
    plt.savefig(os.path.join(STATIC_DIR,'images/fig01.png'), dpi=300)
    
def saveWordcloud(contents):
    nlp = Okt()
    wordtext=""
    for t in contents:
        wordtext+=str(t)+" "
        
    nouns = nlp.nouns(wordtext)
    count = Counter(nouns)
    
    wordInfo = dict()
    for tags, counts in count.most_common(100):
        if (len(str(tags)) > 1):
            wordInfo[tags] = counts
    filename=os.path.join(STATIC_DIR,'images/wordcloud01.png')
    taglist = pytagcloud.make_tags(dict(wordInfo).items(), maxsize=80)
    pytagcloud.create_tag_image(taglist, filename, 
                                size=(640, 480), 
                                fontname='Korean', rectangular=False)

def make_wordcloud(data):
    f=open("data_al/data.txt",encoding='utf-8')
    data=f.read()
    #data
    npl=Okt() # 형태소 분석기 Okt 생성,Kkma, Mecab-kr, HanNum 등
    nouns=npl.nouns(data) # 형태소 분석기로 단어 추출
    #nouns
    count=Counter(nouns) # 단어 집계
    #count
    tag2=count.most_common(20) # 상위 20개만 추출
    taglist=pytagcloud.make_tags(tag2,maxsize=80) # tag2데이터로 태그 생성
    #taglist
    f.close()

    pytagcloud.create_tag_image(taglist, 'wordcloud.jpg', size=(900, 600), fontname='Korean', rectangular=False)
    
def cctv_map():
    popup=[]
    data_lat_log=[]
    a_path='e:/data/'
    df=pd.read_csv(os.path.join(a_path,"cctv.csv"),encoding="utf-8")
    for data in df.values:
        if data[4]>0:
            popup.append(data[2])
            data_lat_log.append([data[3],data[4]])
            
    m=folium.Map([35.1803305,129.0516257], zoop_start=11)
    plugins.MarkerCluster(data_lat_log,popups=popup).add_to(m)
    m.save(os.path.join(TEMPLATE_DIR,"map/map01.html"))   
     

