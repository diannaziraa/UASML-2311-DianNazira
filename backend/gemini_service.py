import os
import time
from typing import Optional
from google import genai
from google.api_core import exceptions

# Knowledge base untuk fallback responses
INSECT_KNOWLEDGE = {
    "armyworm": """
# 🐞 Armyworm (Serangga Tentara)

**Klasifikasi:** Lepidoptera, Noctuidae
**Ukuran:** 3-4 cm (larva), 3.5 cm (imago)
**Warna:** Hijau kecoklatan dengan garis melintang

## Karakteristik:
- Larva bernama "armyworm" karena bergerak dalam kelompok besar seperti tentara
- Menyerang berbagai tanaman pangan (padi, jagung, rumput)
- Periode larva berlangsung 2-3 minggu

## Kerusakan:
- Merusak daun dan butir tanaman
- Dapat menurunkan hasil panen hingga 50%
- Paling aktif pada malam hari

## Pengendalian:
✅ Penggunaan insektisida biologis
✅ Penyemprotan pada malam hari
✅ Pengelolaan lahan yang baik
✅ Penanaman tanaman perangkap

## Musim Serangan:
Puncak serangan terjadi pada musim basah (September-Desember)
""",
    "fall armyworm": """
# 🐞 Fall Armyworm (Serangga Tentara Musim Gugur)

**Nama ilmiah:** Spodoptera frugiperda
**Ukuran:** 1.4-1.8 cm (larva)
**Asal:** Amerika (invasif di Asia)

## Karakteristik:
- Larva bervariasi warna (hijau, merah, coklat)
- Karakteristik unik: garis putih di kepala dengan pola Y
- Generasi cepat (4-6 generasi per tahun)

## Tanaman Inang:
🌾 Jagung (tanaman utama)
🌽 Padi
🥬 Kacang
🌱 Sayuran lainnya

## Pengendalian:
✅ Monitoring rutin dengan perangkap feromon
✅ Penyemprotan Bt (Bacillus thuringiensis)
✅ Insektisida kimia untuk infestasi berat
✅ Rotasi tanaman

## Status:
Hama invasif berbahaya yang menyebar ke seluruh dunia!
""",
    "beetle": """
# 🐞 Beetle (Kumbang)

**Klasifikasi:** Ordo Coleoptera
**Ukuran:** Bervariasi (2mm-20cm)
**Jenis:** Ribuan spesies

## Karakteristik Umum:
- Sayap keras (elytra) yang melindungi sayap asli
- Mulut tipe pengunyah
- Metamorfosis sempurna (telur-larva-pupa-imago)

## Jenis Hama:
🐞 Colorado Beetle → Kepodang
🐞 Leaf Beetle → Kumbang daun
🐞 Blister Beetle → Kumbang lepuh
🐞 Longhorn Beetle → Kumbang tanduk panjang

## Pengendalian:
✅ Mekanis: Pengumpulan manual
✅ Biologi: Predator alami
✅ Kimia: Insektisida sistematik
✅ Pencegahan: Kebersihan lahan

## Peran Ekologi:
⚠️ Beberapa spesies adalah hama serius
✅ Banyak yang bermanfaat sebagai dekomposer
""",
    "butterfly": """
# 🦋 Butterfly (Kupu-Kupu)

**Klasifikasi:** Ordo Lepidoptera
**Ukuran:** 1-30 cm (tergantung spesies)
**Sayap:** Bersisik dan berwarna-warni

## Karakteristik:
- Metamorfosis sempurna: telur → larva (ulat) → pupa (kepompong) → imago
- Mulut berbentuk proboscis untuk mengisap nectar
- Aktif siang hari (kebanyakan)

## Siklus Hidup:
1️⃣ Telur → 3-5 hari
2️⃣ Larva (Ulat) → 3-5 minggu
3️⃣ Pupa → 10-15 hari
4️⃣ Imago → 2-6 minggu (tergantung spesies)

## Habitat:
🌸 Kebun dengan bunga
🌳 Area bervegetasi
🌲 Hutan

## Fungsi Ekologi:
✅ Penyerbuk bunga yang penting
✅ Indikator kesehatan lingkungan
✅ Sumber makanan satwa liar
✅ Nilai estetika tinggi

## Konservasi:
Banyak spesies terancam punah!
""",
    "dragonfly": """
# 🐉 Dragonfly (Capung)

**Klasifikasi:** Ordo Odonata
**Ukuran:** 2-15 cm
**Umur:** Imago 2-10 minggu

## Karakteristik:
- Predator udara yang sangat efektif
- Mata compound yang besar dengan penglihatan 360°
- Terbang dengan kecepatan hingga 50 km/jam
- Tubuh memanjang, sayap transparan

## Siklus Hidup (Nimfa Air):
- Bermetamorfosis tidak sempurna
- Hidup di air selama berbulan-bulan hingga tahun
- Predator larva serangga dan berudu

## Sebagai Predator:
🦟 Memangsa nyamuk
🦠 Memangsa lalat
🐛 Memangsa serangga kecil

## Habitat:
💧 Sungai
💧 Kolam
💧 Rawa
💧 Danau

## Nilai Ekologi:
✅ Kontrol populasi nyamuk secara alami
✅ Indikator kualitas air yang baik
✅ Penting untuk rantai makanan
""",
    "grasshopper": """
# 🦗 Grasshopper (Belalang)

**Klasifikasi:** Ordo Orthoptera
**Ukuran:** 1.5-6 cm
**Suara:** Bersiul-siul (stridulasi)

## Karakteristik:
- Kaki belakang yang kuat untuk lompatan hingga 20x panjang tubuhnya
- Metamorfosis tidak sempurna
- Tubuh ramping hijau atau coklat

## Perilaku:
- Omnivora, pemakan tumbuhan, rerumputan, atau tanaman budidaya
- Fase soliter dan gregaria (fase rombongan/swarm)
- Aktif siang hari

## Sebagai Hama:
⚠️ Dapat membentuk rombongan besar (locust plagues)
⚠️ Merusak panen signifikan
✅ Tingkat kerusakan sangat tergantung cuaca

## Pengendalian:
✅ Monitoring pemantauan
✅ Insektisida untuk outbreak
✅ Pengelolaan habitat
✅ Predator alami (burung, reptil)

## Nilai Gizi:
Belalang adalah sumber protein untuk konsumsi manusia di beberapa negara!
""",
    "mosquito": """
# 🦟 Mosquito (Nyamuk)

**Klasifikasi:** Ordo Diptera, Keluarga Culicidae
**Ukuran:** 3-9 mm
**Umur:** Betina (hingga 10 minggu), Jantan (2-3 minggu)

## Karakteristik:
- Hanya nyamuk betina yang menghisap darah (untuk produksi telur)
- Jantan hanya menghisap nectar
- Antena berbulu pada jantan, halus pada betina

## Siklus Hidup (4-7 hari):
1️⃣ Telur di permukaan air
2️⃣ Larva → Pupa (akuatik)
3️⃣ Imago (dewasa)

## Vektor Penyakit:
🦟 Malaria (Anopheles)
🦟 Demam Berdarah (Aedes)
🦟 Demam Kuning (Aedes)
🦟 Zika (Aedes)

## Habitat Perindukan:
💧 Air tergenang (kolam, kaleng, piring bunga)
💧 Genangan di atap
💧 Wadah tidak terpakai

## Pencegahan:
✅ Buang/bersihkan genangan air
✅ Gunakan kelambu berinsektisida
✅ Aplikasi abatisasi
✅ Penggunaan repellent
""",
    "bee": """
# 🐝 Bee (Lebah)

**Klasifikasi:** Ordo Hymenoptera, Keluarga Apidae
**Ukuran:** 12-15 mm (pekerja)
**Umur:** Ratu (5-7 tahun), Pekerja (4-6 minggu), Jantan (4-5 minggu)

## Karakteristik:
- Serangga sosial dengan koloni terstruktur
- Rambut berbercabang untuk mengumpulkan serbuk sari
- Aorkan sengat barb (lebah tidak bisa ditarik kembali)

## Struktur Koloni:
👑 1 Ratu
🐝 20,000-80,000 Pekerja
🐝 300-1,000 Jantan (musiman)

## Siklus Hidup:
- Telur 3 hari
- Larva 6 hari
- Pupa 12-15 hari
- Imago (total: 21 hari untuk pekerja)

## Fungsi Ekologi:
✅ Penyerbuk utama (80% tanaman berbunga)
✅ Produksi madu
✅ Produksi royal jelly & propolis
✅ Penting untuk ketahanan pangan

## Ancaman:
⚠️ Pestisida neonikotinoid
⚠️ Hilangnya habitat
⚠️ Penyakit Varroa

## Pelestarian:
Lindungi lebah untuk masa depan pertanian!
""",
    "wasp": """
# 🐝 Wasp (Tawon/Vespa)

**Klasifikasi:** Ordo Hymenoptera
**Ukuran:** 1-5 cm (tergantung spesies)
**Temperamen:** Lebih agresif dari lebah

## Karakteristik:
- Pinggang sempit (perut terpisah dari thorax)
- Sengat halus dapat digunakan berkali-kali
- Sebagian besar solitaris, ada yang sosial

## Jenis Utama:
🐝 Yellowjacket (Vespula)
🐝 Paper Wasp (Polistes)
🐝 European Hornet (Vespa crabro)

## Perilaku:
- Predator serangga lainnya
- Tertarik pada makanan manis
- Territorial dan defensif
- Konstruktor sarang dari kertas (dari air liur)

## Sebagai Bermanfaat:
✅ Predator hama tanaman
✅ Penyerbuk sekunder
✅ Kontrol populasi serangga

## Sebagai Ancaman:
⚠️ Sengatan menyakitkan
⚠️ Alergi berbahaya (anafilaksis)
⚠️ Agresif saat sarang diganggu

## Penanganan:
🛡️ Hindari sarang
🛡️ Jangan pukul di udara
🛡️ Konsultasi profesional untuk penghilangan
""",
    "fly": """
# 🪰 Fly (Lalat)

**Klasifikasi:** Ordo Diptera
**Ukuran:** 2-12 mm (tergantung spesies)
**Umur:** 2-8 minggu

## Karakteristik:
- Satu pasang sayap fungsional (pasangan belakang bermodifikasi menjadi balancer)
- Mata compound yang besar
- Mulut siphoning (hisap) untuk cairan

## Metamorfosis:
1️⃣ Telur (1 hari)
2️⃣ Larva/Belatung (5-8 hari)
3️⃣ Pupa (3-5 hari)
4️⃣ Imago

## Jenis dan Dampak:
🪰 Housefly → Vektor penyakit
🪰 Fruit Fly → Hama buah
🪰 Bot Fly → Parasit
🪰 Robber Fly → Predator bermanfaat

## Sebagai Hama:
⚠️ Perantara penyakit (tifus, kolera, diare)
⚠️ Kontaminasi makanan
⚠️ Mengganggu kesehatan manusia

## Sebagai Bermanfaat:
✅ Dekomposer limbah organik
✅ Penyerbuk
✅ Sumber protein (untuk ikan & unggas)

## Pencegahan:
✅ Kebersihan lingkungan
✅ Manajemen limbah
✅ Penggunaan trap dan repellent
""",
    "spider": """
# 🕷️ Spider (Laba-Laba)

**Klasifikasi:** Kelas Arachnida, Ordo Araneae
**Ukuran:** 1-30 cm (inklusif kaki)
**Umur:** 1-25 tahun (tergantung spesies)

## Karakteristik:
- 8 kaki (bukan serangga, tapi arachnida)
- Banyak mata (hingga 12), penglihatan bervariasi
- Menghasilkan sutra dari spineret
- Predator aktif

## Tipe Predasi:
🕷️ Web spiders → Perangkap sutra
🕷️ Jumping spiders → Pemburu aktif
🕷️ Hunting spiders → Pelihara sempurna
🕷️ Trapdoor spiders → Ambush predator

## Siklus Hidup:
- Tidak sempurna metamorfosis
- Melalui beberapa instar (kulit ganti)
- Dioecious (terpisah jantan-betina)

## Nilai Ekologi:
✅ Kontrol hama serangga secara alami
✅ Predator spider bermanfaat
✅ Tidak berbahaya untuk manusia (kebanyakan)
✅ Indikator ekosistem sehat

## Sebagai Hama:
⚠️ Umumnya tidak merugikan
✅ Hanya beberapa spesies memiliki bisa berbahaya

## Manfaat Pertanian:
Satu laba-laba dapat memangsa 50-100 serangga per hari!
""",
    "caterpillar": """
# 🐛 Caterpillar (Ulat)

**Klasifikasi:** Larva dari Lepidoptera (Kupu-kupu & Ngengat)
**Ukuran:** 1 mm - 12 cm (tergantung spesies)
**Warna:** Hijau, coklat, atau bergaris

## Karakteristik:
- Tubuh berbuku dengan 3 pasang kaki sejati + kaki semu
- Mulut pengunyah (makan daun besar-besaran)
- Bermetamorfosis sempurna (menjadi kupu-kupu/ngengat)

## Perilaku Makan:
🥬 Herbivora (pemakan tumbuhan)
🍃 Beberapa spesies monofag (1 tanaman saja)
🌾 Beberapa polifag (banyak tanaman)
📊 Dapat menurunkan hasil panen hingga 90%

## Sebagai Hama:
⚠️ Hama serius pada padi, jagung, kacang
⚠️ Hama hortikultura (kubis, tomat, dll)
⚠️ Merusak daun dan buah

## Pengendalian:
✅ Penyemprotan Bt (Bacillus thuringiensis)
✅ Insektisida botanis (neem oil)
✅ Predator alami (parasitoid, predator)
✅ Pengelolaan lahan

## Manfaat:
✅ Makanan manusia (entomophagy)
✅ Bahan kosmetik
✅ Penelitian ilmiah
"""
}



