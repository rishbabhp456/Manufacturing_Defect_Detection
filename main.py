import os
import base64
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppresses unneeded compiled optimization warnings
from fpdf import FPDF
from flask import send_file
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from src.utils import Image_clf
from werkzeug.utils import secure_filename
import config
import pymongo
import datetime

client = pymongo.MongoClient(config.MONGO_URL)
db = client[config.db_name]
data_collection = db[config.collection_data]
user_collection = db[config.collection_user]

obj_image_clf = Image_clf()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = 'secret'
app.config["SECRET_KEY"] = "flask-session-secret"
jwt = JWTManager(app)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/forgot_password_page')
def forgot_password_page():
    return render_template('forget_password.html')

@app.route('/dashboard_page')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    response = user_collection.find_one({"username": username},{"email": email})
    if not response:
        user_collection.insert_one({"username": username, "password": password, "email": email})
        return jsonify({"message": "Operator registered successfully!"})
    else:
        return jsonify({"message": "Operator already exists!"})

@jwt_required
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username') 
    password = data.get('password')
    response = user_collection.find_one({"username": username, "password": password})

    if response:
        access_token = create_access_token(identity=username,
                                           expires_delta= datetime.timedelta(minutes=60))
        return jsonify({"status": "success","message": "Login Successful", 
                        "access_token":access_token})
    else:
        return jsonify({"status": "failure", "message": "Invalid Credentials"})

@app.route("/forget_password", methods=["POST"])
def forget_password():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    new_password = data.get('new_password')

    response = user_collection.find_one({"username": username, "email": email})
    if response:
        user_collection.update_one({"username": username, "email": email}, {"$set": {"password": new_password}})
        return jsonify({"status": "success", "message": "Password updated successfully"})
    else:
        return jsonify({"status": "failure", "message": "Invalid username or email"})

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    if request.method == 'POST':
        return jsonify({"status": "success", "message": "Logged out successfully"})
    return redirect(url_for('login_page'))


@app.route("/predict_image", methods=["POST"])
def predict_image():
    username = request.form.get('username', 'anonymous')
    product_id = request.form.get('product_id', 'Unknown') # Replaced Patient with Product

    # Check Image file exists in request
    if 'image' not in request.files:
        return jsonify({"status": "failure", "message": "No image file provided"}), 400

    file = request.files['image']

    if file:
        try:
            os.makedirs("data", exist_ok=True)
            filename = secure_filename(file.filename)
            temp_path = os.path.join("data", filename)
            file.save(temp_path)

            """Predict Image"""
            # Using updated return values from utils.py
            predicted_class_name, confidence = obj_image_clf.predict_image(temp_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            """Save the Inspection Records"""
            prediction_record = {
                "operator_name": username,
                "product_id": product_id,
                "image_name": filename,
                "prediction": predicted_class_name,
                "confidence": confidence,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data_collection.insert_one(prediction_record)

            return jsonify({"status": "success", "predicted_class_name": predicted_class_name, "confidence": confidence})

        except Exception as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"status": "failure", "message": str(e)}), 500
    else:
        return jsonify({"status": "failure", "message": "An unexpected error occurred"}), 500
    

@app.route("/saved_data", methods=["GET"])
def saved_data():
    username = request.args.get('username')
    response = user_collection.find_one({"username": username})
    
    if response:
        user_history = list(data_collection.find({"operator_name": username}, {"_id": 0}))
        return jsonify({"status": "success", "history": user_history})
    
    return jsonify({"status": "success", "message": "No previous inspections found", "history": []})


@app.route("/analytics", methods=["GET"])
def analytics():
    username = request.args.get('username')
    
    total_inspected = data_collection.count_documents({"operator_name": username})
    total_good = data_collection.count_documents({"operator_name": username, "prediction": "Unit Condition is Good"})
    total_defective = data_collection.count_documents({"operator_name": username, "prediction": "Unit Is Defective"})
    
    defect_percentage = 0
    if total_inspected > 0:
        defect_percentage = round((total_defective / total_inspected) * 100, 2)
        
    return jsonify({
        "status": "success",
        "total_inspected": total_inspected,
        "total_good": total_good,
        "total_defective": total_defective,
        "defect_percentage": defect_percentage
    })

@app.route("/generate_report", methods=["POST"])
def generate_report():      
    data = request.json
    img_path = "temp_scan.jpg"
    
    # Save the base64 image temporarily for the PDF
    if 'image' in data and data['image'].startswith('data:image'):
        with open(img_path, "wb") as fh:
            fh.write(base64.b64decode(data['image'].split(",")[1]))

    pdf = FPDF()
    pdf.add_page()
    
    # --- Header Section ---
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 10, txt="QUALITY CONTROL INSPECTION REPORT", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Automated Manufacturing Defect Detection System", ln=True, align='C')
    pdf.ln(10)
    
    # --- Inspection Details ---
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Inspection Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 8, txt=f"Operator Name: {data.get('operator_name', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Product Batch ID: {data.get('product_id', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # --- AI Analysis ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="--- AI Analysis Results ---", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Model Prediction: {data.get('prediction', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Confidence Score: {data.get('confidence', 'N/A')}%", ln=True)
    
    # --- Automated Decision Logic ---
    prediction = data.get('prediction', '').upper()
    suggestion = "REJECT: Route to scrap or manual rework." if "DEFECTIVE" in prediction else "PASS: Approved for next assembly stage."
    pdf.multi_cell(0, 10, txt=f"System Action: {suggestion}")
    pdf.ln(10)
    
    # Attach the casting product image
    if os.path.exists(img_path):
        pdf.image(img_path, x=10, w=100)
        os.remove(img_path)
        
    report_path = "data/inspection_report.pdf"
    pdf.output(report_path)
    
    return send_file(report_path, as_attachment=True, download_name=f"{data.get('product_id')}_Report.pdf")


@app.route("/generate_history_report", methods=["POST"])
def generate_history_report():
    data = request.json
    pdf = FPDF()
    pdf.add_page()
    
    # --- Header Section ---
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 10, txt="HISTORICAL INSPECTION RECORD", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Automated Manufacturing Defect Detection System", ln=True, align='C')
    pdf.ln(10)
    
    # --- Past Inspection Details ---
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Original Inspection Date: {data.get('date', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Inspecting Operator: {data.get('operator_name', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Product Batch ID: {data.get('product_id', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # --- Past AI Analysis ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="--- Logged Analysis Results ---", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Logged Prediction: {data.get('prediction', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Logged Confidence: {data.get('confidence', 'N/A')}%", ln=True)
    
    # Professional Disclaimer
    pdf.ln(10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt="Note: This is a system-generated historical record. The original product snapshot is archived securely on the factory server and is omitted from this summary document.")
    
    report_path = "data/history_report.pdf"
    pdf.output(report_path)
    return send_file(report_path, as_attachment=True, download_name=f"{data.get('product_id')}_History.pdf")


if __name__ == "__main__":
    app.run(host= config.FLASK_HOST, port= config.FLASK_PORT, debug= True)