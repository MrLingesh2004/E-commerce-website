from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Product, Cart, Wishlist, Order, OrderItem, Category
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# --- Database setup ---
with app.app_context():
    db.create_all()


# --- Routes ---
@app.route("/")
def index():
    products = Product.query.all()
    categories = Category.query.all()  # fetch categories
    return render_template("index.html", products=products, categories=categories)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    products = Product.query.all()
    return render_template("dashboard.html", products=products)


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))
    
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if username:
        user.username = username
    if email:
        user.email = email
    if password:
        user.password = generate_password_hash(password)
    
    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile"))
    
    
@app.route("/delete_account")
def delete_account():
    if "user_id" not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    if user:
        # Delete all related data if needed (orders, wishlist, addresses, etc.)
        db.session.delete(user)
        db.session.commit()
        session.clear()  # Logout user
        flash("Your account has been deleted.", "success")
    return redirect(url_for("index"))
    
    
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    file = request.files['profile_pic']
    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join('static', 'profile_pics')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))

        # Save filename to user table
        user = User.query.get(session['user_id'])
        user.profile_pic = filename
        db.session.commit()
        flash("Profile picture updated!", "success")
    return redirect(url_for('profile'))
    

# Add address
@app.route("/add_address", methods=["POST"])
def add_address():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    addr = Address(
        user_id=user.id,
        address_line=request.form["address_line"],
        city=request.form["city"],
        state=request.form["state"],
        postal_code=request.form["postal_code"]
    )
    db.session.add(addr)
    db.session.commit()
    flash("Address added!", "success")
    return redirect(url_for("profile"))

# Delete address
@app.route("/delete_address/<int:address_id>")
def delete_address(address_id):
    addr = Address.query.get(address_id)
    if addr:
        db.session.delete(addr)
        db.session.commit()
        flash("Address deleted!", "success")
    return redirect(url_for("profile"))
    
    
# --- Cart Routes ---
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))
    items = Cart.query.filter_by(user_id=session["user_id"]).all()
    return render_template("cart.html", items=items)


@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    item = Cart.query.filter_by(user_id=session["user_id"], product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        new_item = Cart(user_id=session["user_id"], product_id=product_id, quantity=1)
        db.session.add(new_item)
    db.session.commit()
    flash("Added to cart!", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    item = Cart.query.filter_by(user_id=session["user_id"], product_id=product_id).first()
    if item:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            db.session.delete(item)
        db.session.commit()
        flash("Cart updated!", "success")
    return redirect(url_for("cart"))


# --- Wishlist Routes ---
@app.route("/wishlist")
def wishlist():
    if "user_id" not in session:
        return redirect(url_for("login"))
    items = Wishlist.query.filter_by(user_id=session["user_id"]).all()
    return render_template("wishlist.html", items=items)


@app.route("/wishlist/add/<int:product_id>")
def add_to_wishlist(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    item = Wishlist.query.filter_by(user_id=session["user_id"], product_id=product_id).first()
    if not item:
        new_item = Wishlist(user_id=session["user_id"], product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        flash("Added to wishlist!", "success")
    return redirect(url_for("wishlist"))


@app.route("/wishlist/remove/<int:product_id>")
def remove_from_wishlist(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    item = Wishlist.query.filter_by(user_id=session["user_id"], product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Removed from wishlist!", "info")
    return redirect(url_for("wishlist"))
    
    
@app.route("/category/<int:category_id>")
def category_page(category_id):
    # Get the category
    category = Category.query.get_or_404(category_id)
    # Get products in this category
    products = Product.query.filter_by(category_id=category.id).all()
    return render_template("category.html", category=category, products=products)
    
    
@app.route("/categories")
def categories_page():
    categories = Category.query.all()
    return render_template("categories.html", categories=categories)
    
    
# --- Orders ---
@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)


@app.route("/orders/cancel/<int:order_id>")
def cancel_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    order = Order.query.get_or_404(order_id)
    if order.status == "Pending":
        order.status = "Cancelled"
        db.session.commit()
        flash("Order cancelled successfully!", "success")
    return redirect(url_for("orders"))


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    items = Cart.query.filter_by(user_id=session["user_id"]).all()
    if not items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for("cart"))

    total_price = sum(item.quantity * item.product.price for item in items)
    new_order = Order(user_id=session["user_id"], total_price=total_price)
    db.session.add(new_order)
    db.session.commit()  # commit first to get order.id

    # Create OrderItems
    for item in items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product.id,
            quantity=item.quantity,
            price=item.product.price  # store price at purchase
        )
        db.session.add(order_item)

    db.session.commit()

    # Clear cart
    for item in items:
        db.session.delete(item)
    db.session.commit()

    flash("Order placed successfully!", "success")
    return redirect(url_for("orders"))


# --- CRUD for Products (Admin role not implemented, but simple CRUD) ---
@app.route("/product/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        desc = request.form["description"]

        product = Product(name=name, price=price, stock=stock, description=desc)
        db.session.add(product)
        db.session.commit()
        flash("Product added!", "success")
        return redirect(url_for("dashboard"))

    return render_template("product_form.html")


@app.route("/product/delete/<int:product_id>")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted!", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)