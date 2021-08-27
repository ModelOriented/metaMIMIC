### metaMIMIC data
# Below code is supposed to be run using clean MIMIC-IV PostgreSQL database created with these scripts https://github.com/MIT-LCP/mimic-iv/tree/master/buildmimic/postgres.

import psycopg2 as ps2
import numpy as np
import pandas as pd

## Settings

# Path of the connection_info.txt file in the following form:
# username
# password
# host_address
# database_name

connection_info_path = './connection_info.txt'

# Path of the output file in CSV form:

output_path = './metaMIMIC.csv'

## Connect to the MIMIC-IV PostgreSQL database

# extract connection info
connection_info = open(connection_info_path, 'r')
username = str.rstrip(connection_info.readline())
password = str.rstrip(connection_info.readline())
host_address = str.rstrip(connection_info.readline())
database_name = str.rstrip(connection_info.readline())
connection_info.close()

# connect to database
try:
    conn = ps2.connect(
        user = username,
        password = password,
        host = host_address,
        database = database_name
    )
    conn.autocommit = True
except:
    print('Unable to connect to the database.')

## Create the 'mimic_processing' schema

# create schema
with conn.cursor() as curs:
    curs.execute(f"""
        CREATE SCHEMA mimic_processing
        AUTHORIZATION {username};
    """)
    
## Create and fill the 'mimic_processing.patients' table

# create table
with conn.cursor() as curs:
    curs.execute(f"""
        CREATE TABLE mimic_processing.patients(
            subject_id integer NOT NULL,
            PRIMARY KEY (subject_id)
        );

        ALTER TABLE mimic_processing.patients
        OWNER TO {username};
    """)
    
# fill subject_id, age, gender, first_admission_id, time_spent, died
with conn.cursor() as curs:
    curs.execute(f"""
        INSERT INTO mimic_processing.patients
        SELECT subject_id
        FROM mimic_core.patients;

        ALTER TABLE mimic_processing.patients
        ADD age INTEGER,
        ADD gender INTEGER;

        UPDATE mimic_processing.patients
        SET
            age = temp.age,
            gender = temp.gender
        FROM
            (SELECT
                subject_id,
                anchor_age age,
                (CASE WHEN gender = 'F' THEN 1 ELSE 0 END) gender
            FROM mimic_core.patients) temp
        WHERE mimic_processing.patients.subject_id = temp.subject_id;

        ALTER TABLE mimic_processing.patients
        ADD first_admission_id INTEGER;

        UPDATE mimic_processing.patients
        SET first_admission_id = hadm_id
        FROM
            (SELECT
                DISTINCT ON (subject_id)
                subject_id,
                hadm_id
            FROM mimic_core.admissions
            ORDER BY
                subject_id,
                admittime) temp
        WHERE mimic_processing.patients.subject_id = temp.subject_id;

        ALTER TABLE mimic_processing.patients
        ADD time_spent INTERVAL,
        ADD died BOOLEAN;

        UPDATE mimic_processing.patients
        SET
            time_spent = temp.time_spent,
            died = temp.died
        FROM
            (SELECT
                x.subject_id,
                (dischtime - admittime) time_spent,
                (CASE WHEN deathtime IS NULL THEN FALSE ELSE TRUE END) died
            FROM mimic_processing.patients x
            LEFT JOIN mimic_core.admissions y
            ON
                x.subject_id = y.subject_id AND
                x.first_admission_id = y.hadm_id) temp
        WHERE mimic_processing.patients.subject_id = temp.subject_id;
    """)

# fill chartevents_count, outputevents_count, labevents_count, microbiologyevents_count, diagnoses_count
with conn.cursor() as curs:
    counts = {
        'chartevents_count': 'mimic_icu.chartevents',
        'outputevents_count': 'mimic_icu.outputevents',
        'labevents_count': 'mimic_hosp.labevents',
        'microbiologyevents_count': 'mimic_hosp.microbiologyevents',
        'diagnoses_count': 'mimic_hosp.diagnoses_icd'
    }
    for key, value in counts.items():
        curs.execute(f"""
            ALTER TABLE mimic_processing.patients
            ADD {key} INTEGER;

            UPDATE mimic_processing.patients
            SET {key} = temp.{key}
            FROM
                (SELECT
                    x.subject_id,
                    SUM(CASE WHEN y.hadm_id IS NULL THEN 0 ELSE 1 END) {key}
                FROM mimic_processing.patients x
                LEFT JOIN {value} y
                ON
                    x.subject_id = y.subject_id AND
                    x.first_admission_id = y.hadm_id
                GROUP BY
                    x.subject_id,
                    x.first_admission_id) temp
                WHERE mimic_processing.patients.subject_id = temp.subject_id;
        """)

