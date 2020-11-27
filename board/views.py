from django.shortcuts import render, redirect
from board.models import Board, Comment, Movie
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.http import urlquote
from django.db.models import Q
import os
import math
from board import bigdataPro
from django.db.models.aggregates import Avg
import pandas as pd
UPLOAD_DIR='e:/upload/' #upload 폴더 

# Create your views here.
def movie_save(request):
    data = []
    bigdataPro.movie_crawling(data)
    for row in data:
        dto=Movie(title=row[0],point=int(row[1]),content=row[2])
        dto.save()
    return redirect('list/')

def chart(request):
    #sql='select title,avg(point) points from board_movie group by title'
    #data=Movie.objects.raw(sql)
    data=Movie.objects.values('title').annotate(point_avg=Avg('point'))[0:10]
    df=pd.DataFrame(data)
    bigdataPro.make_graph(df.title, df.point_avg)
    return render(request,"chart.html",{"data":data})

def wordcloud(request):
    content = Movie.objects.values('content')
    df = pd.DataFrame(content)
    bigdataPro.saveWordcloud(df.content)
    return render(request,"wordcloud.html",{"contents" : df.content})

def cctv_map(request):
    bigdataPro.cctv_map()
    return render(request, "map/map01.html")
    
@csrf_exempt 
def list(request): 
    #검색옵션, 검색값 
    try: #예외가 발생할 가능성이 있는 코드 
        search_option = request.POST["search_option"]
    except: #예외가 발생했을 때의 코드 
        search_option = "writer" 
        
    try: 
        search= request.POST["search"] 
    except: 
        search = "" 
        
    if search_option=="all":
        boardCount=Board.objects.filter(
            Q(writer__contains=search) |
            Q(title__contains=search) |
            Q(content__contains=search)).count()
    elif search_option=='writer':
        boardCount=Board.objects.filter(writer__contains=search).count()
    elif search_option=='title':
        boardCount=Board.objects.filter(title__contains=search).count()
    elif search_option=='content':
        boardCount=Board.objects.filter(content__contains=search).count()
    else:
        boardCount=Board.objects.all().count()
        
        
    try:
        start=int(request.GET['start'])
    except:
        start = 0
        
    page_size = 5
    block_size = 3
    end = start + page_size
    total_page = math.ceil(boardCount/page_size)
    current_page = math.ceil((start+1)/page_size)
    start_page = math.floor((current_page-1)/block_size)*block_size+1
    end_page = start_page+block_size-1
    
    if end_page > total_page:
        end_page = total_page
    
    if start_page >= block_size:
        prev_list = (start_page-2)*page_size
    else:
        prev_list = 0
    
    if end_page < total_page:
        next_list = end_page*page_size
    else:
        next_list = 0
        
    if search_option=="all":
        boardList=Board.objects.filter(
            Q(writer__contains=search) |
            Q(title__contains=search) |
            Q(content__contains=search)).order_by('-idx')[start:end]
    elif search_option=='writer':
        boardList=Board.objects.filter(writer__contains=search).order_by('-idx')[start:end]
    elif search_option=='title':
        boardList=Board.objects.filter(title__contains=search).order_by('-idx')[start:end]
    elif search_option=='content':
        boardList=Board.objects.filter(content__contains=search).order_by('-idx')[start:end]
    else:
        boardList=Board.objects.all().order_by('-idx')[start:end] 
        
    links = []
    for i in range(start_page, end_page + 1):
        page_start = (i-1)*page_size
        links.append("<li class='page-item'><a class='page-link' href='/list?start="+str(page_start)+"'>"+str(i)+"</a></li>")
    
    return render(request, "list.html",
                  {"boardList":boardList,
                   "boardCount":boardCount,
                   "search_option":search_option,
                   "search":search,
                   "range":range(start_page-1, end_page),
                   "start_page":start_page,
                   "end_page":end_page,
                   "block_size":block_size,
                   "total_page":total_page,
                   "priv_list":prev_list,
                   "next_list":next_list,
                   "links":links})

def list2(request): 
    boardCount = Board.objects.count() 
    boardList = Board.objects.all().order_by("-idx") 
    return render(request, 'list.html', {"boardList":boardList, "boardCount":boardCount})

def write(request): 
    return render(request, "write.html")

@csrf_exempt
def insert(request): 
    fname = "" 
    fsize = 0 
    if "file" in request.FILES: #d\request.FILES에 file이 있는가 - 파일넘어왓는가
        file=request.FILES["file"] 
        fname = file.name 
        fsize = file.size 
        fp=open("%s%s" % (UPLOAD_DIR, fname), "wb") 
        for chunk in file.chunks(): 
            fp.write(chunk) 
        fp.close() 
        
    dto = Board( writer=request.POST["writer"],title=request.POST["title"], content=request.POST["content"], filename=fname,filesize=fsize ) 
    dto.save() 
    print(dto) 
    return redirect("list/") 

def download(request): 
    id=request.GET['idx'] 
    dto=Board.objects.get(idx=id) 
    path = UPLOAD_DIR+dto.filename 
    filename= os.path.basename(path) 
    filename = filename.encode("utf-8") 
    filename = urlquote(filename) 
    with open(path, 'rb') as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response["Content-Disposition"] = "attachment; filename*=UTF-8''{0}".format(filename)
        dto.down_up() 
        dto.save() 
        return response

def detail(request): 
    #조회수 증가 처리 
    id=request.GET["idx"] 
    dto=Board.objects.get(idx=id) 
    dto.hit_up() 
    dto.save() 
    commentList = Comment.objects.filter(board_idx = id).order_by("-idx")
    print("filesize:",dto.filesize) 
    #filesize = "%0.2f" % (dto.filesize / 1024) 
    filesize = "%.2f" % (dto.filesize) 
    return render(request, "detail.html", {"dto": dto, "filesize":filesize, "commentList":commentList})

@csrf_exempt 
def reply_insert(request): 
    id=request.POST["idx"] #게시물 번호 
    #댓글 객체 생성 
    dto = Comment(board_idx=id,
                  writer=request.POST["writer"], 
                  content=request.POST["content"]) 
    #insert query 실행 
    dto.save() 
    # detail?idx=글번호 페이지로 이동 
    return HttpResponseRedirect("detail?idx=" + id)

@csrf_exempt 
def update(request): 
    id=request.POST["idx"] #글번호 
    #select * from board_board where idx=id 
    dto_src=Board.objects.get(idx=id) 
    fname=dto_src.filename #기존 첨부파일 이름 
    fsize=0 #기존 첨부파일 크기 
    if "file" in request.FILES: #새로운 첨부파일이 있으면 
        file=request.FILES["file"] 
        fname=file.name #새로운 첨부파일의 이름 
        fp = open("%s%s" % (UPLOAD_DIR, fname), "wb") 
        for chunk in file.chunks(): 
            fp.write(chunk) #파일 저장 
        fp.close() 
        #첨부파일의 크기(업로드완료 후 계산 
        fsize=os.path.getsize(UPLOAD_DIR+fname) 
    #수정 후 board의 내용 
    dto_new = Board(idx=id,title=request.POST["title"], writer=request.POST["writer"],
                    content=request.POST["content"], filename=fname, filesize=fsize) 
    dto_new.save() #update query 호출 
    return redirect("list/") #시작 페이지로 이동

@csrf_exempt 
def delete(request): 
    id=request.POST["idx"] #삭제할 게시물의 번호
    Board.objects.get(idx=id).delete() #레코드 삭제
    return redirect("list/") #시작 페이지로 이동