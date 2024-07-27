# Author: Christopher Forget
# Description : this file generate a date dimension table for the mysql database
# Last update: 2024-07-23

import pandas as pd
from datetime import timedelta
import mysql.connector
from mysql.connector import Error
from tqdm import tqdm

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_ADMIN_USERNAME = os.getenv('DATABASE_ADMIN_USERNAME')
DATABASE_ADMIN_PASSWORD = os.getenv('DATABASE_ADMIN_PASSWORD')

# Function to calculate fiscal quarter
def get_fiscal_quarter(date):
    month = date.month
    if month in [4, 5, 6]:
        return '1'
    elif month in [7, 8, 9]:
        return '2'
    elif month in [10, 11, 12]:
        return '3'
    else:  # months in [1, 2, 3]
        return '4'

# Function to find the Sunday (start of the week) of the given week
def get_week_start_sunday(date):
    # Calculate the number of days to subtract to reach Sunday (Sunday is 6 days before Saturday)
    # Assuming the week starts on Sunday
    days_to_sunday = date.weekday() + 1
    return date - timedelta(days=days_to_sunday)
    
# Function to find the Saturday of the given week
def get_week_end_saturday(date):
    # Calculate the number of days to add to reach Saturday (Saturday is 5 days from Monday)
    # Assuming the week starts on Sunday
    days_to_saturday = 5 - date.weekday()
    if days_to_saturday < 0:
        days_to_saturday += 7
    return date + timedelta(days=days_to_saturday)

# Generate a date dimension table
def generate_date_dimension_table(start_date, end_date):
    date_range = pd.date_range(start_date, end_date)
    date_dimension = pd.DataFrame(date_range, columns=['date'])
    date_dimension['day'] = date_dimension['date'].dt.day
    date_dimension['month'] = date_dimension['date'].dt.month
    date_dimension['month_name'] = date_dimension['date'].dt.strftime('%B') # full month name
    date_dimension['month_name_fr'] = date_dimension['date'].dt.strftime('%B').map({
        'January': 'Janvier',
        'February': 'Février',
        'March': 'Mars',
        'April': 'Avril',
        'May': 'Mai',
        'June': 'Juin',
        'July': 'Juillet',
        'August': 'Août',
        'September': 'Septembre',
        'October': 'Octobre',
        'November': 'Novembre',
        'December': 'Décembre'
    })
    date_dimension['year'] = date_dimension['date'].dt.year
    date_dimension['quarter'] = date_dimension['date'].dt.quarter
    date_dimension['fiscal_quarter'] = date_dimension['date'].apply(get_fiscal_quarter)
    date_dimension['day_of_week'] = date_dimension['date'].dt.dayofweek.map({
        0: '2',
        1: '3',
        2: '4',
        3: '5',
        4: '6',
        5: '7',
        6: '1'
    })
    date_dimension['day_of_week'] = date_dimension['day_of_week'].astype(int)
    date_dimension['day_name'] = date_dimension['date'].dt.strftime('%A') # full day name
    date_dimension['day_name_fr'] = date_dimension['date'].dt.strftime('%A').map({
        'Monday': 'Lundi',
        'Tuesday': 'Mardi',
        'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi',
        'Friday': 'Vendredi',
        'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    })
    date_dimension['week_of_year'] = date_dimension['date'].dt.strftime('%U') # week of year canadian standard (start on sunday)
    date_dimension['week_of_year'] = date_dimension['week_of_year'].astype(int) + 1
    date_dimension['week_starts_on'] = date_dimension['date'].apply(get_week_start_sunday)
    date_dimension['week_ends_on'] = date_dimension['date'].apply(get_week_end_saturday)
    date_dimension['is_weekend'] = date_dimension['day_of_week'].apply(lambda x: 1 if (x == 1 or x == 7) else 0)
    return date_dimension

# Generate date dimension table
date_dimension = generate_date_dimension_table('2015-01-01', '2030-12-31')

# save data in mysql database
try:
    connection = mysql.connector.connect(host=DATABASE_HOST,
                                         database=DATABASE_NAME,
                                         user=DATABASE_ADMIN_USERNAME,
                                         password=DATABASE_ADMIN_PASSWORD)
    if connection.is_connected():
        pbar = tqdm(total=date_dimension.shape[0], desc='Adding rows to MySQL database')
        cursor = connection.cursor()
        for _, row in date_dimension.iterrows():
            cursor.execute("INSERT INTO dates VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (row['date'].strftime('%Y-%m-%d'), row['day'], row['month'], row['month_name'], row['month_name_fr'], row['year'],
                row['quarter'], row['fiscal_quarter'], row['day_of_week'], row['day_name'], row['day_name_fr'],
                row['week_of_year'], row['week_starts_on'].strftime('%Y-%m-%d'), row['week_ends_on'].strftime('%Y-%m-%d'), row['is_weekend']))
            pbar.update(1)

    connection.commit()
    pbar.close()

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