class GeminiExpert:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.max_retries = 3
        self.retry_delay = 2  # detik

        if api_key:
            try:
                self.client = genai.Client(
                    api_key=api_key
                )

                print("✅ Gemini Client berhasil diinisialisasi")

            except Exception as e:
                print(f"❌ Gagal inisialisasi Gemini: {e}")

        else:
            print(
                "⚠️ GEMINI_API_KEY tidak ditemukan. "
                "AI Insight dinonaktifkan."
            )

    def _make_request_with_retry(
        self,
        prompt: str,
        use_thinking: bool = True,
        use_search: bool = True,
        retry_count: int = 0
    ) -> Optional[str]:
        """
        Membuat request ke Gemini dengan retry logic untuk menangani 503 errors.
        """
        if not self.client:
            return None

        try:
            # Konfigurasi request dengan ThinkingConfig dan Google Search
            thinking_config = None
            tool_config = None

            if use_thinking:
                thinking_config = {
                    "type": "enabled",
                    "budget_tokens": 5000  # Token untuk thinking process
                }

            if use_search:
                # Enable Google Search untuk grounding
                tool_config = {
                    "google_search": {}
                }

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "thinking": thinking_config,
                    "tools": [tool_config] if use_search else None
                }
            )

            if hasattr(response, "text") and response.text:
                return response.text

            return None

        except (exceptions.ServiceUnavailable, exceptions.InternalServerError) as e:
            # Error 503 atau 500 - retry
            if retry_count < self.max_retries:
                print(
                    f"⚠️ Gemini service unavailable (attempt {retry_count + 1}/{self.max_retries}). "
                    f"Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)
                # Exponential backoff
                self.retry_delay *= 1.5
                return self._make_request_with_retry(
                    prompt,
                    use_thinking,
                    use_search,
                    retry_count + 1
                )
            else:
                print(f"❌ Gemini Error after {self.max_retries} retries: {e}")
                return None

        except exceptions.RateLimitError as e:
            # Rate limit - tunggu lebih lama
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                print(
                    f"⚠️ Rate limit hit. Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)
                return self._make_request_with_retry(
                    prompt,
                    use_thinking,
                    use_search,
                    retry_count + 1
                )
            else:
                print(f"❌ Rate limit exceeded after {self.max_retries} retries")
                return None

        except Exception as e:
            print(f"❌ Gemini Error: {type(e).__name__}: {e}")
            return None

    def _get_fallback_knowledge(self, insect_name: str) -> str:
        """
        Get fallback knowledge dari database lokal untuk serangga umum.
        """
        insect_lower = insect_name.lower().strip()
        
        # Try exact match
        if insect_lower in INSECT_KNOWLEDGE:
            return INSECT_KNOWLEDGE[insect_lower]
        
        # Try partial match
        for key, knowledge in INSECT_KNOWLEDGE.items():
            if key in insect_lower or insect_lower in key:
                return knowledge
        
        # Default response untuk serangga tidak dikenal
        return f"""
# 🐞 Hasil Identifikasi

**{insect_name}**

Serangga ini teridentifikasi dengan baik oleh model AI kami. 

Sayangnya, informasi detail khusus untuk "{insect_name}" belum tersedia dalam database kami saat ini. 

**Rekomendasi:**
- Gunakan Google Lens atau iNaturalist untuk informasi lebih lanjut
- Konsultasi dengan ahli entomologi setempat
- Cek website pertanian lokal untuk panduan pengendalian

Serangga yang teridentifikasi telah melalui training dengan 90,000+ gambar dan 118 kelas serangga!
"""

    def get_insect_info(
        self,
        insect_name: str
    ) -> str:

        # Prioritas 1: Coba Gemini dengan API key
        if self.client:
            prompt = f"""
Anda adalah ahli entomologi profesional dengan akses ke sumber terkini.

Model AI mendeteksi serangga berikut:

{insect_name}

ATURAN PENTING:

1. Jawab dalam Bahasa Indonesia.
2. Gunakan format Markdown yang rapi.
3. Jangan menjelaskan keterbatasan AI.
4. Jangan mengatakan nama tidak ditemukan.
5. Jika data spesifik tidak tersedia, berikan informasi umum yang paling mendekati.
6. Jangan memberikan paragraf panjang.
7. Maksimal 250 kata.
8. Sumber informasi boleh dari web search jika relevan.

Gunakan format berikut:

# 🐞 Nama Serangga
{insect_name}

# 🔬 Nama Ilmiah
(tulis jika diketahui)

# 📚 Klasifikasi
- Kingdom:
- Filum:
- Kelas:
- Ordo:
- Famili:

# 🌿 Habitat
(deskripsi singkat)

# ✨ Karakteristik
- poin 1
- poin 2
- poin 3

# 🌎 Peran Ekosistem
(deskripsi singkat)

# 🎯 Fakta Unik
- fakta unik 1
- fakta unik 2
"""

            # Reset retry delay setiap request
            self.retry_delay = 2

            # Coba dengan thinking dan search
            result = self._make_request_with_retry(
                prompt,
                use_thinking=True,
                use_search=True,
                retry_count=0
            )

            if result:
                return result

            # Fallback: coba tanpa thinking tapi dengan search
            print("⚠️ Trying Gemini fallback: without thinking...")
            result = self._make_request_with_retry(
                prompt,
                use_thinking=False,
                use_search=True,
                retry_count=0
            )

            if result:
                return result

            print("⚠️ Gemini API gagal, menggunakan knowledge base lokal")

        # Prioritas 2: Gunakan knowledge base lokal
        return self._get_fallback_knowledge(insect_name)