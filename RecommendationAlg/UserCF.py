__author__ = 'Jerry'

import numpy as np

from DataModel.FileDataModel import *
from utils.Similarity import Similarity
from DataModel.MemeryDataModel import *
from sklearn.base import BaseEstimator
from sklearn import cross_validation
from sklearn import metrics
from sklearn import grid_search
from sklearn.cross_validation import StratifiedKFold
from Eval.Evaluation import *

class UserCF(BaseEstimator):

    def __init__(self, neighbornum=5, n=5):
        print 'ucf begin'
        self.neighbornum = neighbornum
        self.similarity = Similarity('COSINE')
        self.n = n

    def predict(self,testSamples):
        recList = []
        for user_item in testSamples:
            uid = self.dataModel.getUidByUser(user_item[0])
            recList.append(self.recommend(uid))
        return recList

    def fit(self, trainSamples, trainTargets):
        #print len(trainSamples)
        self.dataModel = MemeryDataModel(trainSamples, trainTargets)
        usersNum = self.dataModel.getUsersNum()
        self.simiMatrix = np.zeros((usersNum, usersNum))
        for i in range(usersNum):
            for j in range(i+1, usersNum):
                s = self.similarity.compute(self.dataModel.getItemIDsFromUid(i), self.dataModel.getItemIDsFromUid(j))
                self.simiMatrix[i][j] = self.simiMatrix[j][i] = s

    def neighborhood(self, userID):
        neighbors = np.argsort(np.array(self.simiMatrix[userID]))[-1:-self.neighbornum-1:-1]
        return neighbors
    def predict_single(self, userID, itemID):
        rating = 0.0
        for uid in self.neighborhood(userID):
            if itemID in self.dataModel.getItemIDsFromUid(uid):
                rating += self.simiMatrix[userID][uid] * self.dataModel.getRating(uid, itemID)
        return rating
    def recommend(self, u):
        userID = self.dataModel.getUidByUser(u)
        if userID == -1:
            print 'not in test'
            return []
        else:
            #interactedItems = self.dataModel.getItemIDsFromUid(userID)
            ratings = dict()
            for uid in self.neighborhood(userID):
                for iid in self.dataModel.getItemIDsFromUid(uid):
                    #if iid in interactedItems:
                        #continue
                    r = ratings.get(iid, 0)
                    ratings[iid] = r + self.simiMatrix[userID][uid] * self.dataModel.getRating(uid, iid)
            r = [x for (x, y) in sorted(ratings.items(), lambda a, b: cmp(a[1], b[1]), reverse=True)[:self.n]]
            return [self.dataModel.getItemByIid(i) for i in r]
    def score(self, testSamples, trueLabels):
        print 'User_CF scoring ...'
        #print len(testSamples)
        trueList = []
        recommendList= []
        user_unique = list(set(np.array(testSamples)[:,0]))
        for u in user_unique:
            uTrueIndex = np.argwhere(np.array(testSamples)[:,0] == u)[:,0]
            #true = [self.dataModel.getIidByItem(i) for i in list(np.array(testSamples)[uTrueIndex][:,1])]
            true = list(np.array(testSamples)[uTrueIndex][:,1])
            trueList.append(true)
            pre = self.recommend(u)
            recommendList.append(pre)
        e = Eval()
        result = e.evalAll(recommendList, trueList)
        print 'UserCF result:'+'('+str(self.get_params())+')'+str((result)['F1'])
        return (result)['F1']


if __name__ == '__main__':
    nmf = UserCF()
    data = pd.read_csv('../Data/bbg/transaction.csv')
    samples = [[int(i[0]), int(i[1])] for i in data.values[:,0:2]]
    targets = [1 for i in samples]
    parameters = {'n':[5], 'neighbornum':[5]}
    labels = [int(i[0]) for i in data.values[:,0:2]]
    rec_cv =  StratifiedKFold(labels, 5)
    clf = grid_search.GridSearchCV(nmf, parameters,cv=rec_cv)
    clf.fit(samples, targets)
    print(clf.grid_scores_)
