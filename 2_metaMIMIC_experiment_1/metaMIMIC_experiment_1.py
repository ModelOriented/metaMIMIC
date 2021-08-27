### metaMIMIC experiment 1

import time, os.path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_score

data = pd.read_csv('../1_metaMIMIC_data/metaMIMIC.csv')

if os.path.isfile('./results.csv'):
    print('Results file already exists, aborting execution.')
    exit()

X = data.iloc[:, 1:-12]
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
X = imp.fit_transform(X)
ys = data.iloc[:, -12:].to_numpy()

param_sets_raw = pd.read_csv('./grid.csv').drop(['param_index', 'missing'], axis=1).iloc[1:,].to_dict('records')
param_sets = []
for param_set in param_sets_raw:
    param_set['n_estimators'] = param_set['nrounds']
    param_set.pop('nrounds')
    param_set['learning_rate'] = param_set['eta']
    param_set.pop('eta')
    param_sets.append(param_set)

with open('./results.csv', 'w') as f:
    f.write('set_index,target,booster,subsample,max_depth,min_child_weight,colsample_bytree,colsample_bylevel,n_estimators,learning_rate,CV,AUC')
cv = StratifiedKFold(n_splits=4, random_state=1, shuffle=True)
for i in range(len(param_sets)):
    for j in range(ys.shape[1]):
        print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}, param_set: {i+1}/{len(param_sets)}, target: {j+1}/{ys.shape[1]}')
        y = ys[:, -(12-j)]
        model = xgb.XGBClassifier(**param_sets[i], n_jobs = 12, use_label_encoder=False, verbosity=0)
        scores = cross_val_score(model, X, y, scoring='roc_auc', cv=cv, n_jobs=4)
        with open('./results.csv', 'a') as f:
            for k in range(len(scores)):
                f.write(f'\n{i},{data.columns[-(12-j)]},{(str(param_sets[i].values())[13:-2]).replace(" ", "")},{k+1},{round(scores[k], 6)}')
