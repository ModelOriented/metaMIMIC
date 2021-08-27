### metaMIMIC experiment 3

import os, time
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
import scipy, skopt

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

estimator = xgb.XGBClassifier(
        n_jobs = 12,
        use_label_encoder=False,
        verbosity=0
)

search_spaces = {
        'booster': ['gbtree', 'gblinear'],
        'subsample': skopt.space.space.Real(0.5, 1),
        'max_depth': skopt.space.space.Integer(6, 15),
        'min_child_weight': skopt.space.space.Real(1, 8),
        'colsample_bytree': skopt.space.space.Real(0.2, 1),
        'colsample_bylevel': skopt.space.space.Real(0.2, 1),
        'n_estimators': skopt.space.space.Integer(1, 1000),
        'learning_rate': skopt.space.space.Real(0.03, 1)
}

cv = StratifiedKFold(n_splits=4, random_state=1, shuffle=True)

with open('./results.csv', 'w') as f:
    f.write('target,half,set_index,booster,subsample,max_depth,min_child_weight,colsample_bytree,colsample_bylevel,n_estimators,learning_rate,CV,AUC')

for i in range(ys_1.shape[1]):
    print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}, target: {i+1}/{ys_1.shape[1]}, half: 1/2')
    y_1 = ys_1[:, -(12-i)]
    opt_1 = skopt.BayesSearchCV(
        estimator=estimator,
        search_spaces=search_spaces,
        cv=cv,
        scoring='roc_auc',
        n_jobs=4,
        n_iter=100,
        verbose=0,
        random_state=1
    )
    opt_1.fit(X_1, y_1)
    results_1 = pd.DataFrame(opt_1.cv_results_)
    with open('./results.csv', 'a') as f:
            for j in range(len(results_1)):
                for k in range(4):
                    f.write(f'\n{sorted_data.columns[-(12-i)]},1,{j},{results_1["param_booster"][j]},{results_1["param_subsample"][j]},{results_1["param_max_depth"][j]},{results_1["param_min_child_weight"][j]},{results_1["param_colsample_bytree"][j]},{results_1["param_colsample_bylevel"][j]},{results_1["param_n_estimators"][j]},{results_1["param_learning_rate"][j]},{k+1},{results_1[f"split{k}_test_score"][j]}')
    print(f'current time: {time.strftime("%d.%m.%Y %H:%M:%S UTC")}, target: {i+1}/{ys_1.shape[1]}, half: 2/2')
    y_2 = ys_2[:, -(12-i)]
    opt_2 = skopt.BayesSearchCV(
        estimator=estimator,
        search_spaces=search_spaces,
        cv=cv,
        scoring='roc_auc',
        n_jobs=4,
        n_iter=100,
        verbose=0,
        random_state=1
    )
    opt_2.fit(X_2, y_2)
    results_2 = pd.DataFrame(opt_2.cv_results_)
    with open('./results.csv', 'a') as f:
            for j in range(len(results_2)):
                for k in range(4):
                    f.write(f'\n{sorted_data.columns[-(12-i)]},2,{j},{results_2["param_booster"][j]},{results_2["param_subsample"][j]},{results_2["param_max_depth"][j]},{results_2["param_min_child_weight"][j]},{results_2["param_colsample_bytree"][j]},{results_2["param_colsample_bylevel"][j]},{results_2["param_n_estimators"][j]},{results_2["param_learning_rate"][j]},{k+1},{results_2[f"split{k}_test_score"][j]}')
    
exit()    
