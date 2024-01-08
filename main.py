from flask import Flask, render_template, redirect, url_for, request, flash, abort, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, URL
import stripe
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# stripe configuration
app.config[
    "STRIPE_PUBLIC_KEY"] = "pk_test_51OSP3yJsLunIJogOr4E931yptIqQEJgSLEMpbdgymXlrZoTjokeYPIJuDEbUYYNSFKcNaXVJhiPse6nzKTjpR1mV00OkuvAHzp"
app.config[
    'STRIPE_SECRET_KEY'] = "sk_test_51OSP3yJsLunIJogOzzky5qw77aFjMYzb7XRWX4RBldEiakNBmiqM2FUdnbVXwQCRh6MhOYDi7hotk0LajhTZPQhi00VVcgbIzv"
stripe.api_key = app.config['STRIPE_SECRET_KEY']

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
db = SQLAlchemy()
db.init_app(app)


# User database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    carts = db.relationship("Cart", backref='user', lazy=True)
    favorites = db.relationship("Favorite", backref='user', lazy=True)


# Books database
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    review = db.Column(db.String(1000), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Float, nullable=False)
    price_code = db.Column(db.String(250), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    carts = db.relationship("Cart", backref='book', lazy=True)
    favorites = db.relationship("Favorite", backref='book', lazy=True)


# Cart database
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


# Favorite database
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)


with app.app_context():
    db.create_all()


class AddForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    review = StringField("Review", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    price_code = StringField("Price Code", validators=[DataRequired()])
    stock = StringField("Stock", validators=[DataRequired()])
    submit = SubmitField("Submit")





# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired()])
    name = StringField("Name:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])

    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


def get_books_in_cart():
    with current_app.app_context():
        if current_user.is_authenticated:
            cart = Cart.query.filter_by(user_id=current_user.id).all()
            books_in_cart = len(cart)
            return books_in_cart
        return 0

@app.route('/', methods=["GET", 'POST'])
def home():
    books = Books.query.all()

    books_in_cart = get_books_in_cart()
    if request.method == 'POST' and current_user.is_authenticated:
        book_id_to_add = request.form.get('add_to_cart')
        if book_id_to_add:
            book = Books.query.get(int(book_id_to_add))
            if book:
                cart_item = Cart(user_id=current_user.id, book_id=book.id, quantity=1)
                db.session.add(cart_item)
                db.session.commit()
                books_in_cart = get_books_in_cart()

    return render_template("index.html", books=books, current_user=current_user, books_in_cart=books_in_cart)


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    user_cart = Cart.query.filter_by(user_id=current_user.id).all()

    line_items = []

    # Create line items for each book in the cart
    for cart_item in user_cart:
        line_items.append({
            'price': cart_item.book.price_code,
            'quantity': cart_item.quantity,
        })

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=url_for('thanks', _external=True),
            cancel_url=url_for("home", _external=True),
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        author = form.author.data
        review = form.review.data
        img_url = form.img_url.data
        price = form.price.data
        price_code = form.price_code.data
        stock = form.stock.data
        book = Books(title=title, author=author, review=review, img_url=img_url, price=price, stock=stock,
                     price_code=price_code)
        db.session.add(book)
        db.session.commit()
        return redirect("/")
    return render_template("add.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # check if the user is already in the database
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form, current_user=current_user)

def add_to_cart(book_id, user_id):
    try:
        book = Books.query.get(book_id)
        if book:
            cart_item = Cart(user_id=user_id, book_id=book.id, quantity=1)
            db.session.add(cart_item)
            db.session.commit()
            flash(f"{book.title} added to cart successfully!", "success")
        else:
            flash("Book not found.", "error")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")


# @app.route('/add-to-favorites/<int:book_id>', methods=["GET", 'POST'])
# @login_required
# def add_to_favorites(book_id):
#     book = Books.query.get(book_id)
#
#     if book:
#         current_user.favorites.append(book)
#         db.session.commit()
#
#     return redirect(url_for('home'))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            print(user)
            print(current_user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/cart', methods=["GET", "POST"])
def view_cart():
    if current_user.is_authenticated:
        if request.method == 'POST':
            user_cart = Cart.query.filter_by(user_id=current_user.id).all()

            line_items = []

            # Create line items for each book in the cart
            for cart_item in user_cart:
                line_items.append({
                    'price': cart_item.book.price_code,
                    'quantity': cart_item.quantity,
                })

            try:
                checkout_session = stripe.checkout.Session.create(
                    line_items=line_items,
                    mode='payment',
                    success_url=url_for('thanks', _external=True),
                    cancel_url=url_for("home", _external=True),
                )

                # Delete cart items after successful creation of checkout session
                for cart_item in user_cart:
                    db.session.delete(cart_item)
                db.session.commit()


            except Exception as e:
                return str(e)

            return redirect(checkout_session.url, code=303)
        else:
            books_to_buy = []
            total_price = 0
            number_of_books = 0
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            for item in cart_items:
                book = Books.query.get(item.book_id)
                if book:
                    total_price += book.price
                    number_of_books += 1
                    books_to_buy.append(book)
            return render_template('cart.html', cart=books_to_buy, total=round(total_price, 2), number_of_books=number_of_books)

    else:
        flash('Please log in to view your cart.')
        return redirect(url_for('login'))


@app.route("/delete-from-cart/<int:book_id>")
def delete_from_cart(book_id):
    # Check if the user is authenticated
    if not current_user.is_authenticated:
        abort(401)  # Unauthorized

    # Get the cart item to delete
    cart_item = Cart.query.filter_by(user_id=current_user.id, book_id=book_id).first()

    # Check if the cart item exists
    if not cart_item:
        abort(404)  # Not Found

    # Delete the cart item
    db.session.delete(cart_item)
    db.session.commit()

    return redirect("/cart")


@app.route('/delete-book/<int:book_id>')
def delete_book(book_id):
    # Check if the current user is authenticated and is an admin
    if current_user.is_authenticated and current_user.id == 1:
        book = Books.query.get(book_id)

        if book:
            # Delete the book from the database
            db.session.delete(book)
            db.session.commit()

        # Redirect to the home page or wherever you want after deletion
        return redirect(url_for('home'))
    else:
        # Redirect to home or another page if the user is not authenticated or not an admin
        return redirect(url_for('home'))


@app.route('/book/<int:book_id>', methods=["GET", "POST"])
def show_book(book_id):
    book = Books.query.get(book_id)

    books = Books.query.all()

    if request.method == 'POST' and current_user.is_authenticated:
        book_id_to_add = request.form.get('add_to_cart')
        if book_id_to_add:
            book = Books.query.get(int(book_id_to_add))
            if book:
                cart_item = Cart(user_id=current_user.id, book_id=book.id, quantity=1)
                db.session.add(cart_item)
                db.session.commit()
                return redirect('/')
    return render_template('book.html', book=book)


@app.route('/author/<book_author>')
def show_author(book_author):
    books = Books.query.filter_by(author=book_author).all()
    return render_template('author.html', books=books, book_author=book_author)


@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q')
    print(q)
    
# case-insensitive search using ilike
    if q:
        results = Books.query.filter(or_(Books.title.ilike(f"%{q}%"), Books.author.ilike(f"%{q}%"))).order_by(Books.title.asc()).all()
    else:
        results = []

    return render_template("search_results.html", results=results)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/thanks")
def thanks():
    return render_template("thanks.html")


if __name__ == '__main__':
    app.run(debug=True)
