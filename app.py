from flask import Flask

app = Flask(__name__)

@app.route('/auth/health', methods=['GET'])
def health_check():
    return "Authentication Service is running", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
    