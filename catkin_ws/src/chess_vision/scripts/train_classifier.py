import os
import cv2
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

PACKAGE_ROOT = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(PACKAGE_ROOT, 'data')
MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')

os.makedirs(MODELS_DIR, exist_ok=True)

EMPTY_WHITE_DIR = os.path.join(DATA_DIR, 'empty_white')
EMPTY_BLACK_DIR = os.path.join(DATA_DIR, 'empty_black')
PIECE_DIR = os.path.join(DATA_DIR, 'piece_with_blue_paper')

def augment_image(image: np.ndarray) -> np.ndarray:
    """
    Applies random transformations in the image to imitate bad quality (lighting changes, noise)

    :param image: Original cell image (BGR).
    :return: augmented image
    """
    # Changing brightness and contrast (simulating shadows/glare)
    # Alpha - contrast
    alpha = 1.0 + np.random.uniform(-0.15, 0.15)
    # Beta - brightness
    beta = np.random.uniform(-10, 10)

    # image * alpha + beta
    augmented_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    # Adding noise
    row, col, ch = augmented_image.shape
    mean = 0
    sigma = np.random.uniform(1, 5) # Random noise intensity
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)

    noisy_image = augmented_image.astype(float) + gauss
    noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)

    return noisy_image

def extract_features(image: np.ndarray, bins=(8, 8, 8)):
    """
    Extracts the HSV color histogram as a feature from an image object.
    """
    try:
        if image is None:
            return None

        image = cv2.resize(image, (64, 64))

        # Convert color space to HSV (H-hue, S-saturation, V-value)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 3D histogram
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        print(f"Error in extract_features: {e}")
        return None

def load_and_augment_data(directory, label, num_augmentations=4): 
    """Loads original images and generates augmented versions. """
    features_list = []
    labels_list = []

    if os.path.isdir(directory):
        print(f"Augmentation from: {os.path.basename(directory)}")

        for filename in os.listdir(directory):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.join(directory, filename)
                original_image = cv2.imread(path)

                if original_image is None:
                    continue

                # Original processing
                original_features = extract_features(original_image)
                if original_features is not None:
                    features_list.append(original_features)
                    labels_list.append(label)

                # Augmented processing
                for _ in range(num_augmentations):
                    augmented_image = augment_image(original_image)
                    augmented_features = extract_features(augmented_image)
                    if augmented_features is not None:
                        features_list.append(augmented_features)
                        labels_list.append(label)

    return features_list, labels_list


def train_and_save_model():
    print("1. Loading and extracting features")

    data = [] # Featers list
    labels = [] # Marks list (0: empty, 1: occupied)

    NUM_AUGMENT = 4

    # White empty cells
    f, l = load_and_augment_data(EMPTY_WHITE_DIR, 0, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)

    # Black empty cells
    f, l = load_and_augment_data(EMPTY_BLACK_DIR, 0, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)

    # Occupied cells
    f, l = load_and_augment_data(PIECE_DIR, 1, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)


    if not data:
        print("\nTrain images not found")
        return

    data = np.array(data)
    labels = np.array(labels)

    # Train test (80% / 20%)
    (train_data, test_data, train_labels, test_labels) = train_test_split(
        data, labels, test_size=0.20, random_state=42
    )

    print("\n 2. Training the SVM classifier")
    model = SVC(kernel="linear", C=1.0, random_state=42)
    model.fit(train_data, train_labels)

    print("\n 3. Model evaluation")
    predictions = model.predict(test_data)
    accuracy = accuracy_score(test_labels, predictions)
    print(f"Accuracy on train dataset: {accuracy * 100:.2f}%\n")

    print("Classification Report")
    print("0=EMPTY, 1=WITH PIECE")

    target_names = ['EMPTY (0)', 'WITH PIECE (1)']
    print(classification_report(test_labels, predictions, target_names=target_names, zero_division=0))

    # 4. Save the model
    joblib.dump(model, MODEL_PATH)

if __name__ == '__main__':
    train_and_save_model()