from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, URL
import stripe
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretcode'
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# stripe configuration
app.config["STRIPE_PUBLIC_KEY"] = "pk_test_51OSP3yJsLunIJogOr4E931yptIqQEJgSLEMpbdgymXlrZoTjokeYPIJuDEbUYYNSFKcNaXVJhiPse6nzKTjpR1mV00OkuvAHzp"
app.config['STRIPE_SECRET_KEY'] = "sk_test_51OSP3yJsLunIJogOzzky5qw77aFjMYzb7XRWX4RBldEiakNBmiqM2FUdnbVXwQCRh6MhOYDi7hotk0LajhTZPQhi00VVcgbIzv"
stripe.api_key = app.config['STRIPE_SECRET_KEY']


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
db = SQLAlchemy()
db.init_app(app)

#books database
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    review = db.Column(db.String(1000), nullable=False)
    img_url = db.Column(db.String(250),  nullable=False)
    price = db.Column(db.Float,  nullable=False)
    price_code = db.Column(db.String(250),  nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"


# with app.app_context():
#     db.create_all()

#user database

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()

    def __repr__(self):
        return f"<Book {self.title}>"


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
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


@app.route('/', methods=["GET",'POST'])
def home():
    books = Books.query.all()
    return render_template(
        "index.html",
        books=books)


@app.route('/create-checkout-session/<int:book_id>', methods=['POST'])
def create_checkout_session(book_id):
    book = Books.query.get(book_id)
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': book.price_code,
                    'quantity': 1,
                },
            ],
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
        book = Books(title=title, author=author, review=review, img_url=img_url, price=price, stock=stock, price_code=price_code)
        db.session.add(book)
        db.session.commit()
        return redirect("/")
    return render_template("add.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        #check if the user is already in the database
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))



@app.route("/thanks")
def thanks():
    return render_template("thanks.html")

if __name__ == '__main__':
    app.run(debug=True)