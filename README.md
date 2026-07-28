# 🩺 MedDiag - Clinical AI Diagnosis Portal

This project implements a Transfer Learning model (MobileNetV2) for classifying Chest X-rays (Normal vs. Pneumonia). The model is deployed as a full-stack web application using Flask, featuring JWT authentication, a modern clinical dashboard, and automated PDF report generation. It leverages PyMongo for patient history management and is structured for production deployment on cloud platforms like Azure.

## Table of Contents
- [Features](#features)
- [Project Flow](#project-flow)
- [Local Setup](#local-setup)
- [Project Structure](#project-structure)
- [Azure Deployment Guide](#azure-deployment-guide)
- [Usage Examples (API & UI)](#usage-examples-api--ui)
- [Requirements](#requirements)

## Features
- **Medical Image Classification**: Utilizes a fine-tuned MobileNetV2 model to perform binary classification on Chest X-rays (Normal vs. Pneumonia).
- **Automated PDF Reports**: Dynamically generates downloadable clinical PDF reports for both new diagnoses and historical patient records without permanently storing heavy image files.
- **Secure Authentication**: Provides doctor/user registration and login endpoints secured via JSON Web Tokens (JWT).
- **Web API & Dashboard**: A Flask backend serves the RESTful APIs, connected to a dynamic frontend featuring chronological patient history and diagnostic suggestions.
- **Database Integration**: Interacts with MongoDB to persistently store user credentials and patient prediction histories (Name, Age, Diagnosis, Date).

## Project Flow
1. **Model Training**: MobileNetV2 is fine-tuned for feature extraction on chest X-rays. The trained model (`.keras`) is saved as an artifact.
2. **Authentication**: Users log in, receiving a JWT access token stored in `localStorage`.
3. **Inference & Reporting**: The `/predict_image` endpoint accepts an image and patient metadata, verifies the JWT, and classifies the scan. The `/generate_report` endpoint packages this into a downloadable PDF.
4. **Data Logging**: Results are permanently logged in MongoDB. Temporary images and PDFs in the `data/` folder are overwritten or cleaned up to save server storage.
5. **History Retrieval**: The dashboard fetches past predictions and can generate image-free historical PDF summaries on demand.

## Local Setup
1. **Clone and enter repository**:
    ```bash
    git clone [https://github.com/your-username/MedDiag_Portal.git](https://github.com/your-username/MedDiag_Portal.git)
    cd MedDiag_Portal
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
4. **Prepare artifacts**: Place your trained model (`MedDiag_MobileNetV2.keras`) in the `artifacts/` directory. 
5. **Environment Variables**: Configure your `.env` or export directly:
    ```bash
    export FLASK_APP=main.py
    export MONGODB_URI="mongodb://localhost:27017/meddiag_db"
    export JWT_SECRET_KEY="your_super_secret_key"
    ```
6. **Run Application**:
    ```bash
    flask run
    # OR for production-like local run: gunicorn -w 4 -b 0.0.0.0:8000 main:app
    ```

## Project Structure
```text
MedDiag_Portal/
├── .venv/                            
├── artifacts/                        
│   └── MedDiag_MobileNetV2.keras     # Fine-tuned transfer learning model
├── data/                             # Temporary storage for uploads and generated PDFs
├── src/
│   └── utils.py                      # Preprocessing and thresholding logic (sigmoid)
├── static/
│   └── style.css                     
├── templates/
│   ├── login.html                    
│   └── dashboard.html                # Clinical interface with PDF download triggers
├── config.py                         
├── main.py                           # Flask app, APIs, and PDF generation routes (fpdf)
└── requirements.txt

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