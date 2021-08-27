### metaMIMIC columns
# Below code is supposed to be run using the CSV file created with 'metaMIMIC data script'.

import os
import numpy as np
import pandas as pd
import xgboost as xgb
import dalex as dx
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score, StratifiedKFold

## Settings

# Path of the 'metaMIMIC data script' output:

data_path = '../1_metaMIMIC_data/metaMIMIC.csv'

# Path of the output files in CSV form:

output_path = './columns'

## Load data

data = pd.read_csv(data_path)

## Separate data into balanced halves

data = data.sort_values(list(data.columns[-12:-1])).reset_index()
data['half'] = pd.Series(np.array(data.index)%2==0, dtype=int) + 1

## Prepare data for predictor selection model

X = data.iloc[:, 2:-13].values
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
X_imp = pd.DataFrame(imp.fit_transform(X), columns=data.columns[2:-13])

## Select predictors (using default XGBoost and permutation variable importance) and save to CSV files

for count in [10, 20, 50, 100]:
    if not os.path.exists(f'{output_path}/columns_{count}'): os.makedirs(f'{output_path}/columns_{count}')

for count, target in enumerate(data.columns[-13:-1]):
    y = data.loc[:, target].values
    model = xgb.XGBClassifier(use_label_encoder=False, verbosity=0)
    model.fit(X_imp, y)
    
    explainer = dx.Explainer(model, X_imp, y, verbose=False)
    mp = explainer.model_parts(loss_function='1-auc', random_state=1)
    df = mp.permutation.agg([np.mean, np.std])
    
    for count in [10, 20, 50, 100]:
        variables = list(df.transpose().sort_values('mean', ascending=False).iloc[:(count+1), ].index[1:])
        out = data.loc[:, ['index', 'half', *variables, target]]

        out_1 = out[out['half']==1].drop('half', axis=1)
        # mean imputation disabled
        # out_1 = pd.DataFrame(imp.fit_transform(out_1), columns=['index', *variables, 'target'])
        out_1.to_csv(f'{output_path}/columns_{count}/{target}_1.csv', index=False)

        out_2 = out[out['half']==2].drop('half', axis=1)
        # mean imputation disabled
        # out_2 = pd.DataFrame(imp.fit_transform(out_2), columns=['index', *variables, 'target'])
        out_2.to_csv(f'{output_path}/columns_{count}/{target}_2.csv', index=False)
