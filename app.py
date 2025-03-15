from flask_migrate import Migrate
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from jinja2 import ChoiceLoader, FileSystemLoader


# Initialize Flask
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure Jinja2 to search for templates in both the root directory and the 'templates' folder
app.jinja_loader = ChoiceLoader([
    FileSystemLoader('.'),        # Allows searching for index.html in the root directory
    FileSystemLoader('templates') # All other templates are searched in the 'templates' folder
])

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

ab = 10000

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bonus_amount = db.Column(db.Integer, default=10000)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationships with Feedback and Booking
    feedbacks = db.relationship('Feedback', back_populates='user')
    bookings = db.relationship('Booking', back_populates='user')
    total_bookings = db.Column(db.Integer, default=0)

# Feedback model
class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mark = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationship with User
    user = db.relationship('User', back_populates='feedbacks')

# Booking model
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)  # Unique booking ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User
    excursion_id = db.Column(db.Integer, db.ForeignKey('excursions.id'), nullable=False)  # Foreign key to Excursion
    status = db.Column(db.String(20), default="Booked")  # Default booking status
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Timestamp of booking

    # Relationships with User and Excursion
    user = db.relationship('User', back_populates='bookings')  # User who made the booking
    excursion = db.relationship('Excursion', back_populates='bookings')  # The booked excursion

# Excursion model
class Excursion(db.Model):
    __tablename__ = 'excursions'
    id = db.Column(db.Integer, primary_key=True)  # Unique excursion ID
    name = db.Column(db.String(100), nullable=False)  # Excursion name
    name1 = db.Column(db.String(50), nullable=False, unique=True)  # Unique identifier (e.g., "karpatians")
    location = db.Column(db.String(100), nullable=False)  # Excursion location
    price = db.Column(db.Float, nullable=False)  # Excursion price
    start_date = db.Column(db.Date, nullable=False)  # Start date
    end_date = db.Column(db.Date, nullable=False)  # End date
    image = db.Column(db.String(200))  # Path to the excursion image
    opis = db.Column(db.Text)  # Description of the excursion

    # Relationship with Booking
    bookings = db.relationship('Booking', back_populates='excursion')  # All bookings for this excursion
    max_capacity = db.Column(db.Integer, nullable=True)

# Create all tables in the database
with app.app_context():
    db.create_all()

