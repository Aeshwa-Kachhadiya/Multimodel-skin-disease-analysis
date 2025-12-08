import numpy as np
from PIL import Image
import io
from typing import Dict, Tuple

disease_mapping = {
    "akiec": "Actinic Keratosis (Pre-cancerous)",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic Nevus (Mole)",
    "vasc": "Vascular Lesion"
}

def extract_image_features(image_bytes: bytes) -> Dict:
    """Extract color and texture features from image for disease detection."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_array = np.array(img)
        
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        
        avg_r = np.mean(r)
        avg_g = np.mean(g)
        avg_b = np.mean(b)
        
        std_r = np.std(r)
        std_g = np.std(g)
        std_b = np.std(b)
        
        has_red = avg_r > avg_g and avg_r > avg_b
        has_brown = avg_r > avg_g and avg_g > avg_b
        has_purple = avg_r > avg_b and avg_b > avg_g
        
        variance = np.var(img_array)
        
        return {
            "avg_r": avg_r, "avg_g": avg_g, "avg_b": avg_b,
            "std_r": std_r, "std_g": std_g, "std_b": std_b,
            "has_red": has_red, "has_brown": has_brown, "has_purple": has_purple,
            "variance": variance
        }
    except Exception as e:
        return {}

def predict_disease_from_image(image_bytes: bytes) -> Dict:
    """Predict skin disease from image using feature analysis."""
    features = extract_image_features(image_bytes)
    
    if not features:
        return {
            "condition": "unknown",
            "name": "Unable to process image",
            "confidence": 0.0
        }
    
    scores = {disease: 0.0 for disease in disease_mapping.keys()}
    
    if features.get("has_red") and features.get("avg_r") > 150:
        scores["vasc"] += 0.3
        scores["bcc"] += 0.2
    
    if features.get("has_brown"):
        scores["nv"] += 0.25
        scores["bkl"] += 0.25
        scores["mel"] += 0.15
    
    if features.get("has_purple"):
        scores["mel"] += 0.3
        scores["vasc"] += 0.2
    
    if features.get("variance", 0) > 3000:
        scores["mel"] += 0.2
        scores["bcc"] += 0.15
    
    if features.get("std_r", 0) > 50:
        scores["akiec"] += 0.2
        scores["bcc"] += 0.15
    
    best_match = max(scores, key=scores.get)
    confidence = max(0.0, min(1.0, scores[best_match] + 0.4))
    
    return {
        "condition": best_match,
        "name": disease_mapping.get(best_match, "Unknown"),
        "confidence": confidence,
        "all_scores": scores
    }

def get_image_based_analysis(image_bytes: bytes) -> Tuple[str, float, str]:
    """Get image-based disease prediction."""
    result = predict_disease_from_image(image_bytes)
    condition = result.get("condition", "unknown")
    confidence = result.get("confidence", 0.0)
    name = result.get("name", "Unknown")
    return condition, confidence, name
