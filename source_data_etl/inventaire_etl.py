# Description: ETL script to extract data from a csv file and load it into a SQL Server database

import pandas as pd
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_ADMIN_USERNAME = os.getenv('DATABASE_ADMIN_USERNAME')
DATABASE_ADMIN_PASSWORD = os.getenv('DATABASE_ADMIN_PASSWORD')

# Read all csv files in /data folder
data_frames = []
for file in os.listdir('data'):
    if file.endswith('.csv'):
        df = pd.read_csv(f'data/{file}')
        df['date_stock'] = file.split('_')[1].split('.')[0]
        data_frames.append(df)

# Concatenate all dataframes into a single dataframe
stock_df = pd.concat(data_frames, ignore_index=True)

# Drop columns
stock_df.drop(columns=['Units'], inplace=True)

# Rename columns
stock_df.rename(columns={'RM#': 'room',
                         'Location': 'location',
                         'Lot #': 'batch_name',
                         'Product Name': 'lineage_name',
                         'Nature of Product': 'category_name_initial',
                         '# of boxes': 'boxes',
                         'Packages / Box': 'packages_per_box',
                         'Units / Package': 'units_per_package',
                         'Total (un)': 'units',
                         'Label grams':'grams_per_unit',
                         'Total (g)':'weight_g',
                         'Total (KG)':'weight_kg',
                         'Réservé Retail | Réservé Wholesale':'is_retail',
                         'THC %':'thc'}, inplace=True)

# Add column is_rnd and is_qa
stock_df['is_rnd'] = False
stock_df['needs_qa_approval'] = False
stock_df['released_by_qa'] = False

# Add column category_name
stock_df['category_name'] = stock_df['category_name_initial']

# Set weight_g to decimal(10,2)
stock_df['weight_g'] = stock_df['weight_g'].str.replace(',', '').astype('float64')

# for column is_retail, is value is None, remove row
stock_df = stock_df[stock_df['is_retail'].notnull()]

# if is_retail is 'Retail', set value to True, else False
stock_df.loc[stock_df['is_retail'] == 'Retail', 'is_retail'] = True
stock_df.loc[stock_df['is_retail'] == 'Wholesale', 'is_retail'] = False

# In category_name, replace 'RND', 'QA', 'Defect' and '|' with ''
stock_df['category_name'] = stock_df['category_name'].str.replace('RND', '')
stock_df['category_name'] = stock_df['category_name'].str.replace('QA', '')
stock_df['category_name'] = stock_df['category_name'].str.replace('Defect', '')
stock_df['category_name'] = stock_df['category_name'].str.replace('|', '')

# Logical loop to determine if the product is rnd
# Look for the word 'RND' or 'QA' in the category_name
stock_df.loc[stock_df['category_name_initial'].str.contains('RND', case=False), 'is_rnd'] = True
stock_df.loc[stock_df['category_name_initial'].str.contains('QA', case=False), 'needs_qa_approval'] = True
stock_df.loc[stock_df['category_name_initial'].str.contains('Defect', case=False), 'is_defect'] = True

# Set released_by_qa based on needs_qa_approval
stock_df.loc[stock_df['needs_qa_approval'], 'released_by_qa'] = False
stock_df.loc[~stock_df['needs_qa_approval'], 'released_by_qa'] = True


# For column is_retail, select only when value is NaN
stock_df.loc[stock_df['is_retail'].isnull(), 'is_retail'] = None
stock_df.loc[stock_df['is_defect'].isnull(), 'is_defect'] = None

# Convert boxes, packages_per_box and units_per_package columns to integer
stock_df['boxes'] = stock_df['boxes'].astype('Int64')
stock_df['packages_per_box'] = stock_df['packages_per_box'].astype('Int64')
stock_df['units_per_package'] = stock_df['units_per_package'].astype('Int64')

# For every row, if a value is NaN, replace with None
stock_df = stock_df.replace({pd.NA: None})

# in column category_name, replace value 'Hash' with 'Haschich'
stock_df['category_name'] = stock_df['category_name'].str.replace('Hash', 'Haschich')
stock_df['category_name'] = stock_df['category_name'].str.replace('Prérouler', 'Préroulés')