# Registration function
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('Register.html')

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered.', 'danger')
            return render_template('Register.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

def send_notification(user_email, subject, body):
    """Example usage of Flask-Mail for sending an email notification."""

    msg = Message(subject, recipients=[user_email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/feedback', methods=['POST'])
def feedback():
    """Handle feedback submission from users."""
    
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not authorized'}), 403

    # Retrieve JSON request data
    data = request.get_json()

    # Validate that all required fields are present
    required_fields = ['name', 'email', 'mark', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required!'}), 400

    try:
        # Create a new feedback record
        new_feedback = Feedback(
            user_id=session['user_id'],
            name=data['name'],
            email=data['email'],
            mark=data['mark'],
            message=data['message']
        )
        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({'success': 'Your feedback has been successfully saved!'}), 201
    except Exception as e:
        return jsonify({'error': 'An error occurred while saving feedback', 'details': str(e)}), 500

    
@app.route('/feedback_history', methods=['GET'])
def feedback_history():
    """Retrieve all feedback entries sorted by date (latest first)."""
    
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('feedback_history.html', feedbacks=feedbacks)

@app.route('/my_feedbacks', methods=['GET'])
def my_feedbacks():
    """Retrieve feedback submitted by the currently logged-in user."""
    
    if 'user_id' not in session:
        flash('Please log in to your account.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    feedbacks = Feedback.query.filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).all()
    
    return render_template('feedbacks.html', feedbacks=feedbacks)


@app.route('/book_trip', methods=['GET', 'POST'])
def book_trip():
    """Handle trip booking for logged-in users."""
    
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('Please log in to your account to book a trip.', 'warning')
        return redirect(url_for('login'))  # Redirect to login page
    
    # If the user is logged in, confirm booking
    flash('The trip has been successfully booked!', 'success')
    return redirect(url_for('dashboard'))  # Redirect to user dashboard

@app.route('/excursion/<name>')
def excursion(name):
    """Render the excursion details page based on the provided name."""
    
    try:
        return render_template(f'{name}.html')
    except:
        return render_template('404.html'), 404  # Return a 404 error page if the excursion is not found

@app.route('/excursions')
def all_excursions():
    """Retrieve and display all available excursions."""
    
    excursions = [
        {
            "image": "/static/images/Karpatians.jpg",
            "name": "Carpathian Tour",
            "name1": "karpatians",
            "location": "Carpathians",
            "price": 3000,
            "start_date": "2024-01-10",
            "end_date": "2024-01-15",
            "opis": "Explore the charm of the Carpathian Mountains! Unique landscapes, fresh air, and hospitality await you."
        },
        {
            "image": "/static/images/Lviv.jpg",
            "name": "Lviv Adventures",
            "name1": "Lviv",
            "location": "Lviv",
            "price": 2500,
            "start_date": "2024-02-01",
            "end_date": "2024-02-03",
            "opis": "Immerse yourself in the magical atmosphere of historic Lviv, its architecture, and delicious cuisine!"
        },
        {
            "image": "/static/images/kiev.jpg",
            "name": "Kyiv Tour",
            "name1": "Kiev",
            "location": "Kyiv",
            "price": 2000,
            "start_date": "2024-03-15",
            "end_date": "2024-03-17",
            "opis": "Explore the capital of Ukraine: Kyiv. Discover its rich history and vibrant modern life."
        },
        {
            "image": "/static/images/Odesa.jpg",
            "name": "Odesa - The Pearl of the Sea",
            "name1": "Odesa",
            "location": "Odesa",
            "price": 3500,
            "start_date": "2024-06-24",
            "end_date": "2024-07-24",
            "opis": "Experience the unique atmosphere of Odesa with its seaside charm, architecture, and gastronomy!"
        },
        {
            "image": "/static/images/Chornobil.jpg",
            "name": "Chernobyl Tour",
            "name1": "Chornobil",
            "location": "Prypiat",
            "price": 4000,
            "start_date": "2024-02-23",
            "end_date": "2024-03-03",
            "opis": "Dive into the history of the Chernobyl exclusion zone and learn more about the consequences of the disaster!"
        },
        {
            "image": "/static/images/vinnitsa.jpg",
            "name": "Vinnytsia Fountain",
            "name1": "Vinnitsa",
            "location": "Vinnytsia",
            "price": 1800,
            "start_date": "2024-08-15",
            "end_date": "2024-09-17",
            "opis": "Visit the Roshen musical fountain, one of the largest in Europe, bringing magic and excitement."
        },
        {
            "image": "/static/images/Буковель.jpg",
            "name": "Winter Fun in Bukovel",
            "name1": "bukovel",
            "location": "Bukovel",
            "price": 7000,
            "start_date": "2024-09-10",
            "end_date": "2024-09-25",
            "opis": "Discover Ukraine’s best winter resort – Bukovel! Skiing, snowboarding, and unforgettable emotions await you."
        },
        {
            "image": "/static/images/Kamin.jpg",
            "name": "Kamianets-Podilskyi",
            "name1": "KaminPod",
            "location": "Kamianets-Podilskyi",
            "price": 3000,
            "start_date": "2024-10-01",
            "end_date": "2024-11-03",
            "opis": "Visit Kamianets-Podilskyi – an ancient fortress city with rich history and picturesque landscapes."
        },
        {
            "image": "/static/images/Poltava.jpg",
            "name": "Poltava Adventures",
            "name1": "poltava",
            "location": "Poltava",
            "price": 2500,
            "start_date": "2024-11-15",
            "end_date": "2024-12-17",
            "opis": "Poltava is the heart of history and culture! Visit places that preserve the richness of Ukrainian heritage."
        }
    ]

    return render_template('all_excursions.html', excursions=excursions)

@app.route('/excursions/<name>')
def excursion_detail(name):
    """Retrieve and display details for a specific excursion."""

    excursions = [
        {
            "image": "/static/images/Karpatians.jpg",
            "name": "Carpathian Tour",
            "name1": "karpatians",
            "location": "Carpathians",
            "price": 3000,
            "start_date": "2024-01-10",
            "end_date": "2024-01-15",
            "opis": "Explore the charm of the Carpathian Mountains! Unique landscapes, fresh air, and hospitality await you."
        },
        {
            "image": "/static/images/Lviv.jpg",
            "name": "Lviv Adventures",
            "name1": "Lviv",
            "location": "Lviv",
            "price": 2500,
            "start_date": "2024-02-01",
            "end_date": "2024-02-03",
            "opis": "Immerse yourself in the magical atmosphere of historic Lviv, its architecture, and delicious cuisine!"
        },
        {
            "image": "/static/images/kiev.jpg",
            "name": "Kyiv Tour",
            "name1": "Kiev",
            "location": "Kyiv",
            "price": 2000,
            "start_date": "2024-03-15",
            "end_date": "2024-03-17",
            "opis": "Explore the capital of Ukraine: Kyiv. Discover its rich history and vibrant modern life."
        },
        {
            "image": "/static/images/Odesa.jpg",
            "name": "Odesa - The Pearl of the Sea",
            "name1": "Odesa",
            "location": "Odesa",
            "price": 3500,
            "start_date": "2024-06-24",
            "end_date": "2024-07-24",
            "opis": "Experience the unique atmosphere of Odesa with its seaside charm, architecture, and gastronomy!"
        },
        {
            "image": "/static/images/Chornobil.jpg",
            "name": "Chernobyl Tour",
            "name1": "Chornobil",
            "location": "Prypiat",
            "price": 4000,
            "start_date": "2024-02-23",
            "end_date": "2024-03-03",
            "opis": "Dive into the history of the Chernobyl exclusion zone and learn more about the consequences of the disaster!"
        },
        {
            "image": "/static/images/vinnitsa.jpg",
            "name": "Vinnytsia Fountain",
            "name1": "Vinnitsa",
            "location": "Vinnytsia",
            "price": 1800,
            "start_date": "2024-08-15",
            "end_date": "2024-09-17",
            "opis": "Visit the Roshen musical fountain, one of the largest in Europe, bringing magic and excitement."
        },
        {
            "image": "/static/images/Буковель.jpg",
            "name": "Winter Fun in Bukovel",
            "name1": "bukovel",
            "location": "Bukovel",
            "price": 7000,
            "start_date": "2024-09-10",
            "end_date": "2024-09-25",
            "opis": "Discover Ukraine’s best winter resort – Bukovel! Skiing, snowboarding, and unforgettable emotions await you."
        },
        {
            "image": "/static/images/Kamin.jpg",
            "name": "Kamianets-Podilskyi",
            "name1": "KaminPod",
            "location": "Kamianets-Podilskyi",
            "price": 3000,
            "start_date": "2024-10-01",
            "end_date": "2024-11-03",
            "opis": "Visit Kamianets-Podilskyi – an ancient fortress city with rich history and picturesque landscapes."
        },
        {
            "image": "/static/images/Poltava.jpg",
            "name": "Poltava Adventures",
            "name1": "poltava",
            "location": "Poltava",
            "price": 2500,
            "start_date": "2024-11-15",
            "end_date": "2024-12-17",
            "opis": "Poltava is the heart of history and culture! Visit places that preserve the richness of Ukrainian heritage."
        }
    ]

    # Find the requested excursion by its unique identifier (name1)
    excursion = next((exc for exc in excursions if exc["name1"] == name), None)
    
    if excursion is None:
        return render_template('404.html'), 404  # Return a 404 page if excursion is not found

    return render_template('excursion.html', excursion=excursion)  # Render the excursion details page

@app.route('/excursion/<int:excursion_id>', methods=['GET', 'POST'])
def excursion_details(excursion_id):
    """Retrieve and display details for a specific excursion."""

    excursion = Excursion.query.get_or_404(excursion_id)
    is_booked = False

    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']
        # Check if the excursion is already booked
        is_booked = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first() is not None

    if request.method == 'POST':
        # If the user is not logged in
        if 'user_id' not in session:
            flash("Please log in to book an excursion.", "danger")
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])

        # If already booked
        if is_booked:
            flash("You have already booked this excursion.", "info")
            return redirect(url_for('excursion_details', excursion_id=excursion_id))

        # Check user balance
    if user.bonus_amount < excursion.price:
        flash("Insufficient funds for booking.", "danger")
        return redirect(url_for('excursion_details', excursion_id=excursion_id))

        # Create a new booking
        booking = Booking(user_id=user.id, excursion_id=excursion.id)
        user.balance -= excursion.price
        db.session.add(booking)
        db.session.commit()

        flash(f"You have successfully booked the excursion: {excursion.name}.", "success")
        return redirect(url_for('excursion_details', excursion_id=excursion_id))

    return render_template('excursion.html', excursion=excursion, is_booked=is_booked)

# Model for logging transactions
class TransactionLog(db.Model):
    __tablename__ = 'transaction_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route('/book/<int:excursion_id>', methods=['POST'])
def book_excursion(excursion_id):
    """Handle excursion booking for logged-in users."""

    if 'user_id' not in session:
        return jsonify({"message": "Please log in to book an excursion."}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    excursion = Excursion.query.get(excursion_id)

    # Check if the excursion exists
    if not excursion:
        return jsonify({"message": "Excursion not found."}), 404

    # Check if the excursion is already booked by the user
    existing_booking = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first()
    if existing_booking:
        return jsonify({"message": "You have already booked this excursion."}), 400

    # Check for available slots
    max_capacity = excursion.max_capacity if hasattr(excursion, 'max_capacity') else None
    current_bookings = Booking.query.filter_by(excursion_id=excursion_id).count()

    if max_capacity and current_bookings >= max_capacity:
        return jsonify({"message": "No available slots for this excursion."}), 400

    # Check user's balance
    if user.bonus_amount < excursion.price:
        return jsonify({"message": "Insufficient funds for booking."}), 400

    # Create the booking
    booking = Booking(user_id=user.id, excursion_id=excursion.id, status="Booked")
    db.session.add(booking)

    # Deduct the excursion price from the user's balance
    user.bonus_amount -= excursion.price

    # Log the transaction (optional)
    transaction_log = TransactionLog(
        user_id=user.id,
        amount=excursion.price,
        description=f"Excursion booking: {excursion.name}"
    )
    db.session.add(transaction_log)

    # Update user's total bookings
    user.total_bookings = user.total_bookings + 1 if hasattr(user, 'total_bookings') else 1

    # Send a notification email to the user (optional)
    send_notification(
        user_email=user.email,
        subject="Booking Successful!",
        body=f"You have successfully booked the excursion: {excursion.name}. We look forward to seeing you!"
    )

    # Commit changes to the database
    db.session.commit()

    return jsonify({"message": f"Excursion '{excursion.name}' successfully booked!"}), 200

@app.route('/api/user/bookings', methods=['GET'])
def get_user_bookings():
    """Retrieve all bookings for the logged-in user."""

    if 'user_id' not in session:
        return jsonify({"message": "Please log in."}), 401

    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).all()
    result = []

    for booking in bookings:
        excursion = Excursion.query.get(booking.excursion_id)
        if excursion:
            result.append({
                "id": excursion.id,
                "name": excursion.name,
                "location": excursion.location,
                "price": excursion.price,
                "startDate": excursion.start_date.strftime('%Y-%m-%d'),
                "endDate": excursion.end_date.strftime('%Y-%m-%d'),
                "image": excursion.image,  # Added field for image URL
                "status": booking.status
            })

    return jsonify(result), 200


@app.route('/api/excursions', methods=['GET'])
def get_excursions():
    """Retrieve all excursions and indicate if the logged-in user has booked them."""

    excursions = Excursion.query.all()
    user_bookings = []

    if 'user_id' in session:
        user_id = session['user_id']
        user_bookings = [b.excursion_id for b in Booking.query.filter_by(user_id=user_id).all()]

    result = []
    for excursion in excursions:
        status = "Booked" if excursion.id in user_bookings else "Available"
        result.append({
            "id": excursion.id,
            "name": excursion.name,
            "location": excursion.location,
            "price": excursion.price,
            "startDate": excursion.start_date.strftime('%Y-%m-%d'),
            "endDate": excursion.end_date.strftime('%Y-%m-%d'),
            "image": excursion.image,
            "description": excursion.opis,
            "status": status
        })
    return jsonify(result)


@app.route('/api/check_booking/<int:excursion_id>', methods=['GET'])
def check_booking(excursion_id):
    """Check if the logged-in user has booked a specific excursion."""

    if 'user_id' not in session:
        return jsonify({"isBooked": False}), 401

    user_id = session['user_id']
    booking = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first()

    if booking:
        return jsonify({"isBooked": True}), 200
    else:
        return jsonify({"isBooked": False}), 200


# Login function
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login authentication."""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Verify user credentials
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect email or password.', 'danger')

    return render_template('Login.html')


# User dashboard function
@app.route('/dashboard')
def dashboard():
    """Display the user dashboard if logged in."""

    if 'user_id' not in session:
        flash('Please log in to access your account.', 'warning')
        return redirect(url_for('login'))
    
    # Fetch user details
    user = db.session.get(User, session['user_id'])

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    return render_template('Dashboard.html', user=user)

# Function for user logout
@app.route('/logout')
def logout():
    """Logs out the user by clearing the session and redirecting to login page."""
    
    session.clear()  # Clear the session
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))


# Home page route
@app.route('/')
def index():
    """Render the home page with available excursions and user bookings if logged in."""
    
    excursions = Excursion.query.all()
    user_bookings = []
    
    if 'user_id' in session:
        user_bookings = [b.excursion_id for b in Booking.query.filter_by(user_id=session['user_id']).all()]
    
    return render_template('index.html', excursions=excursions, user_bookings=user_bookings)


# Handle 404 errors (Page not found)
@app.errorhandler(404)
def page_not_found(e):
    """Render the custom 404 error page if the requested page is not found."""
    
    return render_template('404.html'), 404


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)