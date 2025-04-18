"""
ML model utilities for Easy Clinic Portal.
"""
import os
import numpy as np
from PIL import Image
import tensorflow as tf
from flask import current_app

# Define the class names for the skin disease model
# Based on model summary, the model has 3 output classes
SKIN_DISEASE_CLASSES = [
    "Melanoma",
    "Acne",
    "Eczema"
]

def load_model():
    """
    Load the ML model from the mlmodel directory.

    Returns:
        model: The loaded TensorFlow model or a dummy model if loading fails
    """
    model_path = os.path.join(current_app.root_path, '..', 'mlmodel', 'SkinD_model_V1.keras')
    try:
        current_app.logger.info(f"Attempting to load model from: {model_path}")
        current_app.logger.info(f"Absolute path: {os.path.abspath(model_path)}")

        # Check if file exists and log file size
        if not os.path.exists(model_path):
            current_app.logger.error(f"Model file not found at: {model_path}")
            return None
        else:
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
            current_app.logger.info(f"Model file found. Size: {file_size:.2f} MB")

            # Check TensorFlow version
            current_app.logger.info(f"TensorFlow version: {tf.__version__}")

            # Try to load the model
            current_app.logger.info("Loading model with tf.keras.models.load_model...")
            try:
                # First, check if TensorFlow can access the file
                with open(model_path, 'rb') as f:
                    file_start = f.read(20)  # Read first 20 bytes
                current_app.logger.info(f"Successfully opened model file. First bytes: {file_start}")

                # Try to load the model with detailed error handling
                current_app.logger.info("Calling tf.keras.models.load_model...")
                model = tf.keras.models.load_model(model_path)
                current_app.logger.info("Model loaded successfully!")
            except Exception as model_err:
                current_app.logger.error(f"Error during model loading: {str(model_err)}")
                import traceback
                current_app.logger.error(f"Model loading traceback: {traceback.format_exc()}")
                raise  # Re-raise to be caught by the outer try/except

            # Log model summary
            current_app.logger.info("Model loaded successfully")
            current_app.logger.info(f"Model type: {type(model)}")

            # Try to get model summary
            try:
                # Redirect summary to string
                import io
                import contextlib
                summary_str = io.StringIO()
                with contextlib.redirect_stdout(summary_str):
                    model.summary()
                current_app.logger.info(f"Model summary:\n{summary_str.getvalue()}")
            except Exception as summary_err:
                current_app.logger.warning(f"Could not get model summary: {str(summary_err)}")

            return model
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error loading ML model: {str(e)}")
        current_app.logger.error(traceback.format_exc())

        # Return None to indicate model loading failure
        current_app.logger.warning("Model loading failed, no fallback available")
        return None

def model_unavailable_error():
    """
    Return an error message when the model is unavailable.
    This is used instead of a dummy model to avoid misleading diagnostics.

    Returns:
        dict: Error message indicating the model is unavailable
    """
    return {
        "error": "The diagnostic model is currently unavailable. Please try again later or contact technical support.",
        "model_status": "unavailable"
    }

def preprocess_image(image_path):
    """
    Preprocess an image for the ML model.

    Args:
        image_path (str): Path to the image file

    Returns:
        numpy.ndarray: Preprocessed image ready for the model
    """
    try:
        current_app.logger.info(f"Preprocessing image: {image_path}")

        # Check if file exists
        if not os.path.exists(image_path):
            current_app.logger.error(f"Image file not found: {image_path}")
            return None

        # Load and resize the image to 300x300
        img = Image.open(image_path)
        current_app.logger.info(f"Image opened successfully. Format: {img.format}, Size: {img.size}, Mode: {img.mode}")

        # Convert to RGB if needed
        if img.mode != 'RGB':
            current_app.logger.info(f"Converting image from {img.mode} to RGB")
            img = img.convert('RGB')

        # Resize to 300x300
        img = img.resize((300, 300))
        current_app.logger.info(f"Image resized to 300x300")

        # Convert to numpy array and normalize
        img_array = np.array(img) / 255.0
        current_app.logger.info(f"Image converted to numpy array with shape: {img_array.shape}")

        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        current_app.logger.info(f"Added batch dimension. Final shape: {img_array.shape}")

        return img_array
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error preprocessing image: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return None

