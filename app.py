from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = str(form.password.data)

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        cur.execute("CREATE TABLE "+username+" (id INT AUTO_INCREMENT PRIMARY kEY, product VARCHAR(30),quantity VARCHAR(30),price VARCHAR(10),create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if password_candidate== password:
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard')),username
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Products
    result = cur.execute("SELECT * FROM "+session['username'])

    a = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', inventory=a)
    else:
        msg = 'No Products Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# prosuct Form Class
class ProductForm(Form):
    product = StringField('Product', [validators.Length(min=1, max=200)])
    quantity = TextAreaField('Quantity', [validators.Length(min=1)])
    price = StringField('Price Rs.', [validators.Length(min=1, max=200)])

# Add product
@app.route('/add_product', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        product = form.product.data
        quantity = form.quantity.data
        price = form.price.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO "+session['username']+" (product, quantity, price) VALUES(%s, %s, %s)",(product, quantity, price))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Product Added', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_product.html', form=form)


# Edit product
@app.route('/edit_product/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_product(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM "+session['username']+" WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ProductForm(request.form)

    form.product.data = article['product']
    form.quantity.data = article['quantity']
    form.price.data = article['price']
    if request.method == 'POST' and form.validate():
        product = request.form['product']
        quantity = request.form['quantity']
        price = request.form['price']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(product)
        # Execute
        cur.execute ("UPDATE "+session['username']+" SET product=%s, quantity=%s, price=%s WHERE id=%s",(product, quantity, price, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Product Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_product.html', form=form)

# Delete Product
@app.route('/delete_product/<string:id>', methods=['POST'])
@is_logged_in
def delete_product(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM "+session['username']+" WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Product Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
