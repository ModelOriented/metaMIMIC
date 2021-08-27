### metaMIMIC experiment 2

import time, os.path
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_score

if os.path.isfile('./results.csv'):
    print('Results file already exists, aborting execution.')
    exit()

data = pd.read_csv('../1_metaMIMIC_data/metaMIMIC.csv')
sorted_data = data.sort_values(list(data.columns[-12:])).reset_index(drop=True)

X_1 = sorted_data.iloc[np.array(sorted_data.index)%2==0, 1:-12]
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
X_1 = imp.fit_transform(X_1)
ys_1 = sorted_data.iloc[np.array(sorted_data.index)%2==0, -12:].to_numpy()

X_2 = sorted_data.iloc[np.array(sorted_data.index)%2==1, 1:-12]
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
X_2 = imp.fit_transform(X_2)
ys_2 = sorted_data.iloc[np.array(sorted_data.index)%2==1, -12:].to_numpy()

param_sets_raw = pd.read_csv('./grid.csv').drop(['param_index', 'missing'], axis=1).iloc[1:,].to_dict('records')
param_sets = []
for param_set in param_sets_raw:
    param_set['n_estimators'] = param_set['nrounds']
    param_set.pop('nrounds')
    param_set['learning_rate'] = param_set['eta']
    param_set.pop('eta')
    param_sets.append(param_set)

with open('./results.csv', 'w') as f:
    f.write('set_index,target,half,booster,subsample,max_depth,min_child_weight,colsample_bytree,colsample_bylevel,n_estimators,learning_rate,CV,AUC')

cv = StratifiedKFold(n_splits=4, random_state=1, shuffle=True)
for i in range(len(param_sets)):
    for j in range(ys_1.shape[1]):
        print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}, param_set: {i+1}/{len(param_sets)}, target: {j+1}/{ys_1.shape[1]}, half: 1/2')
        y_1 = ys_1[:, -(12-j)]
        model = xgb.XGBClassifier(**param_sets[i], n_jobs = 12, use_label_encoder=False, verbosity=0)
        scores = cross_val_score(model, X_1, y_1, scoring='roc_auc', cv=cv, n_jobs=4)
        with open('./results.csv', 'a') as f:
            for k in range(len(scores)):
                f.write(f'\n{i},{sorted_data.columns[-(12-j)]},1,{(str(param_sets[i].values())[13:-2]).replace(" ", "")},{k+1},{round(scores[k], 6)}')
                
        print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}, param_set: {i+1}/{len(param_sets)}, target: {j+1}/{ys_1.shape[1]}, half: 2/2')
        y_2 = ys_2[:, -(12-j)]
        model = xgb.XGBClassifier(**param_sets[i], n_jobs = 12, use_label_encoder=False, verbosity=0)
        start = time.time()
        scores = cross_val_score(model, X_2, y_2, scoring='roc_auc', cv=cv, n_jobs=4)
        elapsed = round(time.time()-start, 2)
        with open('./results.csv', 'a') as f:
            for k in range(len(scores)):
                f.write(f'\n{i},{sorted_data.columns[-(12-j)]},2,{(str(param_sets[i].values())[13:-2]).replace(" ", "")},{k+1},{round(scores[k], 6)}')
