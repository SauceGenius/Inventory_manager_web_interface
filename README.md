# Inventory Manager Web Interface

This project is an inventory management web application developed as part of my final project for my bachelor's degree in computer science. The application is designed to improve the inventory tracking process for a Canadian cannabis producer, providing better visibility and control over stock data.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Future Work](#future-work)
- [Contributing](#contributing)
- [License](#license)

## Features
- User registration and authentication with admin approval.
- Stock management: Add, update, delete, and view stock items.
- Filter and sort stock items by various criteria.
- Export filtered stock data to Excel.
- Track sales and associate them with customers.
- Role-based access control to secure sensitive features.
- Comment on stock items and maintain an audit trail.

## Technologies Used
- **Frontend:** HTML, CSS, Bootstrap
- **Backend:** Flask (Python)
- **Database:** MySQL (hosted on Azure)
- **Deployment:** Docker, Azure Container Instances

## Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/SauceGenius/Inventory_manager_web_interface.git
   cd Inventory_manager_web_interface

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. **Install the required packages:**
    ```sh
    pip install -r requirements.txt

4. **Set up the environment variables:**
    Create a .env file in the root directory and add the following variables:
   ```sh
    SECRET_KEY=your_secret_key
    MYSQL_HOST=your_mysql_host
    MYSQL_PORT=3306
    MYSQL_USER=your_mysql_user
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_DB=your_mysql_db
    MYSQL_SSL_CA=/path/to/your/ssl_cert.pem

5. **Run the application:**
    ```sh
    flask run

## Usage
The application is designed to be used internally by the sales team of a cannabis producer. The sales team can:
- Register and log in to the system.
- View and filter stock data.
- Export filtered data to Excel for reporting.
- Manage sales and customer information.

## Accessing the Application
- The code source of the project is available at [GitHub Repository](https://github.com/SauceGenius/Inventory_manager_web_interface).
<<<<<<< HEAD
- The application is deployed and can be accessed at [BudTracker](http://budtracker.gch2dzghanfmdhbn.canadaeast.azurecontainer.io/).
=======
- The application is deployed and can be accessed at [Budtracker](http://budtracker.gch2dzghanfmdhbn.canadaeast.azurecontainer.io/).
>>>>>>> 8fd7086500c2a924ff488dd2d9cdd7fd28e28696

## Database Schema
The MySQL database schema includes the following tables:
- users: Stores user information and credentials.
- stocks: Stores stock information.
- batches: Stores batch information.
- categories: Stores product category information.
- lineages: Stores lineage information.
- sales: Stores sales records.
- customers: Stores customer information.

## Future Work
- Implement SSL certificates to secure the application (HTTPS).
- Develop additional use cases identified in the initial project report.
- Integrate with the ISOlocity API to fetch THC and harvest date data.
<<<<<<< HEAD
- Enhance the commenting feature to allow multiple comments per stock item.
=======
- Enhance the commenting feature to allow multiple comments per stock item.
>>>>>>> 8fd7086500c2a924ff488dd2d9cdd7fd28e28696
