from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
from decimal import Decimal, InvalidOperation
from datetime import date
import pandas as pd
from io import BytesIO
from flask import send_file


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
app.config['MYSQL_HOST'] = 'Localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'tofer006007'
app.config['MYSQL_DB'] = 'inventory'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, first_name, last_name, email_address, is_admin, is_approved):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.is_admin = is_admin
        self.is_approved = is_approved

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if user:
        return User(user['id'], user['username'], user['first_name'], user['last_name'], user['email_address'], user['is_admin'], user['is_approved'])
    return None

# Custom filter to format number
def format_number(value):
    return f"{value:,.2f}".replace(",", " ")
app.jinja_env.filters['number'] = format_number

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email_address = request.form['email_address']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email_address):
            flash('Invalid email address.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, first_name, last_name, email_address, is_admin, is_approved) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (username, hashed_password, first_name, last_name, email_address, False, False))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            if user['is_approved']:
                user_obj = User(user['id'], user['username'], user['first_name'], user['last_name'], user['email_address'], user['is_admin'], user['is_approved'])
                login_user(user_obj)
                return redirect(url_for('index'))
            else:
                flash('Your account is not approved by admin yet.', 'warning')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE is_approved = FALSE")
    pending_users = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        cur = mysql.connection.cursor()
        if action == 'approve':
            cur.execute("UPDATE users SET is_approved = TRUE WHERE id = %s", (user_id,))
        elif action == 'reject':
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

        flash('Action performed successfully.', 'success')
        return redirect(url_for('admin'))

    return render_template('admin.html', pending_users=pending_users)

@app.route('/', methods=['GET'])
@login_required
def index():
    cur = mysql.connection.cursor()

    # Fetch unique batches for the filter dropdown
    cur.execute("SELECT DISTINCT batch_name FROM batches ORDER BY batch_name")
    batches = cur.fetchall()

    # Fetch unique lineages for the filter dropdown
    cur.execute("SELECT DISTINCT lineage_name FROM lineages ORDER BY lineage_name")
    lineages = cur.fetchall()

    # Fetch unique categories for the filter dropdown
    cur.execute("SELECT DISTINCT category_name FROM categories ORDER BY category_name")
    categories = cur.fetchall()

    # Fetch stocks based on the filters applied
    selected_batches = request.args.getlist('batch[]')
    selected_lineages = request.args.getlist('lineage[]')
    selected_categories = request.args.getlist('category[]')
    selected_status = request.args.get('status')

    # Sorting parameters
    sort_by = request.args.get('sort_by', 'stock_id')
    sort_order = request.args.get('sort_order', 'asc')

    # Start constructing the SQL query for stocks
    query = f"""
        SELECT s.stock_id, s.date_stock, s.weight_g, b.thc, s.is_sold, b.batch_name, l.lineage_name, b.date_harvest, c.category_name
        FROM stocks s
        JOIN batches b ON s.batch_id = b.batch_id
        JOIN categories c ON s.category_id = c.category_id
        JOIN lineages l ON b.lineage_id = l.lineage_id
        WHERE 1=1
    """

    parameters = []

    # Filter by batch (batch name)
    if selected_batches:
        placeholders = ','.join(['%s'] * len(selected_batches))
        query += f" AND b.batch_name IN ({placeholders})"
        parameters.extend(selected_batches)

    # Filter by multiple lineages
    if selected_lineages:
        placeholders = ','.join(['%s'] * len(selected_lineages))
        query += f" AND l.lineage_name IN ({placeholders})"
        parameters.extend(selected_lineages)

    # Filter by multiple categories
    if selected_categories:
        placeholders = ','.join(['%s'] * len(selected_categories))
        query += f" AND c.category_name IN ({placeholders})"
        parameters.extend(selected_categories)

    # Filter by status
    if selected_status is not None:
        query += " AND s.is_sold = %s"
        parameters.append(selected_status)

    # Add sorting
    query += f" ORDER BY {sort_by} {sort_order}"

    cur.execute(query, parameters)
    stocks = cur.fetchall()
    cur.close()

    return render_template('index.html', 
                           categories=categories, 
                           lineages=lineages, 
                           batches=batches, 
                           selected_categories=selected_categories, 
                           selected_lineages=selected_lineages, 
                           selected_batches=selected_batches, 
                           selected_status=selected_status,
                           stocks=stocks,
                           sort_by=sort_by,
                           sort_order=sort_order)

@app.route('/export', methods=['GET'])
@login_required
def export():
    cur = mysql.connection.cursor()

    # Fetch stocks based on the filters applied
    selected_batches = request.args.getlist('batch[]')
    selected_lineages = request.args.getlist('lineage[]')
    selected_categories = request.args.getlist('category[]')
    selected_status = request.args.get('status')

    # Start constructing the SQL query for stocks
    query = f"""
        SELECT s.stock_id, l.lineage_name, b.batch_name, c.category_name, s.weight_g, b.thc, s.is_sold, b.date_harvest, b.is_hand_trimed
        FROM stocks s
        JOIN batches b ON s.batch_id = b.batch_id
        JOIN categories c ON s.category_id = c.category_id
        JOIN lineages l ON b.lineage_id = l.lineage_id
        WHERE 1=1
    """

    parameters = []

    # Filter by batch (batch name)
    if selected_batches:
        placeholders = ','.join(['%s'] * len(selected_batches))
        query += f" AND b.batch_name IN ({placeholders})"
        parameters.extend(selected_batches)

    # Filter by multiple lineages
    if selected_lineages:
        placeholders = ','.join(['%s'] * len(selected_lineages))
        query += f" AND l.lineage_name IN ({placeholders})"
        parameters.extend(selected_lineages)

    # Filter by multiple categories
    if selected_categories:
        placeholders = ','.join(['%s'] * len(selected_categories))
        query += f" AND c.category_name IN ({placeholders})"
        parameters.extend(selected_categories)

    # Filter by status
    if selected_status is not None:
        query += " AND s.is_sold = %s"
        parameters.append(selected_status)

    # Add sorting
    sort_by = request.args.get('sort_by', 'stock_id')
    sort_order = request.args.get('sort_order', 'asc')
    query += f" ORDER BY {sort_by} {sort_order}"

    cur.execute(query, parameters)
    stocks = cur.fetchall()
    cur.close()

    df = pd.DataFrame(stocks)
    # Drop columns is_sold and batch_name
    df = df.drop(columns=['is_sold', 'batch_name'])
    # Rename column is_hand_trimed to hand_trimed
    df.rename(columns={'is_hand_trimed': 'hand_trimed'}, inplace=True)

    # For column hand_trimed, replace 1 with 'Yes' and 0 with 'No'
    df['hand_trimed'] = df['hand_trimed'].apply(lambda x: 'Yes' if x == 1 else 'No')

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Stocks')
    writer.close()
    output.seek(0)


    return send_file(output, download_name="on_wholesale_stocks_" + str(date.today()) + ".xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/stock/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def stock_detail(stock_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        comment = request.form.get('comment')
        cur.execute("UPDATE stocks SET comment = %s WHERE stock_id = %s", (comment, stock_id))
        mysql.connection.commit()

    cur.execute("""
        SELECT s.*, b.batch_name, l.lineage_name, c.category_name, b.date_harvest, b.thc AS batch_thc,
               sa.price_per_gram, sa.sale_total, sa.date_sale
        FROM stocks s
        JOIN batches b ON s.batch_id = b.batch_id
        JOIN categories c ON s.category_id = c.category_id
        JOIN lineages l ON b.lineage_id = l.lineage_id
        LEFT JOIN sales sa ON s.stock_id = sa.stock_id
        WHERE s.stock_id = %s
    """, (stock_id,))
    stock = cur.fetchone()
    cur.close()

    return render_template('stock_detail.html', stock=stock)

@app.route('/sale/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def sale(stock_id):
    cur = mysql.connection.cursor()
    
    # Fetch stock information for both GET and POST requests
    cur.execute("""
                SELECT s.*, b.date_harvest, b.batch_name, l.lineage_name, c.category_name, b.thc as batch_thc
                FROM stocks as s 
                JOIN batches b ON s.batch_id = b.batch_id
                JOIN lineages l ON b.lineage_id = l.lineage_id
                JOIN categories c ON s.category_id = c.category_id
                WHERE stock_id = %s
    """, (stock_id,))
    stock = cur.fetchone()

    if request.method == 'POST':
        sale_total_str = request.form.get('sale_total').replace(' ', '')
        price_per_gram_str = request.form.get('price_per_gram').replace(' ', '')
        
        try:
            sale_total = Decimal(sale_total_str)
            price_per_gram = Decimal(price_per_gram_str)
        except (InvalidOperation, ValueError):
            flash('Invalid sale total or price per gram value.', 'danger')
            return redirect(url_for('sale', stock_id=stock_id))
        
        customer_id = request.form.get('customer_id')
        new_customer_name = request.form.get('new_customer_name')

        # Handle new customer creation if necessary
        if not customer_id and new_customer_name:
            # Check if customer already exists
            cur.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (new_customer_name,))
            existing_customer = cur.fetchone()

            if existing_customer:
                customer_id = existing_customer['customer_id']
            else:
                cur.execute("INSERT INTO customers (customer_name) VALUES (%s)", (new_customer_name,))
                mysql.connection.commit()
                customer_id = cur.lastrowid
        else:
            customer_id = int(customer_id)

        # Insert sale record
        cur.execute("""
            INSERT INTO sales (stock_id, customer_id, weight_g, price_per_gram, sale_total, date_sale)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (stock_id, customer_id, stock['weight_g'], price_per_gram, sale_total, date.today()))
        
        # Update stock status
        cur.execute("UPDATE stocks SET is_sold = 1 WHERE stock_id = %s", (stock_id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    # Fetch existing customers
    cur.execute("SELECT * FROM customers ORDER BY customer_name")
    customers = cur.fetchall()

    cur.close()

    return render_template('sale.html', stock=stock, customers=customers)


@app.route('/sales')
@login_required
def sales():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT sa.sale_id, sa.stock_id, l.lineage_name, b.batch_name, c.category_name, sa.weight_g, sa.price_per_gram, sa.sale_total, cu.customer_name, sa.date_sale
        FROM sales sa
        JOIN stocks s ON sa.stock_id = s.stock_id
        JOIN batches b ON s.batch_id = b.batch_id
        JOIN lineages l ON b.lineage_id = l.lineage_id
        JOIN categories c ON s.category_id = c.category_id
        JOIN customers cu ON sa.customer_id = cu.customer_id
    """)
    sales = cur.fetchall()
    cur.close()

    # Calculate total sale_total
    total_sale_total = sum(sale['sale_total'] for sale in sales)

    return render_template('sales.html', sales=sales, total_sale_total=total_sale_total)


if __name__ == '__main__':
    app.run(debug=True)