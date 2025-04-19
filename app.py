from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
import requests
import bcrypt

app = Flask(__name__)

# Secret key for JWT
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # change in production
jwt = JWTManager(app)

# The base URL of the db-service inside Docker
DB_SERVICE_URL = "http://db-service:5003"

# ------------------ HEALTH CHECK ------------------

@app.route('/auth/health', methods=['GET'])
def health_check():
    return "Authentication Service is running", 200

# ------------------ REGISTER ------------------

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "customer")  # default to customer

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Hash the password using bcrypt
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Forward the request to db-service to create the user
    response = requests.post(f"{DB_SERVICE_URL}/users", json={
        "email": email,
        "password": hashed_pw,
        "role": role
    })

    if response.status_code == 201:
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Failed to register user"}), 400

# ------------------ LOGIN ------------------

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Fetch user data from db-service
    response = requests.get(f"{DB_SERVICE_URL}/users/email/{email}")

    if response.status_code != 200:
        return jsonify({"error": "Invalid email or password"}), 401

    user = response.json()
    hashed_pw = user["password"]

    # Check password using bcrypt
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create JWT token
    access_token = create_access_token(
        identity=str(user["id"]),  # required: string
        additional_claims={
            "email": user["email"],
            "role": user["role"]
        }
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 200

# ------------------ LOGOUT ------------------

@app.route('/auth/logout', methods=['DELETE'])
def logout():
    return "JWT token cleared", 200

# ------------------ MAIN ------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
