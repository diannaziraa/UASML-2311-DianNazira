from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import asyncio

from ml_service import InsectClassifier
from gemini_service import GeminiExpert

import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================================================
# LOAD ENVIRONMENT
# ==================================================

load_dotenv()

# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="Smart Insect Identifier API",
    version="1.0.0"
)

# ==================================================
# ROOT REDIRECT
# ==================================================

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# MODEL PATH
# ==================================================

basedir = os.path.dirname(__file__)

keras_model_path = os.path.join(
    basedir,
    "artifacts",
    "best_model.keras"
)

torch_model_path = os.path.join(
    basedir,
    "artifacts",
    "model_torchscript.pt"
)

if os.path.exists(keras_model_path):
    model_path = keras_model_path

elif os.path.exists(torch_model_path):
    model_path = torch_model_path

else:
    raise FileNotFoundError(
        "Model tidak ditemukan di folder artifacts"
    )

# ==================================================
# SERVICES
# ==================================================

classifier = InsectClassifier(
    model_path=model_path
)

gemini_api_key = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

gemini_expert = GeminiExpert(
    api_key=gemini_api_key
)

# ==================================================
# DISPLAY NAME MAPPING
# ==================================================

DISPLAY_NAMES = {
    "armyworm": "Armyworm",
    "fall armyworm": "Fall Armyworm",
    "black cutworm": "Black Cutworm",
    "yellow cutworm": "Yellow Cutworm",
    "large cutworm": "Large Cutworm",
    "beetle": "Beetle",
    "ladybug": "Ladybug",
    "grasshopper": "Grasshopper",
    "dragonfly": "Dragonfly",
    "mosquito": "Mosquito",
    "butterfly": "Butterfly",
    "moth": "Moth",
    "bee": "Bee",
    "wasp": "Wasp",
    "spider": "Spider",
    "fly": "Fly",

    # label dataset yang kadang membingungkan
    "chayon": "Unknown Agricultural Insect",
    "kolorado": "Colorado Beetle",
    "lawana imitata Melichar": "Lawana Imitata",
    "potosiabre vitarsis": "Potosia Brevitarsis",
    "lycorma delicatula": "Spotted Lanternfly",
}

# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_file": os.path.basename(model_path),
        "model_type": classifier.model_type,
        "image_size": classifier.img_size,
        "num_classes": len(classifier.class_names),
        "gemini_enabled": bool(gemini_api_key)
    }

# ==================================================
# ANALYZE IMAGE
# ==================================================

@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...)
):
    """
    Endpoint untuk menganalisis gambar serangga.
    Melakukan inference model ML + AI insights dari Gemini.
    """
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail="File harus berupa gambar (jpg, png, etc)"
        )

    try:
        # Step 1: Read image
        logger.info(f"Processing image: {file.filename}")
        image_bytes = await file.read()

        if not image_bytes:
            raise ValueError("Image file is empty")

        # Step 2: Model inference
        try:
            predictions = classifier.predict(
                image_bytes=image_bytes,
                top_k=3
            )
        except Exception as ml_error:
            logger.error(f"Model inference failed: {ml_error}")
            raise HTTPException(
                status_code=500,
                detail="Model inference gagal"
            )

        top_prediction = (
            predictions[0]["class"]
            if predictions
            else "unknown"
        )

        # Display name yang lebih ramah
        display_name = DISPLAY_NAMES.get(
            top_prediction,
            top_prediction
        )

        logger.info(f"Top prediction: {top_prediction} ({display_name})")

        # Step 3: Gemini AI Insights dengan timeout
        ai_insight = "Gemini AI insights tidak tersedia"

        try:
            # Set timeout untuk Gemini request (30 detik)
            loop = asyncio.get_event_loop()
            ai_insight = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    gemini_expert.get_insect_info,
                    display_name
                ),
                timeout=30.0
            )
            logger.info("Gemini response received successfully")

        except asyncio.TimeoutError:
            logger.warning("Gemini request timeout")
            ai_insight = f"""
# 🐞 Hasil Identifikasi

**{display_name}**

✅ Serangga berhasil diidentifikasi.

⏱️ Informasi detail dari AI sedang diproses. Silakan coba lagi beberapa saat.
"""

        except Exception as gemini_error:
            error_msg = str(gemini_error)
            logger.warning(f"Gemini error: {type(gemini_error).__name__}: {error_msg}")

            # Check if error is 503 Service Unavailable
            if "503" in error_msg or "ServiceUnavailable" in str(type(gemini_error)):
                logger.warning("Gemini service unavailable (503)")
                ai_insight = f"""
# 🐞 Hasil Identifikasi

**{display_name}**

✅ Serangga berhasil diidentifikasi sebagai **{display_name}**.

⚠️ Layanan Gemini AI sedang sibuk. Informasi detail akan ditampilkan saat layanan normal kembali.

Coba lagi dalam beberapa saat.
"""
            else:
                # Generic error message
                ai_insight = f"""
# 🐞 Hasil Identifikasi

**{display_name}**

✅ Serangga berhasil diidentifikasi.

⚠️ Gagal mengambil informasi detail dari AI. Hasil prediksi model tetap akurat.
"""

        # Step 4: Return response
        return {
            "success": True,
            "top_prediction": top_prediction,
            "display_name": display_name,
            "predictions": predictions,
            "ai_insight": ai_insight,
            "model_info": {
                "model_type": classifier.model_type,
                "image_size": classifier.img_size,
                "num_classes": len(classifier.class_names)
            },
            "gemini_enabled": bool(gemini_api_key)
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error in analyze_image: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan saat memproses gambar"
        )

# ==================================================
# RUN SERVER
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )