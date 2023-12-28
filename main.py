from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, SelectField, BooleanField
from wtforms.validators import DataRequired, URL
import stripe


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretcode'
Bootstrap5(app)


# stripe configuration
app.config["STRIPE_PUBLIC_KEY"] = "pk_test_51OSP3yJsLunIJogOr4E931yptIqQEJgSLEMpbdgymXlrZoTjokeYPIJuDEbUYYNSFKcNaXVJhiPse6nzKTjpR1mV00OkuvAHzp"
app.config['STRIPE_SECRET_KEY'] = "sk_test_51OSP3yJsLunIJogOzzky5qw77aFjMYzb7XRWX4RBldEiakNBmiqM2FUdnbVXwQCRh6MhOYDi7hotk0LajhTZPQhi00VVcgbIzv"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
db = SQLAlchemy()
db.init_app(app)


class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    review = db.Column(db.String(1000), nullable=False)
    img_url = db.Column(db.String(250),  nullable=False)
    price = db.Column(db.Float,  nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"

# with app.app_context():
#     db.create_all()


class AddForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    review = StringField("Review", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    stock = StringField("Stock", validators=[DataRequired()])
    submit = SubmitField("Submit")


@app.route('/')
def home():
    books = Books.query.all()
    return render_template("index.html", books=books)

@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        author = form.author.data
        review = form.review.data
        img_url = form.img_url.data
        price = form.price.data
        stock = form.stock.data
        book = Books(title=title, author=author, review=review, img_url=img_url, price=price, stock=stock)
        db.session.add(book)
        db.session.commit()
        return redirect("/")
    return render_template("add.html", form=form)

@app.route("/thanks")
def thanks():
    return render_template("thanks.html")

if __name__ == '__main__':
    app.run(debug=True)