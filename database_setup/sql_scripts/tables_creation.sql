USE inventory;

CREATE TABLE dates (
	date date NOT NULL PRIMARY KEY,
    day INT,
    month int,
    month_name VARCHAR(20),
    month_name_fr VARCHAR(20),
    year INT,
    quarter INT,
    fiscal_quarter INT,
    day_of_week INT,
    day_name VARCHAR(20),
    day_name_fr VARCHAR(20),
    week_of_year INT,
    week_starts_on DATE,
    week_ends_on DATE,
    is_weekend BOOL
);

CREATE TABLE categories (
	category_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL
);

CREATE TABLE lineages (
	lineage_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    lineage_name VARCHAR(255) NOT NULL
);

CREATE TABLE batches (
	batch_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
	batch_name VARCHAR(255) NOT NULL,
    lineage_id INT NOT NULL,
    weight_harvest_kg DECIMAL(10,3),
    thc DECIMAL(10,2),
    cbd DECIMAL(10,2),
	cbg DECIMAL(10,2),
    is_hand_trimed BOOLEAN DEFAULT TRUE,
    date_harvest DATE,
    FOREIGN KEY (lineage_id) REFERENCES lineages (lineage_id),
    FOREIGN KEY (date_harvest) REFERENCES dates (date)
);

CREATE TABLE stocks (
	stock_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    batch_id INT NOT NULL,
    category_id INT NOT NULL,
    date_stock DATE,
	boxes INT,
	packages_per_box INT,
	units_per_package INT,
	grams_per_unit DECIMAL(10,2),
	weight_g DECIMAL(10,2),
	weight_kg DECIMAL(10,3),
	thc DECIMAL(10,4),
	is_rnd BOOL,
	needs_qa_approval BOOL,
	released_by_qa BOOL,
	reserved_for_retail BOOL,
	is_sold BOOL DEFAULT FALSE,
	sold_to VARCHAR(255),
	price_target_g DECIMAL(10,2),
	price_target_kg DECIMAL(10,2),
	price_target_total DECIMAL(10,2),
	room INT,
	location VARCHAR(255),
	comment TEXT,
    FOREIGN KEY (batch_id) REFERENCES batches (batch_id),
    FOREIGN KEY (category_id) REFERENCES categories (category_id),
    FOREIGN KEY (date_stock) REFERENCES dates (date)
);

CREATE TABLE users (
	id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
	username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email_address VARCHAR(255),
    is_approved BOOLEAN DEFAULT FALSE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE customers (
	customer_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL
);

CREATE TABLE sales (
	sale_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    stock_id INT NOT NULL,
    customer_id INT NOT NULL,
    weight_g DECIMAL(10,3),
    price_per_gram DECIMAL(10,2),
    sale_total DECIMAL(10,2),
    date_sale DATE,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (date_sale) REFERENCES dates (date)
);