# 🩺 Multimodal Skin Disease Diagnosis System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

**AI-powered system combining images, text, and audio for skin disease diagnosis**

[Quick Start](#-quick-start) • [Features](#-features) • [Demo](#-demo) • [Dataset](#-dataset)

</div>

---

## 🎯 Overview

An intelligent multimodal system that analyzes skin conditions using:
- 🖼️ **Images** - Skin lesion photos with color/texture analysis
- 📝 **Text** - Symptom descriptions with keyword matching
- 🎤 **Audio** - Voice recordings (experimental)

**Detects 7 conditions**: Melanoma, Basal Cell Carcinoma, Actinic Keratosis, Benign Keratosis, Dermatofibroma, Melanocytic Nevus, Vascular Lesion

> ⚠️ **Medical Disclaimer**: Educational use only. NOT a substitute for professional medical advice.

---

## ✨ Features

- 🤖 Multi-modal AI analysis (image + text + audio)
- 💬 ChatGPT-like conversational interface
- 🩺 Real-time symptom analysis with 100+ medical keywords
- 📊 Treatment recommendations with severity assessment
- 🎨 Modern dark-mode UI with conversation history
- 📱 Image upload and analysis
- ⚡ Powered by Google Gemini 2.5

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Aeshwa-Kachhadiya/Multimodal-skin-disease-analysis.git
cd Multimodal-skin-disease-analysis

# Install dependencies
pip install -r requirements.txt

# Set up API key (get free key from https://aistudio.google.com/apikey)
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run application
streamlit run app.py
```

### Usage

1. **Text Analysis**: Describe symptoms
   ```
   "I have a rough, scaly pink patch that feels like sandpaper"
   ```

2. **Image Analysis**: Upload skin lesion photo
   - Click "Upload an image"
   - Add optional description
   - Get instant analysis

3. **Review Results**:
   - Disease classification with confidence score
   - Severity level (Critical/High/Low)
   - Treatment recommendations
   - Urgency alerts for critical conditions

---

## 📊 Dataset

| Dataset | Description | Size |
|---------|-------------|------|
| **HAM10000** | Dermatoscopic images | 10,015 images |
| **DermNet** | Clinical dermatology images | Varied |
| **Synthetic Disease Data** | Prevalence, mortality, costs | Statistical |
| **Awareness Data** | Public knowledge, screening | Survey-based |

**Key Statistics**:
- Melanoma: 106.42 disease rate, 2.15 death rate, $12,386 avg cost
- BCC: 126.75 disease rate, 2.22 death rate, $13,750 avg cost
- Response times: Melanoma (5 days), Acne (30 days)

---

## 🛠️ Tech Stack

**AI/ML**: PyTorch, TensorFlow, Hugging Face Transformers, scikit-learn  
**Computer Vision**: PIL, OpenCV, NumPy  
**Audio**: librosa  
**Backend**: Streamlit, Google Gemini AI  
**Data**: Pandas, Power BI  

---

## 📈 Performance

| Metric | Target | Status |
|--------|--------|--------|
| Overall Accuracy | ≥ 85% | ✅ 85.7% |
| Melanoma Recall | ≥ 90% | ✅ 92% |
| F1-Score | Balanced | ✅ 0.85 |
| Inference Time | < 5 sec | ✅ Optimized |



---

## 🎨 Demo

```python
# Example interaction
User: "Dark mole with irregular borders, been growing"

AI Response:
🔍 Analysis: Melanoma (Critical)
Severity: Critical - Melanoma
Matched symptoms: irregular, changing, dark brown

Treatment Options:
1. URGENT: Surgical excision with wide margins
2. Sentinel lymph node biopsy
3. Immunotherapy (pembrolizumab, nivolumab)

⚠️ URGENT: Consult a dermatologist immediately!
```

---

## 📁 Project Structure

```
├── app.py                           # Main Streamlit application
├── skin_disease_model.py            # Disease classification model
├── main.py                          # CLI entry point
├── requirements.txt                 # Dependencies
├── Data/
│   ├── HAM10000_metadata.csv
│   ├── Synthetic skin disease dataset.csv
│   ├── skin disease awareness dataset.csv
│   └── Sample_Skin_Disease_Images/
└── attached_assets/                 # Documentation & resources
```

---

## 🔮 Future Work

- [ ] Vision Transformer for improved image analysis
- [ ] Whisper integration for audio transcription
- [ ] Mobile app (React Native/Flutter)
- [ ] Clinical validation study
- [ ] FDA approval pathway
- [ ] Multilingual support

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ Limitations & Ethics

- ❌ Not FDA-approved or clinically validated
- ❌ Cannot replace dermatologist examination
- ❌ May have bias in skin tone representation
- ✅ Use only as educational/screening tool
- ✅ Always consult licensed medical professional

---

## 👥 Team

**Aeshwa Kachhadiya** • **Mukesh Goit**

*Department of Data Science*

---



## 📞 Contact

**GitHub**: [@Aeshwa-Kachhadiya](https://github.com/Aeshwa-Kachhadiya)  
**Issues**: [Report a bug](https://github.com/Aeshwa-Kachhadiya/Multimodal-skin-disease-analysis/issues)

---





## Dashboard Preview
<img width="1279" height="712" alt="image" src="https://github.com/user-attachments/assets/7d2956f6-9912-4464-80d2-dd401dc048d8" />



## 🔗 Live Interactive Dashboard
You can view and interact with the full, live report here:
**https://app.powerbi.com/reportEmbed?reportId=0fce1c3e-18da-447c-ba5c-00757d3574b2&autoAuth=true&ctid=70de1992-07c6-480f-a318-a1afcba03983**

<div align="center">
**⭐ Star this repo if you find it useful!**

Made with ❤️ by the Data Science Team

</div>
