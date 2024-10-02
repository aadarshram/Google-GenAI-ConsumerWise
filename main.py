# Import necessary libraries
import os
import re
import sys
from datetime import datetime as dt
import pymysql
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_file,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from ai import get_ocr_content, plot_nutrient_info, answer_query
from user_questions import questions
import tempfile

# Instantiate and config app
app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "super secret key"

# Database configuration
db_user = os.environ.get("CLOUD_SQL_USERNAME")
db_password = os.environ.get("CLOUD_SQL_PASSWORD")
db_name = os.environ.get("CLOUD_SQL_DATABASE_NAME")
db_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User model for database
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        # Fetch user from database
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_newest WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        conn.close()
        if not user:
            return None
        return User(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            password=user["password"],
        )


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_db_connection():
    # Establish database connection based on environment
    if os.environ.get("GAE_ENV") == "standard":
        unix_socket = "/cloudsql/{}".format(db_connection_name)
        conn = pymysql.connect(
            user=db_user,
            password=db_password,
            unix_socket=unix_socket,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )
    else:
        host = "127.0.0.1"
        conn = pymysql.connect(
            user=db_user,
            password=db_password,
            host=host,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )
    return conn


# Configuration for file uploads
upload_folder = tempfile.gettempdir() + "/uploads"
allowed_ext = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = upload_folder
app.config["TEMP_FOLDER"] = tempfile.gettempdir()


@app.route("/login", methods=["GET", "POST"])
def login():
    # Handle user login
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_newest WHERE email = %s", (email,))
            user = cursor.fetchone()
        conn.close()
        if not user or not check_password_hash(user["password"], password):
            flash("Please check your login details and try again.")
            return redirect(url_for("login"))
        user_obj = User(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            password=user["password"],
        )
        login_user(user_obj)
        session["user_id"] = user["id"]
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # Handle user logout
    logout_user()
    session.pop("user_id", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # Handle user registration
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_newest WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                flash("Email address already exists")
                conn.close()
                return redirect(url_for("register"))
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO user_newest (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password),
            )
            conn.commit()
        conn.close()
        new_user = User.get(cursor.lastrowid)
        login_user(new_user)
        session["user_id"] = new_user.id
        return redirect(url_for("question", sno=0))
    return render_template("register.html")


@app.route("/questions/<int:sno>", methods=["GET", "POST"])
def question(sno):
    # Handle user questions
    if sno >= len(questions):
        return "Question not found", 404
    question_id = questions[sno]["id"]
    if request.method == "POST":
        answer = request.form.get("answer")
        session[f"answer_{question_id}"] = answer
        if sno < len(questions) - 1:
            return redirect(url_for("question", sno=sno + 1))
        save_answers_to_db(session["user_id"])
        return redirect(url_for("home"))
    question = questions[sno]["text"]
    return render_template("question.html", question=question)


def save_answers_to_db(user_id):
    # Save user answers to database
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM user_preferences_newest WHERE user_id = %s", (user_id,)
        )
        existing_preferences = cursor.fetchone()
        food_intolerance = session.get("answer_food_intolerance")
        diet_preferred = session.get("answer_diet_preferred")
        allergies = session.get("answer_allergies")
        if existing_preferences:
            cursor.execute(
                """
                UPDATE user_preferences_newest 
                SET food_intolerance = %s, diet_preferred = %s, allergies = %s 
                WHERE user_id = %s
            """,
                (food_intolerance, diet_preferred, allergies, user_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_preferences_newest (user_id, food_intolerance, diet_preferred, allergies) 
                VALUES (%s, %s, %s, %s)
            """,
                (user_id, food_intolerance, diet_preferred, allergies),
            )
        conn.commit()
    conn.close()


@app.route("/")
def home():
    # Render home page
    return render_template("home.html", active_page="home")


@app.route("/chatbot")
def chatbot():
    # Render chatbot page
    first_message = "Hey there! I am Nutribot. I can help you analyze the nutritional information on food product labels. How can I help you today?"
    return render_template(
        "chatbot.html", first_message=first_message, active_page="chatbot"
    )


@app.route("/about_product")
def about_product():
    # Render about product page
    return render_template("about_product.html", active_page="about_product")


@app.route("/about_us")
def about_us():
    # Render about us page
    return render_template("about_us.html", active_page="about_us")


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    # Handle image analysis
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            dt_now = dt.now().strftime("%Y%m%d%H%M%S%f")
            filename = dt_now + ".jpg"
            file.save(os.path.join(upload_folder, filename))
            img_dir = upload_folder
            path = img_dir + "/" + filename
            if path:
                session["img_path"] = path
                return parse()
        flash("File type not allowed")
        return redirect(request.url)
    return render_template("analyze.html")


def parse():
    # Parse image and return results
    img_path = session.get("img_path")
    if img_path:
        ocr_content = get_ocr_content(img_path)
        nutrient_data = plot_nutrient_info(ocr_content)
        chart_filename = "uploads/nutrient_distribution.png"
        img_results = {
            "overviewText": ocr_content,
            "chartImageUrl": url_for(
                "serve_image", filename=chart_filename, _external=True
            ),
        }
        session["img_results"] = img_results
        return jsonify(img_results)


@app.route("/contact")
def contact():
    # Render contact page
    return render_template("contact.html", active_page="contact")


@app.route("/terms")
def terms():
    # Render terms page
    return render_template("terms.html", active_page="terms")


@app.route("/privacy")
def privacy():
    # Render privacy page
    return render_template("privacy.html", active_page="privacy")


@app.route("/get", methods=["POST"])
def query():
    # Handle chatbot queries
    input_text = request.form["msg"]
    img_results = session.get("img_results")
    chat_history = session.get("chat_history", [])
    if current_user.is_authenticated:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_preferences_newest WHERE user_id = %s",
                (current_user.id,),
            )
            user_preferences = cursor.fetchone()
        conn.close()
        if user_preferences:
            user_context = f"Food intolerance: {user_preferences['food_intolerance']}, Diet preferred: {user_preferences['diet_preferred']}, Allergies: {user_preferences['allergies']}"
        else:
            user_context = ""
    else:
        user_context = ""
    if img_results is None:
        response = answer_query(
            input_text,
            user_context=user_context,
            food_info="",
            chat_history=chat_history,
        )
    else:
        response = answer_query(
            input_text,
            user_context=user_context,
            food_info=img_results["overviewText"],
            chat_history=chat_history,
        )
    chat_history.append(input_text)
    chat_history.append(response)
    session["chat_history"] = chat_history
    return jsonify({"response": response})


@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    # Handle contact form submission
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]
    if not name or not email or not message:
        flash("Please fill all the fields")
        return redirect(url_for("contact"))
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email address", "danger")
        return redirect(url_for("contact"))
    flash("Your message has been sent", "success")
    return redirect(url_for("contact"))


def allowed_file(filename):
    # Check if file extension is allowed
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_ext


def process_image(img_path):
    # Process uploaded image
    output = f"Hey there! Upon reading the label you have uploaded, here's what we found. This is the processed text from the image at {img_path}"
    return output


# Create upload folder initially
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)


@app.route("/temp/<path:filename>")
def serve_image(filename):
    # Serve image files
    return send_file(
        os.path.join(app.config["TEMP_FOLDER"], filename), mimetype="image/png"
    )


if __name__ == "__main__":
    app.run(debug=True)
