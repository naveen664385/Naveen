import random as rd
from sklearn import datasets
import matplotlib.pyplot as pt
import pylab as pl
%matplotlib inline
digits=datasets.load_digits()
x=digits.images.reshape(len(digits.images),-1)
dimages=digits.images
dtarget=digits.target
ddata=digits.data
dimages.shape
len(x)
sample_index=rd.sample(range(len(x)),350)#220 is number of indices
valid_index=[i for i in range(len(x))]
sample_images=[x[i] for i in sample_index]
valid_images=[x[i] for i in valid_index]
sample_target=[dtarget[i] for i in sample_index]
valid_target=[dtarget[i] for i in valid_index]
from sklearn import ensemble
classifier=ensemble.RandomForestClassifier()
classifier.fit(sample_images,sample_target)
score=classifier.score(valid_images,valid_target)
print(score)
j=0
for i in range(1797):
    final=classifier.predict(x[i].reshape(1,-1))
    if dtarget[i]==final[0]:
        pass
    else:
        j=j+1
        print('Not matched',i)
print (j)
        
i=125
pl.imshow(images[i],cmap='gray')
pl.rcParams['figure.figsize'] = (15,15)
final=classifier.predict(x[i].reshape(1,-1))
print('pedicted',final[0])
print('actual',dtarget[i])

