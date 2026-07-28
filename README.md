# ⚙️ Automated Manufacturing Defect Detection System

This project implements a custom Convolutional Neural Network (CNN) for detecting manufacturing defects in casting products (Good vs. Defective). The model is deployed as a full-stack web application using Flask, featuring JWT authentication, a modern Quality Control (QC) dashboard, live factory analytics, and automated PDF report generation. It leverages PyMongo for inspection history management and is structured for production deployment on cloud platforms like Azure.

## Table of Contents
- [Features](#features)
- [Project Flow](#project-flow)
- [Local Setup](#local-setup)
- [Project Structure](#project-structure)
- [Azure Deployment Guide](#azure-deployment-guide)

## Features
- **Quality Inspection AI**: Utilizes a custom CNN model to perform binary classification on industrial casting product images (Good Product vs. Defective Product).
- **QC Dashboard & Analytics**: A Flask backend serves the RESTful APIs, connected to a dynamic frontend featuring chronological inspection history, live defect rate analytics, and automated system routing actions (Pass/Reject).
- **Automated PDF Reports**: Dynamically generates downloadable QC inspection PDF reports for both new scans and historical batch records without permanently storing heavy image files.
- **Secure Authentication**: Provides factory operator registration and login endpoints secured via JSON Web Tokens (JWT).
- **Database Integration**: Interacts with MongoDB to persistently store user credentials and inspection records (Operator Name, Product Batch ID, Prediction, Confidence, Date).

## Project Flow
1. **Model Training**: A CNN architecture is trained from scratch on casting product images with data augmentation. The trained model (`.keras`) and class index mapping (`.json`) are saved as artifacts.
2. **Authentication**: Operators log in, receiving a JWT access token stored in `localStorage`.
3. **Inference & Reporting**: The `/predict_image` endpoint accepts an image and product metadata, verifies the JWT, and classifies the unit. The `/generate_report` endpoint packages this into a downloadable PDF.
4. **Analytics & Logging**: Results are permanently logged in MongoDB. The `/analytics` endpoint provides real-time metrics for total inspected, good, defective, and overall defect rate. Temporary images in the `data/` folder are cleaned up to save server storage.
5. **History Retrieval**: The dashboard fetches past inspections and can generate image-free historical PDF summaries on demand.

## Local Setup
1. **Clone and enter repository**:
    ```bash
    git clone [https://github.com/your-username/Manufacturing_Defect_Detection.git](https://github.com/your-username/Manufacturing_Defect_Detection.git)
    cd Manufacturing_Defect_Detection
    ```
2. **Create and activate virtual environment**:
    ```bash
    python -m venv .venv
    # Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
    ```
3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4. **Prepare artifacts**: Place your trained model (`Manufacturing_Defect_Detection.keras`) and mapping file (`Detection_Class_names.json`) in the `artifacts/` directory. 
5. **Environment Variables**: Configure your `.env` or `config.py` directly:
    ```bash
    export FLASK_APP=main.py
    export MONGODB_URI="mongodb://localhost:27017/image_clf"
    export JWT_SECRET_KEY="your_super_secret_key"
    ```
6. **Run Application**:
    ```bash
    flask run
    # OR for production-like local run: gunicorn -w 4 -b 0.0.0.0:8000 main:app
    ```

## Project Structure
```text
Manufacturing_Defect_Detection/
├── .venv/                            
├── artifacts/                        
│   ├── Detection_Class_names.json    # JSON mapping of class indices (0: Defective, 1: Good)
│   └── Manufacturing_Defect_Detection.keras # Trained custom CNN model
├── data/                             # Temporary storage for uploads and generated QC PDFs
├── src/
│   └── utils.py                      # Preprocessing and binary thresholding logic
├── static/
│   └── style.css                     # Industrial UI styling
├── templates/
│   ├── login.html                    
│   ├── register.html                 
│   ├── forget_password.html          
│   └── dashboard.html                # Factory QC interface with analytics & PDF downloads
├── config.py                         
├── main.py                           # Flask app, APIs, Analytics, and PDF generation (fpdf)
└── requirements.txt                  # Python dependencies

Azure Deployment Guide

### 1. Set up Azure Cosmos DB (MongoDB API)
Create Cosmos DB:
-> az cosmosdb create --name <your-cosmosdb-name> --resource-group <your-rg> --kind MongoDB

Retrieve connection string (Save this for MONGODB_URI):
-> az cosmosdb keys list --name <your-cosmosdb-name> --resource-group <your-rg> --type

### 2. Set up Azure Blob Storage (For Model Artifacts)
Create Storage & Container:
-> az storage account create --name <your-storage-name> --resource-group <your-rg> --location "East US" --sku Standard_LRS
-> az storage container create --name models --account-name <your-storage-name> --public-access off

Upload model:
-> az storage blob upload --container-name models --file artifacts/MedDiag_MobileNetV2.keras --name MedDiag_MobileNetV2.keras --account-name <your-storage-name>

### 3. Deploy to Azure App Service
Create Web App:
-> az webapp create --resource-group <your-rg> --plan <your-plan> --name <your-webapp-name> --runtime "PYTHON|3.11"

Configure Settings & Startup:
-> az webapp config appsettings set --resource-group <your-rg> --name <your-webapp-name> --settings MONGODB_URI="<your-mongodb-uri>" JWT_SECRET_KEY="<secret>"
-> az webapp config set --resource-group <your-rg> --name <your-webapp-name> --startup-file "gunicorn --bind 0.0.0.0 --timeout 600 main:app"

Deploy Code:
-> az webapp deployment user set --username <git-user> --password <git-pass>
-> az webapp deployment source config-local-git --name <your-webapp-name> --resource-group <your-rg> --query scmUri --output tsv
# Add remote and git push azure master