# remove ' 3.5'
stock_df['category_name'] = stock_df['category_name'].str.replace(' 3.5', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 28.0', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 3.0', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 0.75', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 0.6', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 1.0', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 2.0', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 15.0', '')
stock_df['category_name'] = stock_df['category_name'].str.replace(' 0.35', '')


# Connect to the database
try:
    connection = mysql.connector.connect(host=DATABASE_HOST,
                                         database=DATABASE_NAME,
                                         user=DATABASE_ADMIN_USERNAME,
                                         password=DATABASE_ADMIN_PASSWORD)

    if connection.is_connected():
        cursor = connection.cursor(buffered=True)

        print("You're connected to the database: ")

        # for each row in the dataframe, get the lineage_id, batch_id and category_id
        for index, row in stock_df.iterrows():
            lineage_name = row['lineage_name']
            batch_name = row['batch_name']
            category_name = row['category_name']  

            # Get the lineage_id
            cursor.execute("SELECT lineage_id FROM lineages WHERE lineage_name = %s", (lineage_name,))
            lineage_record = cursor.fetchone()
            #print(index, lineage_name ,lineage_record)
            # If the lineage does not exist, insert it into the lineages table
            if lineage_record is None:
                cursor.execute("INSERT INTO lineages (lineage_name) VALUES (%s)", (lineage_name,))
                connection.commit()
                # Print lineage added
                print(f"Lineage {lineage_name} added to lineages table")
                cursor.execute("SELECT lineage_id FROM lineages WHERE lineage_name = %s", (lineage_name,))
                lineage_record = cursor.fetchone()

            lineage_id = lineage_record[0]
            stock_df.at[index, 'lineage_id'] = lineage_id


            # Get the batch_id
            cursor.execute("SELECT batch_id FROM batches WHERE batch_name = %s", (batch_name,))
            batch_record = cursor.fetchone()

            # If the batch does not exist, insert it into the batches table
            if batch_record is None:
                cursor.execute("INSERT INTO batches (batch_name, lineage_id) VALUES (%s, %s)", (batch_name, lineage_id,))
                connection.commit()
                # Print batch added
                print(f"Batch {batch_name} added to batches table")
                cursor.execute("SELECT batch_id FROM batches WHERE batch_name = %s", (batch_name,))
                batch_record = cursor.fetchone()

            batch_id = batch_record[0]
            stock_df.at[index, 'batch_id'] = batch_id

            # Get the category_id
            cursor.execute("SELECT category_id FROM categories WHERE category_name = %s", (category_name,))
            category_record = cursor.fetchone()
            # If the category does not exist
            if category_record is None:
                # print error message
                print(f"Category {category_name} does not exist in the categories table")
            else:
                category_id = category_record[0]
                stock_df.at[index, 'category_id'] = category_id

        # Insert the data into the stocks table if not already present (based on batch_id and category_id, date_stock)
        for index, row in stock_df.iterrows():
            batch_id = row['batch_id']
            category_id = row['category_id']
            date_stock = row['date_stock']

            cursor.execute("SELECT * FROM stocks WHERE batch_id = %s AND category_id = %s AND date_stock = %s", (batch_id, category_id, date_stock))
            stock_record = cursor.fetchone()
            if stock_record is None:
                cursor.execute("INSERT INTO stocks (batch_id, category_id, date_stock, boxes, packages_per_box, units_per_package, grams_per_unit, weight_g, weight_kg, is_rnd, needs_qa_approval, released_by_qa, reserved_for_retail, room, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                               (batch_id, category_id, date_stock, row['boxes'],  row['packages_per_box'], row['units_per_package'], row['grams_per_unit'], row['weight_g'] ,row['weight_kg'], row['is_rnd'], row['needs_qa_approval'], row['released_by_qa'], row['is_retail'], row['room'], row['location']))
                connection.commit()
                # Print stock added (batch_id, category_id, date_stock)
                print(f"Stock {batch_id}, {category_id}, {date_stock} added to stocks table")

            else:
                # Print error message (batch_id, category_id, date_stock)
                print(f"Stock {batch_id}, {category_id}, {date_stock} already exists in stocks table")


except Error as e:
    print("Error while connecting to MySQL", e)

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

    