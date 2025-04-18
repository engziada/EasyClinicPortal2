# ML Model Directory

This directory contains the ML model files for the Easy Clinic Portal.

## Model Files

- `SkinD_model_V1.keras`: Skin disease classification model (EfficientNetB3-based)

## Model Details

- **Architecture**: EfficientNetB3-based neural network
- **Input Size**: 300x300 pixels
- **Output Classes**: Melanoma, Acne, Eczema
- **File Format**: Keras (.keras)
- **File Size**: 148MB

## Usage

The model is used by the Easy Clinic Portal to analyze patient-uploaded images and provide diagnostic suggestions to doctors. The model is loaded by the `app/utils/ml_model.py` module.

## Model Loading

The model is loaded using TensorFlow's `tf.keras.models.load_model()` function. If the model file is missing or corrupted, the system will display an error message to the user.

## Sample Images

Sample images for testing the model can be found in the `/sampleimages` directory.

## Requirements

The following dependencies are required to use the model:

- TensorFlow 2.19.0
- Keras 3.9.2
- NumPy 2.1.3
- Pillow 10.0.0
