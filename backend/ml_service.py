import json
import io
import os
from PIL import Image
import numpy as np

try:
    import torch
    import torchvision.transforms as transforms
    from torch.nn.functional import softmax
except ImportError:
    torch = None
    transforms = None
    softmax = None

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image as keras_image
except ImportError:
    tf = None
    keras_image = None


class InsectClassifier:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.class_names = []
        self.img_size = 224
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]
        self.use_mock = False
        self.model_type = None

        if not model_path:
            self.use_mock = True
            print(
                "[InsectClassifier] Tidak ada model path yang diberikan, menggunakan mock prediction."
            )
            return

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model tidak ditemukan: {model_path}"
            )

        metadata_path = os.path.join(
            os.path.dirname(model_path),
            "model_metadata.json"
        )

        if os.path.exists(metadata_path):
            with open(
                metadata_path,
                "r",
                encoding="utf-8"
            ) as metadata_file:
                metadata = json.load(metadata_file)

            self.class_names = metadata.get(
                "class_names",
                self.class_names
            )

            self.img_size = metadata.get(
                "img_size",
                self.img_size
            )

            self.mean = metadata.get(
                "imagenet_mean",
                self.mean
            )

            self.std = metadata.get(
                "imagenet_std",
                self.std
            )

        file_ext = os.path.splitext(model_path)[1].lower()

        # =========================
        # KERAS MODEL
        # =========================
        if file_ext in {".keras", ".h5", ".hdf5"}:

            if tf is None:
                self.use_mock = True
                print(
                    "[InsectClassifier] tensorflow tidak terpasang, menggunakan mock prediction untuk model Keras."
                )
                return

            self.model = tf.keras.models.load_model(
                model_path
            )

            self.model_type = "keras"

            print("=" * 50)
            print("MODEL BERHASIL DIMUAT")
            print("Path :", self.model_path)
            print("Type :", self.model_type)
            print("Image Size :", self.img_size)
            print("Input Shape :", self.model.input_shape)
            print("Output Shape :", self.model.output_shape)
            print("Jumlah Kelas :", len(self.class_names))
            print("=" * 50)

        # =========================
        # PYTORCH MODEL
        # =========================
        elif file_ext in {".pt", ".pth"}:

            if torch is None or transforms is None:
                self.use_mock = True
                print(
                    "[InsectClassifier] torch atau torchvision tidak terpasang, menggunakan mock prediction untuk model PyTorch."
                )
                return

            self.model = torch.jit.load(
                model_path,
                map_location="cpu"
            )

            self.model.eval()

            self.model_type = "torch"

            self.transform = transforms.Compose(
                [
                    transforms.Resize(
                        (self.img_size, self.img_size)
                    ),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=self.mean,
                        std=self.std
                    ),
                ]
            )

            print("=" * 50)
            print("MODEL BERHASIL DIMUAT")
            print("Path :", self.model_path)
            print("Type :", self.model_type)
            print("Image Size :", self.img_size)
            print("Jumlah Kelas :", len(self.class_names))
            print("=" * 50)

        else:
            self.use_mock = True
            print(
                f"[InsectClassifier] Ekstensi model tidak didukung: {file_ext}. Menggunakan mock prediction."
            )
            return

    def _mock_predictions(self, top_k=3):
        fallback_labels = [
            "armyworm",
            "cutworm",
            "beetle",
            "fly",
            "grasshopper",
        ]

        return [
            {
                "class": (
                    fallback_labels[i]
                    if i < len(fallback_labels)
                    else f"class_{i}"
                ),
                "prob": float(
                    max(
                        0.05,
                        0.9 - i * 0.1
                    )
                ),
            }
            for i in range(
                min(
                    top_k,
                    len(fallback_labels)
                )
            )
        ]

    def _prepare_keras_image(
        self,
        image_bytes
    ):
        image_obj = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        image_obj = image_obj.resize(
            (self.img_size, self.img_size)
        )

        image_array = keras_image.img_to_array(
            image_obj
        )

        image_array = image_array / 255.0

        # Convert mean/std lists to numpy arrays for proper broadcasting
        mean_array = np.array(self.mean).reshape(1, 1, 3)
        std_array = np.array(self.std).reshape(1, 1, 3)
        
        image_array = (
            image_array - mean_array
        ) / std_array

        image_array = tf.expand_dims(
            image_array,
            axis=0
        )

        return image_array

    def predict(
        self,
        image_bytes,
        top_k=3
    ):
        if self.use_mock:
            return self._mock_predictions(
                top_k=top_k
            )

        # =========================
        # KERAS
        # =========================
        if self.model_type == "keras":

            image_array = self._prepare_keras_image(
                image_bytes
            )

            outputs = self.model.predict(
                image_array,
                verbose=0
            )

            outputs = outputs[0]

            # Jika model belum softmax
            if outputs.max() > 1 or outputs.min() < 0:
                probabilities = tf.nn.softmax(
                    outputs
                ).numpy()
            else:
                probabilities = outputs

            top_indices = (
                tf.argsort(
                    probabilities,
                    direction="DESCENDING"
                )[:top_k]
                .numpy()
            )

            predictions = []

            for index in top_indices:

                class_name = (
                    self.class_names[index]
                    if index < len(self.class_names)
                    else f"class_{index}"
                )

                predictions.append(
                    {
                        "class": class_name,
                        "prob": float(
                            probabilities[index]
                        ),
                    }
                )

            return predictions

        # =========================
        # PYTORCH
        # =========================
        if self.model_type == "torch":

            image_tensor = (
                self.transform(
                    Image.open(
                        io.BytesIO(image_bytes)
                    ).convert("RGB")
                )
                .unsqueeze(0)
            )

            with torch.no_grad():

                outputs = self.model(
                    image_tensor
                )

                if isinstance(
                    outputs,
                    tuple
                ):
                    outputs = outputs[0]

                probabilities = softmax(
                    outputs,
                    dim=1
                )[0]

                scores, indices = torch.topk(
                    probabilities,
                    top_k
                )

            predictions = []

            for score, index in zip(
                scores.tolist(),
                indices.tolist()
            ):

                class_name = (
                    self.class_names[index]
                    if index < len(self.class_names)
                    else f"class_{index}"
                )

                predictions.append(
                    {
                        "class": class_name,
                        "prob": float(score),
                    }
                )

            return predictions

        return self._mock_predictions(
            top_k=top_k
        )