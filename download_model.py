#!/usr/bin/env python3
"""
download_model.py  –  fixed for Keras 3.x
"""

import os
import urllib.request

HDF5_URL = (
    "https://github.com/oarriaga/face_classification/raw/master"
    "/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5"
)

MODEL_DIR  = "model"
HDF5_SRC   = os.path.join(MODEL_DIR, "emotion_model_src.hdf5")   # original download
JSON_DEST  = os.path.join(MODEL_DIR, "emotion_model.json")
W_DEST     = os.path.join(MODEL_DIR, "emotion_model.weights.h5")  # new format


def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Step 1: Download original HDF5 ──────────────────
    if not os.path.exists(HDF5_SRC):
        print("Downloading pretrained FER model (~3 MB)...")
        try:
            urllib.request.urlretrieve(HDF5_URL, HDF5_SRC)
            print("[OK] Download complete!")
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return
    else:
        print("[OK] Model already downloaded.")

    # ── Step 2: Extract JSON + weights ──────────────────
    if os.path.exists(JSON_DEST) and os.path.exists(W_DEST):
        print("[OK] Model files already extracted.")
        return

    try:
        from tensorflow.keras.models import load_model as keras_load
        print("Extracting model architecture to JSON...")
        model = keras_load(HDF5_SRC, compile=False)

        # Save architecture as JSON
        with open(JSON_DEST, "w") as f:
            f.write(model.to_json())
        print(f"[OK] Saved architecture → {JSON_DEST}")

        # Save weights in new Keras 3.x format
        model.save_weights(W_DEST)
        print(f"[OK] Saved weights      → {W_DEST}")

        print("\nAll done! You can now run: python app.py")

    except ImportError:
        print("[WARN] TensorFlow not installed yet.")


if __name__ == "__main__":
    download_model()