# fill all the diagnoses
with conn.cursor() as curs:
    diagnoses = {
        'diabetes_diagnosed': "LEFT(icd_code, 3) IN ('249', '250', 'E08', 'E09', 'E10', 'E11', 'E12', 'E13')",
        'hypertensive_diagnosed': "LEFT(icd_code, 3) IN ('401', '402', '403', '404', '405', 'I10', 'I11', 'I12', 'I13', 'I14', 'I15', 'I16')",
        'ischematic_diagnosed': "LEFT(icd_code, 3) IN ('410', '411', '412', '413', '414', 'I20', 'I21', 'I22', 'I23', 'I24', 'I25')",
        'heart_diagnosed': "LEFT(icd_code, 3) IN ('428', 'I50')",
        'overweight_diagnosed': "LEFT(icd_code, 3) IN ('278', 'E65', 'E66', 'E67', 'E68')",
        'anemia_diagnosed': "LEFT(icd_code, 3) IN ('280', '281', '282', '283', '284', '285', 'D60', 'D61', 'D62', 'D63', 'D64')",
        'respiratory_diagnosed': "LEFT(icd_code, 3) IN ('466', '490', '491', '492', '493', '494', '495', '496', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J46', 'J47')",
        'hypotension_diagnosed': "LEFT(icd_code, 3) IN ('458', 'I95')",
        'lipoid_diagnosed': "LEFT(icd_code, 3) IN ('272', 'E78')",
        'atrial_diagnosed': "LEFT(icd_code, 5) = '427.3' OR LEFT(icd_code, 3) = 'I48'",
        'purpura_diagnosed': "LEFT(icd_code, 3) IN ('287', 'D69')",
        'alcohol_diagnosed': "LEFT(icd_code, 3) IN ('303', 'F10')"
    }
    for key, value in diagnoses.items():
        curs.execute(f"""
            ALTER TABLE mimic_processing.patients
            ADD IF NOT EXISTS {key} BOOLEAN;

            UPDATE mimic_processing.patients
            SET {key} = temp.{key}
            FROM
            (SELECT
                x.subject_id,
                (CASE WHEN y.hadm_id IS NULL THEN FALSE ELSE TRUE END) {key}
                FROM mimic_processing.patients x
                LEFT JOIN
                    (SELECT *
                    FROM mimic_hosp.diagnoses_icd
                    WHERE {value}) y
                ON
                    x.subject_id = y.subject_id AND
                    x.first_admission_id = y.hadm_id) temp
            WHERE mimic_processing.patients.subject_id = temp.subject_id;
        """)

## Create the 'mimic_processing.patients_filtered' view

# create view
with conn.cursor() as curs:
    curs.execute("""
    CREATE VIEW mimic_processing.patients_filtered
    AS
        SELECT *
        FROM mimic_processing.patients
        WHERE
            patients.age > 0 AND
            patients.first_admission_id IS NOT NULL AND
            patients.chartevents_count > 0 AND
            patients.labevents_count > 0 AND
            patients.diagnoses_count > 0 AND
            patients.time_spent < '60 days'::interval;
    """)
    
## Aggregate predictors and create the final CSV file

# aggregate values using first value
with conn.cursor() as curs:
    first_input = {
        'mimic_icu.chartevents': 'itemid IN (226512, 226730)'
    }
    
    first_output = {}
    
    for key, value in first_input.items():
        df = pd.read_sql(f"""
            WITH temp AS (
                SELECT 
                    a.subject_id,
                    b.itemid, 
                    b.valuenum,
                    ROW_NUMBER() OVER(
                        PARTITION BY
                            a.subject_id,
                            b.itemid 
                    ORDER BY b.charttime) rank
            FROM mimic_processing.patients_filtered a
            LEFT JOIN
                (SELECT *
                FROM {key}
                WHERE {value}) b
            ON
                a.subject_id = b.subject_id AND
                a.first_admission_id = b.hadm_id)
            SELECT
                subject_id,
                itemid item_id,
                valuenum "first"
            FROM temp
            WHERE rank = 1
        """, conn)
        
        df = df[~df['item_id'].isna()].pivot(index='subject_id', columns='item_id', values=['first'])
        df.columns = df.columns.to_flat_index()
        df.columns = [f'{column[0]}_{int(column[1])}' for column in df.columns]
        df = df.reset_index()
        
        first_output[key] = df
        
# aggregate values using minimum, average and maximum value
with conn.cursor() as curs:
    agg_input = {
        'mimic_icu.chartevents': 'itemid IN (227073, 220546, 227457, 227465, 227466, 220045, 223761, 220179, 220180, 223900, 223901, 223791, 220210, 224054, 224055, 224056, 224057, 224058, 224059, 220739, 220228, 226253, 225624, 223834, 220277)',
        'mimic_hosp.labevents': 'itemid IN (50818, 50820, 50821, 50960, 51221, 51222, 50970, 50971, 51491, 50983, 50861, 50863, 51248, 51249, 51250, 50868, 50878, 51006, 51265, 50882, 50885, 50893, 51277, 51279, 50902, 50912, 51301, 50802, 50931, 50804, 50813)'
    }

    agg_output = {}

    for key, value in agg_input.items():
        df = pd.read_sql(f"""
            SELECT
                a.subject_id,
                b.itemid item_id,
                MIN(b.valuenum) min,
                AVG(b.valuenum) avg,
                MAX(b.valuenum) max
            FROM mimic_processing.patients_filtered a
            LEFT JOIN
                (SELECT *
                FROM {key}
                WHERE {value}) b
            ON
                a.subject_id = b.subject_id AND
                a.first_admission_id = b.hadm_id
            GROUP BY
                a.subject_id,
                b.itemid
        """, conn)
        
        df = df[~df['item_id'].isna()].pivot(index='subject_id', columns='item_id', values=['min', 'avg', 'max'])
        df.columns = df.columns.to_flat_index()
        df.columns = [f'{column[0]}_{int(column[1])}' for column in df.columns]
        df = df.reset_index()

        agg_output[key] = df
        
# create and save the final CSV file
patients_filtered = pd.read_sql('SELECT * from mimic_processing.patients_filtered', conn)

final = patients_filtered[['subject_id', 'age', 'gender']]
for key, value in first_output.items():
    final = final.merge(value, on='subject_id', how='left')
for key, value in agg_output.items():
    final = final.merge(value, on='subject_id', how='left')    
final = final.merge(patients_filtered.iloc[:, np.r_[0, 11:23]], on='subject_id')

final.to_csv(output_path, index=False)
