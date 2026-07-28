import config
import keras
import json
from keras.preprocessing import image

class Image_clf:
    def __init__(self):
        # 1. Load the model ONCE when the app starts
        self.load_model()

    def load_model(self):
        """---Load model file----"""
        self.model = keras.models.load_model(config.MODEL_PATH)
        
        """ ---- Load model Class----"""
        with open(config.MODEL_CONFIG, 'r') as f:
            self.class_names = json.load(f)

    def preprocess_image(self, input_img): 
        """Load and preprocess image"""
        img = image.load_img(input_img, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = img_array / 255.0
        
        self.test_array = img_array.reshape(1, 224, 224, 3)
        return self.test_array

    def predict_image(self, input_img):
        """Preprocess image"""
        self.preprocessed_image = self.preprocess_image(input_img)

        """Predict image"""
        # Get the single float probability value from the sigmoid output
        self.prediction = self.model.predict(self.preprocessed_image)[0][0] 

        # Binary threshold logic for Manufacturing Defects
        # We assume 1 is 'Unit Condition is Good' (ok_front) and 0 is 'Unit Is Defective' (def_front)
        predicted_class_index = 1 if self.prediction >= 0.5 else 0
        
        # Calculate Confidence Score (0-100%)
        confidence = float(self.prediction * 100) if predicted_class_index == 1 else float((1 - self.prediction) * 100)
        
        professional_labels = {
            0: "Unit Is Defective", 
            1: "Unit Condition is Good"
        }
        self.predicted_class_name = professional_labels[predicted_class_index]
        
        # Return predicted class name and confidence score
        return self.predicted_class_name, confidence