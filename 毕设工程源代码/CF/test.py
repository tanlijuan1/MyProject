#!/usr/bin/python3
# -*- coding: utf-8 -*-
from numpy import *
import sys
import pymysql

class CF:
    def __init__(self, problems, ratings, k=1, n=10):
        self.problems = problems
        self.ratings = ratings
        # 邻居个数
        self.k = k
        # 推荐个数
        self.n = n
        # 用户对学术资源的评分
        # 数据格式{'UserID：用户ID':[(FIleID：文件ID,Rating：用户对文件的下载量)]}
        self.userDict = {}
        # 对某学术资源进行下载的用户
        # 数据格式：{'FIleID：文件ID',[UserID：用户ID]}
        # {'1',[1,2,3..],...}
        self.ItemUser = {}
        # 邻居的信息
        self.neighbors = []
        # 推荐列表
        self.recommandList = []
        self.cost = 0.0

    # 基于用户的推荐
    # 根据对文件的下载量计算用户之间的相似度
    def recommendByUser(self, userId):
        self.formatRate()  #转换函数
        self.getNearestNeighbor(userId) # 找到某用户的相邻用户
        self.getrecommandList(userId) # 获取推荐列表
        # self.getPrecision(userId)#打印数据
        for i in self.recommandList:
            print(i[1], end=',')

    # 获取推荐列表
    def getrecommandList(self, userId):
        self.recommandList = []
        # 建立推荐字典
        recommandDict = {}
        for neighbor in self.neighbors:
            problems = self.userDict[neighbor[1]]
            for problem in problems:
                if (problem[0] in recommandDict):
                    recommandDict[problem[0]] += neighbor[0]
                else:
                    recommandDict[problem[0]] = neighbor[0]

        # 建立推荐列表
        for key in recommandDict:
            self.recommandList.append([recommandDict[key], key])
        self.recommandList.sort(reverse=True)
        self.recommandList = self.recommandList[:self.n]

    # 将ratings转换为userDict和ItemUser
    def formatRate(self):
        self.userDict = {}
        self.ItemUser = {}
        for i in self.ratings:
            i = i[0].split('\t')
            # 评分最高为100 除以100 进行数据归一化,这个是计算的，就是算出来的然后除以100，得到你的一个有序集合，百分制或者十分制
            temp = (i[1], float(i[2]) / 100)
            # 计算userDict {'1':[(1,5),(2,5)...],'2':[...]...}
            if (i[0] in self.userDict):
                self.userDict[i[0]].append(temp)
            else:
                self.userDict[i[0]] = [temp]
            # 计算ItemUser {'1',[1,2,3..],...}
            if (i[1] in self.ItemUser):
                self.ItemUser[i[1]].append(i[0])
            else:
                self.ItemUser[i[1]] = [i[0]]

    # 找到某用户的相邻用户
    def getNearestNeighbor(self, userId):
        neighbors = []
        self.neighbors = []
        # 获取userId下载的学术资源文件都有哪些用户也下载过
        for i in self.userDict[userId]:
            for j in self.ItemUser[i[0]]:
                if (j != userId and j not in neighbors):
                    neighbors.append(j)
        # 计算这些用户与userId的相似度并排序
        for i in neighbors:
            dist = self.getCost(userId, i)
            self.neighbors.append([dist, i])
        # 排序默认是升序，reverse=True表示降序
        self.neighbors.sort(reverse=True)
        self.neighbors = self.neighbors[:self.k]

    # 格式化userDict数据
    def formatuserDict(self, userId, l):
        user = {}
        for i in self.userDict[userId]:
            user[i[0]] = [i[1], 0]
        for j in self.userDict[l]:
            if (j[0] not in user):
                user[j[0]] = [0, j[1]]
            else:
                user[j[0]][1] = j[1]
        return user

    # 计算余弦距离
    def getCost(self, userId, l):
        # 获取用户userId和l下载学术资源文件的并集
        # {'学术资源文件ID'：[userId的评分，l的评分]} 没有评分为0
        user = self.formatuserDict(userId, l)
        x = 0.0
        y = 0.0
        z = 0.0
        for k, v in user.items():
            x += float(v[0]) * float(v[0])
            y += float(v[1]) * float(v[1])
            z += float(v[0]) * float(v[1])
        if (z == 0.0):
            return 0
        return z / sqrt(x * y)

    # 推荐的准确率
    def getPrecision(self, userId):
        user = [i[0] for i in self.userDict[userId]]
        recommand = [i[1] for i in self.recommandList]
        count = 0.0
        if (len(user) >= len(recommand)):
            for i in recommand:
                if (i in user):
                    count += 1.0
            self.cost = count / len(recommand)
        else:
            for i in user:
                if (i in recommand):
                    count += 1.0
            self.cost = count / len(user)


# 获取数据
def readFile(filename):
    # files = open(filename, "r", encoding="utf-8")
    # utf-8读取会失败
    files = open(filename, "r", encoding="iso-8859-15")
    data = []
    for line in files.readlines():
        item = line.strip().split("::")
        data.append(item)
    return data


# -------------------------开始-------------------------------
# 创建数据库链接
db = pymysql.connect("localhost", "root", "123456", "academicsystem")

# cursor()创建游标
cursor = db.cursor()

# 使用 execute()  方法执行 SQL 查询
cursor.execute("select file_id from file_entity")

# 使用 fetchall() 方法获取所有结果数据.
dataset = cursor.fetchall()

problems = []
# 遍历结果集构造题目数据
for row in dataset:
    problems.append([str(row[0])])
print(problems)

ratings = []
cursor.execute("select distinct user_entity.user_id,log_entity.log_params file_id,file_entity.down_times FROM log_entity,file_entity,user_entity WHERE log_entity.log_params = file_entity.file_id and log_entity.log_username = user_entity.user_name and log_operation='下载文件'")
# 
dataset = cursor.fetchall()
print (dataset)

# 遍历结果集构造评分数据
for row in dataset:
    ratings.append([str(row[0])+"\t"+str(row[1])+"\t"+str(row[2])])
print("分割")
print(ratings)

demo = CF(problems, ratings, k=10, n=5)#n为推荐列表中取出的数量
userId = sys.argv[1]
demo.recommendByUser(userId)
