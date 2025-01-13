# Import necessary modules and libraries
from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pyngrok import ngrok

# Set up Ngrok for public URL
ngrok.set_auth_token("Paste Toekn Here")
public_url = ngrok.connect(5000)
print("Ngrok URL:", public_url)

# Initialize the Flask application
app = Flask(__name__, template_folder="Flask_Syncverse/templates", static_folder="Flask_Syncverse/static")
app.secret_key = 'your_secret_key'  # Set a secret key for session management and flash messages

# Temporary "database" replacement (in-memory dictionary)
users = {}  # Example: {'email@example.com': {'name': 'John', 'password': 'hashed_password'}}

# Route for the home page, redirects to login by default
@app.route('/')
def index():
    return redirect(url_for('auth', action='login'))

# Route for authentication (login and signup)
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    action = request.args.get('action', 'login')  # Determine if login or signup

    if request.method == 'POST':
        # Get form data for email and password
        email = request.form.get('email')
        password = request.form.get('password')

        # Login process
        if action == 'login':
            user = users.get(email)
            if user and check_password_hash(user['password'], password):
                session['user'] = {'email': email, 'name': user['name']}  # Store user details in session
                flash("Login successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials, please try again.")

        # Signup process
        elif action == 'signup':
            name = request.form.get('name')
            if email in users:
                flash("Email already registered. Please log in.")
                return redirect(url_for('auth', action='login'))

            # Hash the password and store the user in the dictionary
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            users[email] = {'name': name, 'password': hashed_password}
            flash("User registered successfully!")
            return redirect(url_for('auth', action='login'))

    # Render the authentication page with login or signup action
    return render_template('auth.html', action=action)



# Route for the dashboard, accessible only if logged in
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Check login status
    if 'user' in session:
        user = session['user']

        # Handle POST request for downloading models
        if request.method == 'POST' and request.form.get('form_id') == 'download_form':
            import os
            import torch
            import time
            from google.colab import drive
            from IPython.display import clear_output

            # Check if GPU is available
            print('Checking for GPU...')
            if not torch.cuda.is_available():
                return render_template('dashboard.html', user=user, message='No GPU in runtime. Please enable GPU.')

            # Check if Syncverse folder already exists
            if not os.path.exists('/content/Syncverse'):
                print("Cloning Syncverse repository...")
                giturl = 'https://github.com/haroonsardar/Syncverse.git'
                !git clone {giturl}
                %cd 'Syncverse'
                !mkdir 'face_alignment' 'temp'
            else:
                print('Syncverse folder already exists.')
                %cd '/content/Syncverse'

            # Install prerequisites
            try:
                import batch_face
                print('batch_face is already installed.')
            except ImportError:
                print('Installing batch_face...')
                !pip install batch_face --quiet

            try:
                import basicsr
                if basicsr.__version__ == '1.4.2':
                    print('basicsr 1.4.2 is already installed.')
                else:
                    raise ImportError
            except ImportError:
                print('Installing basicsr 1.4.2...')
                !pip install basicsr==1.4.2 --quiet
                print('Fixing basicsr degradations.py...')
                !cp /content/Syncverse/degradations.py /usr/local/lib/python3.10/dist-packages/basicsr/data/degradations.py

            try:
                import gfpgan
                print('gfpgan is already installed.')
            except ImportError:
                print('Installing gfpgan...')
                !pip install gfpgan --quiet

            # Run additional installation script
            print("Running additional installation...")
            !python install.py

            return render_template('dashboard.html', user=user, message='Setup has been done.')

        # Render the dashboard for GET requests or when no specific POST action
        return render_template('dashboard.html', user=user)

    else:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('auth', action='login'))





# Route for the profile page, accessible only if logged in
@app.route('/profile')
def profile():
    if 'user' in session:
        user = session['user']
        return render_template('profile.html', user=user)
    else:
        flash("Please log in to access the profile.")
        return redirect(url_for('auth', action='login'))

# Route for a results page (e.g., displaying some generated content)
@app.route('/result')
def result():
    return render_template('result.html')  # Ensure this template exists

# Route for logging out the user
@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    flash("You have been logged out.")
    return redirect(url_for('auth', action='login'))

# Run the app
if __name__ == '__main__':
    app.run()
