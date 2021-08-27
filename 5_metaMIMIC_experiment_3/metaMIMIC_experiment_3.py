### metaMIMIC experiment 4

import os, time
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_score

param_sets_raw = pd.read_csv('./grid.csv').drop(['param_index', 'missing'], axis=1).iloc[1:,].to_dict('records')
param_sets = []
for param_set in param_sets_raw:
    param_set['n_estimators'] = param_set['nrounds']
    param_set.pop('nrounds')
    param_set['learning_rate'] = param_set['eta']
    param_set.pop('eta')
    param_sets.append(param_set)

cv = StratifiedKFold(n_splits=4, random_state=1, shuffle=True)  
    
for i, count in enumerate([10, 20, 50, 100]):
    if os.path.isfile(f'./results_{count}.csv'):
        print('Results file already exists, aborting execution.')
        exit()

    with open(f'./results_{count}.csv', 'w') as f:
        f.write('target,half,set_index,booster,subsample,max_depth,min_child_weight,colsample_bytree,colsample_bylevel,n_estimators,learning_rate,CV,AUC')      

    path = f'../4_metaMIMIC_columns/columns/columns_{count}'
    for j, file in enumerate(sorted(os.listdir(path))):
        target = file[:-6]
        half = int(file[-5])
        
        data = pd.read_csv(path+'/'+file, index_col=0)
        X = data.iloc[:, 1:-1]
        y = data.iloc[:, -1]

        for k, param_set in enumerate(param_sets):
            print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}\ncount: {i+1}/4 ({count}), file: {j+1}/24 ({file}), param_set: {k+1}/1000\n')
            model = xgb.XGBClassifier(**param_set, n_jobs = 12, use_label_encoder=False, verbosity=0)
            scores = cross_val_score(model, X, y, scoring='roc_auc', cv=cv, n_jobs=4)
            with open(f'./results_{count}.csv', 'a') as f:
                for l in range(len(scores)):
                    f.write(f'\n{target},{half},{k},{(str(param_sets[k].values())[13:-2]).replace(" ", "")},{l+1},{round(scores[l], 6)}')
                    
exit()