def predict_skin_disease(image_path):
    """
    Predict skin disease from an image using the ML model.

    Args:
        image_path (str): Path to the image file

    Returns:
        dict: Prediction results with class names and probabilities
    """
    try:
        # Get the full path to the image
        full_image_path = os.path.join(current_app.static_folder, image_path)
        current_app.logger.info(f"Processing image at: {full_image_path}")

        # Check if file exists
        if not os.path.exists(full_image_path):
            current_app.logger.error(f"Image file not found: {full_image_path}")
            return {"error": f"Image file not found: {image_path}"}

        # Load the model
        current_app.logger.info("Loading ML model...")
        model = load_model()
        if model is None:
            current_app.logger.error("Failed to load ML model")
            return model_unavailable_error()

        # Preprocess the image
        current_app.logger.info("Preprocessing image...")
        img_array = preprocess_image(full_image_path)
        if img_array is None:
            current_app.logger.error("Failed to preprocess image")
            return {"error": "Failed to preprocess image"}

        # Make prediction
        current_app.logger.info("Making prediction...")
        current_app.logger.info(f"Input image shape: {img_array.shape}")
        current_app.logger.info(f"Model type: {type(model)}")

        # Get model prediction
        predictions = model.predict(img_array)[0]
        current_app.logger.info(f"Raw predictions: {predictions}")
        current_app.logger.info(f"Prediction shape: {predictions.shape}")

        # Log prediction details for each class
        for i, class_name in enumerate(SKIN_DISEASE_CLASSES):
            if i < len(predictions):
                current_app.logger.info(f"Class {class_name}: {predictions[i] * 100:.2f}%")
            else:
                current_app.logger.warning(f"Class index {i} out of range for predictions with length {len(predictions)}")

        # Format results
        results = []
        for i, prob in enumerate(predictions):
            results.append({
                "class": SKIN_DISEASE_CLASSES[i],
                "probability": float(prob),
                "percentage": f"{float(prob) * 100:.2f}%"
            })

        # Sort by probability (highest first)
        results.sort(key=lambda x: x["probability"], reverse=True)
        current_app.logger.info(f"Top prediction: {results[0]['class']} with {results[0]['percentage']} probability")

        return {
            "top_prediction": results[0],
            "all_predictions": results
        }
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error in prediction: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return {"error": str(e)}

def resize_image_to_300x300(image_path, output_path=None):
    """
    Resize an image to 300x300 pixels.

    Args:
        image_path (str): Path to the image file
        output_path (str, optional): Path to save the resized image. If None, overwrites the original.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        current_app.logger.info(f"Resizing image to 300x300: {image_path}")

        # Check if file exists
        if not os.path.exists(image_path):
            current_app.logger.error(f"Image file not found: {image_path}")
            return False

        # Open the image
        img = Image.open(image_path)
        current_app.logger.info(f"Original image format: {img.format}, size: {img.size}, mode: {img.mode}")

        # Convert to RGB if needed
        if img.mode != 'RGB':
            current_app.logger.info(f"Converting image from {img.mode} to RGB")
            img = img.convert('RGB')

        # Resize to 300x300
        try:
            img_resized = img.resize((300, 300), Image.Resampling.LANCZOS)
        except AttributeError:
            # Fallback for older Pillow versions
            img_resized = img.resize((300, 300), Image.LANCZOS)

        current_app.logger.info(f"Image resized successfully to {img_resized.size}")

        # Save the resized image
        save_path = output_path if output_path else image_path
        img_resized.save(save_path, format='JPEG')
        current_app.logger.info(f"Resized image saved to: {save_path}")

        return True
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error resizing image: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return False
