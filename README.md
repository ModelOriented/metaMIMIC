# metaMIMIC

analysis of hyperparameter transferability for tabular data using MIMIC-IV database

## What is this?

This is a repository containing code used to reproduce the results presented in the metaMIMIC study available here: (not publicised yet).

## What is needed to reproduce the results?

To reproduce the results you will need the following:

* access to the MIMIC-IV data. Relevant information is available here: https://physionet.org/content/mimiciv/1.0/,
* a PostgreSQL database containing MIMIC-IV data. Relevant scripts are available here: https://github.com/MIT-LCP/mimic-iv/tree/master/buildmimic/postgres,
* a Python environment containing packages listed in the `requirements.txt` file (we suggest using the Miniconda distribution available here: https://docs.conda.io/en/latest/miniconda.html and running the `conda create --name metaMIMIC --file requirements.txt` command),
* code available in this repository.

It is important to mention that both the PostgreSQL database and the proposed calculations may be considered resource-heavy. It took us several days of CPU time using 48 cores and 256 GB of RAM to generate all the results.

## How to reproduce the results?

Results of the experiments are already available in the respective experiment directories, but you can also reproduce them by making sure you have all the above available and following these steps:

1. Create the *1_metaMIMIC_data/metaMIMIC.csv* file containing the base data for all models. To do this, provide PostgreSQL database credentials and location (username, password, host address, and database name) in the *1_metaMIMIC_data/connection_info.txt* file and run the *1_metaMIMIC_data/metaMIMIC_data.py* script (e.g. `cd 1_metaMIMIC_data && nano connection_info.txt && python metaMIMIC_data.py` on Linux).
2. Run the first two experiments. To do this, remove or rename the already provided *(2-3)\_metaMIMIC_experiment_(1-2)/results.csv* results file (the script will not run if it is present) and run the *(2-3)\_metaMIMIC_experiment_(1-2)/metaMIMIC_experiment_(1-2).py* script (e.g. `cd 2_metaMIMIC_experiment_1 && mv results.csv original_results.csv && python metaMIMIC_experiment_1` on Linux).
3. Prepare the data needed for the third experiment. To do this, run the *4_metaMIMIC_columns/metaMIMIC_columns.py* script (e.g. `cd 4_metaMIMIC_columns && python metaMIMIC_columns.py` on Linux).
4. Run the third experiment. To do this, remove or rename the already provided *5\_metaMIMIC_experiment_3/results.csv* results file (the script will not run if it is present) and run the *5\_metaMIMIC_experiment_3/metaMIMIC_experiment_3.py* script (e.g. `cd 5_metaMIMIC_experiment_3 && ls results* | xargs -I {} mv {} official_{} && python metaMIMIC_experiment_3.py` on Linux).
5. Run the last experiment. To do this, remove or rename the already provided *6\_metaMIMIC_experiment_bayes/results.csv* results file (the script will not run if it is present) and run the *6\_metaMIMIC_experiment_bayes/metaMIMIC_experiment_bayes.py* script (e.g. `cd 6_metaMIMIC_experiment_bayes && mv results.csv original_results.csv && python metaMIMIC_experiment_bayes.py` on Linux).

All the exemplary commands are supposed to be run from the toplevel directory of this repository.

## Additional information

Directory *mementoML_results* contains the results from the mementoML study available here: https://arxiv.org/abs/2008.13162. Our results were prepared using the same hyperparameter grid and we used the mementoML results for a comparison.

The code we used to analyse the results and prepare figures for the metaMIMIC paper can be found in the *results_analysis* directory.
