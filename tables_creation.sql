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
    weight_harvest_kg DECIMAL(10,3) NOT NULL,
    thc DECIMAL(10,2),
    cbd DECIMAL(10,2),
	cbg DECIMAL(10,2),
    date_harvest DATE,
    FOREIGN KEY (lineage_id) REFERENCES lineages (lineage_id),
    FOREIGN KEY (date_harvest) REFERENCES dates (date)
);

CREATE TABLE stocks (
	stock_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    batch_id INT NOT NULL,
    category_id INT NOT NULL,
    date_stock DATE,
	boxes int,
	packages_per_box int,
	units_per_package int,
	grams_per_unit decimal(10,2),
	weight_g decimal(10,2),
	weight_kg decimal(10,3),
	thc decimal(10,4),
	is_rnd bool,
	needs_qa_approval bool,
	released_by_qa bool,
	reserved_for_retail bool,
	is_sold bool,
	sold_to varchar(255),
	price_target_g decimal(10,2),
	price_target_kg decimal(10,2),
	price_target_total decimal(10,2),
	room int,
	location varchar(255),
	comments varchar(255),
    FOREIGN KEY (batch_id) REFERENCES batches (batch_id),
    FOREIGN KEY (category_id) REFERENCES categories (category_id),
    FOREIGN KEY (date_stock) REFERENCES dates (date)
)