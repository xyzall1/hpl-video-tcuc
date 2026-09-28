# 🎬 HPL Video TCUC

**Skill Claude Code** untuk memproduksi *learning video* bergaya **storytelling** sesuai **house style Telkom CorpU**. Bahan mentahnya bisa berupa script polos atau VO rekaman, gambar scene, dan bumper. Hasil akhirnya adalah video MP4 16:9 720p lengkap dengan motion graphic, subtitle, dan jeda napas yang natural.

Skill ini menggabungkan beberapa tool:
- **ElevenLabs** untuk voice over
- **HyperFrames** untuk motion graphic
- **Pexels** untuk footage stock
- **Tesseract** untuk perakitan dan export

Alurnya dijaga agar tiap video punya gaya yang sama: nuansa putih, aksen teal `#2796A3`, dan subtitle berbentuk pill.

---

## Daftar isi
1. [Apa yang dihasilkan](#-apa-yang-dihasilkan)
2. [Alur kerja](#-alur-kerja)
3. [Fitur utama](#-fitur-utama)
4. [Tools di dalam skill](#-tools-di-dalam-skill)
5. [Struktur folder](#-struktur-folder)
6. [Instalasi](#-instalasi)
7. [Cara pakai](#-cara-pakai)
8. [Konfigurasi](#-konfigurasi)
9. [House style](#-house-style)
10. [Troubleshooting](#-troubleshooting)
11. [Credit](#-credit)

---

## 📦 Apa yang dihasilkan

Untuk setiap folder scene (misal `DV3 KB2/SC3/`), skill membuat subfolder `<Scene>_Video/` yang berisi:

| File | Keterangan |
|---|---|
| `<Scene>.mp4` | Video final, 1280×720, 30 fps, H.264 + AAC |
| `<Scene>.tsrct` | Proyek Tesseract yang **masih bisa diedit**: subtitle, gambar, timing, dan audio |
| `hf/index.html` | Sumber motion graphic HyperFrames, bisa diedit lalu dirender ulang |
| `vo/vo.wav`, `vo/timing.json` | VO dengan jeda napas dan data timing per kalimat |
| `stock/` + `credits.txt` | Footage Pexels yang dipakai beserta atribusinya |
| `Previews/Filmstrip.png` | Ringkasan visual seluruh video |
| `Versions/` | Arsip hasil sebelumnya setiap kali ada revisi |

Struktur video: **Bumper In** (audio asli) → **Isi** (VO + motion graphic + scene + subtitle) → **Bumper Out** (audio asli).

---

## 🔄 Alur kerja

```
 script.txt ──► [tts-script-enhancer] ──► ElevenLabs ──┐
                                                       ├──► vo.wav + timing.json
 VO rekaman + transkrip ──► deteksi & sisip jeda ──────┘              │
                                                                      ▼
                                              ✋ STORYBOARD (+ kandidat Pexels)
                                                                      │
                                                                      ▼
                                              HyperFrames: motion graphic
                                                                      │
                                                                      ▼
                                              ✋ PREVIEW (contact sheet)
                                                                      │
                                                                      ▼
                          Tesseract: bumper + MG + scene + stock + subtitle + VO
                                                                      │
                                                                      ▼
                                              MP4 720p + proyek .tsrct
```

✋ = **titik konfirmasi**. Claude berhenti dan menunggu persetujuanmu di dua titik ini. Langkah lainnya berjalan otomatis.

| # | Tahap | Yang terjadi |
|---|---|---|
| 0 | Inventaris | Claude memeriksa isi folder (script/VO, transkrip, bumper, gambar, footage), membaca durasi, dan **melihat setiap gambar** untuk memahami isinya. |
| 1A | VO dari script | Script bisa diperkaya tag suara (misalnya `[sighs]`) lalu dibuat per kalimat di ElevenLabs. Hasilnya disambung dengan jeda napas, dan timing tiap huruf tercatat. |
| 1B | VO rekaman | Jeda antarkalimat dideteksi dari audio dan dicocokkan dengan transkrip. Jeda napas disisipkan tanpa mengubah kecepatan bicara. |
| 2 | Storyboard ✋ | Tabel beat berisi waktu, kalimat VO, dan visual (scene gambar, motion graphic, atau stock Pexels), lengkap dengan lembar thumbnail kandidat stock. |
| 3 | Motion graphic | Dibangun dari template house style di HyperFrames. Momen kunci animasi jatuh tepat pada kata yang diucapkan. |
| 4 | Preview ✋ | Contact sheet satu frame per beat. Setelah disetujui, motion graphic dirender. |
| 5 | Perakitan | Satu script merakit semuanya di Tesseract lalu export, filmstrip, dan cek loudness. |
| 6 | Serah terima | Laporan file hasil, durasi, dan hal-hal yang masih bersifat perkiraan. |

**Mode batch:** beberapa folder scene (SC1, SC2, …) bisa diproses sekaligus. Semua storyboard disetujui dalam satu kali konfirmasi, begitu juga semua preview.

---

## ✨ Fitur utama

- **🎙️ VO otomatis dari script.** Memakai ElevenLabs (default `eleven_v3`, voice bisa diatur) dengan dukungan *audio tags* dari tts-script-enhancer. Tag hanya memengaruhi suara dan otomatis dibuang dari subtitle.
- **🫁 Jeda napas natural.** Default +0,4 detik antarkalimat dan +1,0 detik antarparagraf atau pergantian topik. Berlaku untuk VO ElevenLabs maupun VO rekaman.
- **🎯 Timing presisi.** Untuk VO ElevenLabs, subtitle dan animasi diselaraskan dengan timestamp per karakter. Untuk VO rekaman, timing dicocokkan ke jeda nyata di audio (±0,3 detik).
- **🎨 Motion graphic editable.** HTML + GSAP di HyperFrames, dengan komponen siap pakai: counter angka, tile grafik mini, kartu, pill, mock dashboard, dan lainnya.
- **🖼️ Scene & stock footage.** Gambar scene dan footage di-*cover* ke kanvas, diberi crossfade dan zoom pelan. Footage Pexels dicari, dipilih, diunduh, dan diberi kredit otomatis.
- **💬 Subtitle house style.** Pill teal `#2796A3`, teks putih Poppins Bold, maksimal satu baris, dipecah di koma. Typo dan penulisan nama dirapikan.
- **🔊 Mix audio aman.** Gain bumper dikoreksi karena bumper bawaannya clipping. Target loudness sekitar −16…−14 LUFS dengan peak ≤ −1 dB.
- **✏️ Hasil tetap bisa diedit.** Proyek `.tsrct` dan sumber HyperFrames disimpan. Revisi tidak perlu mulai dari nol, dan versi lama diarsipkan.
- **🔐 Aman untuk dibagikan.** API key tidak pernah disimpan di repo. Tiap anggota tim memakai key dan voice pilihannya sendiri.

---

## 🧰 Tools di dalam skill

Semua script ada di `scripts/` dan bisa juga dijalankan manual dari Terminal.

### `make_vo.py`: membuat VO dari script (ElevenLabs)
```bash
python3 scripts/make_vo.py --script script.txt --out-dir work/vo [--voice-id ID] [--model eleven_v3] \
        [--pause-sentence 0.4] [--pause-paragraph 1.0]
```
- **Format script:** baris kosong menandai paragraf baru. Kalimat diakhiri `.`, `?`, atau `!`. Tag `[...]` boleh dipakai.
- **Cara kerja:** setiap kalimat dibuat lewat endpoint *with-timestamps*, lalu disambung sebagai WAV (akurat per sampel) dengan jeda napas.
- **Bisa dilanjutkan:** kalimat yang sudah jadi tidak dibuat ulang saat perintah dijalankan lagi, jadi hemat kuota.
- **Output:** `vo.wav` (master), `vo.mp3` (untuk didengar atau dibagikan), dan `timing.json`.

### `vo_pauses.py`: jeda napas untuk VO rekaman
```bash
python3 scripts/vo_pauses.py detect --vo "VO.mp3" --transcript transkrip.txt --out work/vo/cuts.json
python3 scripts/vo_pauses.py apply  --cuts work/vo/cuts.json --out-dir work/vo
```
- **`detect`:** mencocokkan tiap baris transkrip Whisper (`[mm:ss] teks`) ke jeda nyata di audio, lalu mengusulkan jenis jedanya: `S` untuk kalimat, `P` untuk paragraf, `-` untuk tanpa jeda.
- **Review `cuts.json`:** tandai pergantian topik sebagai `P` dan perbaiki teks subtitle kalau perlu.
- **`apply`:** menyisipkan jeda lalu menulis `vo.wav` dan `timing.json`, dengan format yang sama seperti `make_vo.py`.

### `pexels.py`: mencari dan mengunduh footage stock
```bash
python3 scripts/pexels.py search   --query "field worker checking phone" --kind video --out work/stock/beat07.json
python3 scripts/pexels.py download --candidates work/stock/beat07.json --id 6868428 --dest work/stock --name field-phone
```
- **`search`:** mencari video landscape (atau foto dengan `--kind photo`), lalu membuat lembar thumbnail bernomor (`.jpg`) untuk dipilih.
- **`download`:** mengunduh file MP4 720–1080p dan menambahkan atribusi ke `credits.txt`.
- **Sumber:** langsung dari API resmi Pexels, tanpa server pihak ketiga.

### `build_tesseract.py`: perakitan dan export
```bash
python3 scripts/build_tesseract.py work/assemble.json
```
- **Membuat proyek `.tsrct` baru:** kalau proyek lama sudah ada, proyek itu dan MP4-nya dipindah ke `Versions/`.
- **Mengimpor semua media:** bumper, motion graphic, VO, scene, stock, dan font.
- **Menyusun timeline:** bumper in → isi → bumper out.
- **Scene gambar dan footage:** di-*cover* ke kanvas, dengan crossfade 350 ms dan push-in 5 %.
- **Subtitle:** pill house style dengan lebar pill otomatis mengikuti panjang teks.
- **Export:** MP4 720p30, filmstrip, dan ringkasan loudness.
- Format `assemble.json` dijelaskan di [`references/assemble-config.md`](references/assemble-config.md).

### `timing_lib.py`: helper bersama
Berisi pemuat konfigurasi (default + pribadi), pembersih tag audio, dan pemecah subtitle. Subtitle dipecah di koma lalu diseimbangkan per kata, dan waktu tiap potongan diambil dari data per karakter bila tersedia.

### `assets/hf-template/`: template motion graphic
Berisi HTML HyperFrames siap pakai dengan:
- palet dan tipografi house style
- helper `el`, `miniTile`, `popIn`, `rise`, `out`, `fadeScene`, dan `rnd` (random dengan seed, supaya render deterministik)
- satu contoh beat

---

## 🗂️ Struktur folder

```
hpl-video-tcuc/
├── SKILL.md                  # SOP yang dibaca Claude (alur, titik konfirmasi, aturan)
├── README.md                 # dokumen ini
├── config.default.json       # preset bersama: jeda, subtitle, export, gain bumper, model TTS
├── config.json               # (pribadi, tidak di-commit) misal voice_id kamu
├── scripts/
│   ├── make_vo.py            # VO dari script via ElevenLabs
│   ├── vo_pauses.py          # jeda napas untuk VO rekaman
│   ├── pexels.py             # cari & unduh stock Pexels
│   ├── build_tesseract.py    # rakit & export di Tesseract
│   └── timing_lib.py         # helper bersama
├── assets/
│   ├── hf-template/index.html  # template motion graphic house style
│   └── fonts/                  # Plus Jakarta Sans, Poppins (+ lisensi OFL)
└── references/
    ├── house-style.md        # palet, tipografi, zona layout, preset subtitle, tempo
    ├── pitfalls.md           # jebakan teknis yang sudah diketahui & solusinya
    └── assemble-config.md    # format timing.json, assemble.json, config.json
```

---

## ⚙️ Instalasi

### 1. Prasyarat
| Kebutuhan | Keterangan |
|---|---|
| [Claude Code](https://claude.com/claude-code) | Desktop app atau CLI |
| `ffmpeg` / `ffprobe` | Untuk olah dan cek audio/video |
| Python 3.9+ dan [Pillow](https://pypi.org/project/pillow/) | `pip3 install pillow` |
| Node.js 18+ | Untuk `npx hyperframes` |
| Tesseract CLI 0.2.x | Ikuti panduan instalasi di skill `tesseract-video` |
| Skill pendamping | `hyperframes` (+ `hyperframes-core`), `tesseract-video`, dan `tts-script-enhancer` (opsional) |

### 2. Pasang skill
```bash
git clone https://github.com/entuds/hpl-video-tcuc.git ~/.claude/skills/hpl-video-tcuc
```
Untuk update ke versi terbaru: `git -C ~/.claude/skills/hpl-video-tcuc pull`

### 3. Simpan API key (masing-masing orang)
Key disimpan di file pribadi, **bukan di folder skill**. Tempel key **sekali** saja saat diminta:
```bash
mkdir -p ~/.config/elevenlabs && read -s -p "ElevenLabs key: " K && printf '%s' "$K" > ~/.config/elevenlabs/key && chmod 600 ~/.config/elevenlabs/key && unset K
mkdir -p ~/.config/pexels && read -s -p "Pexels key: " K && printf '%s' "$K" > ~/.config/pexels/key && chmod 600 ~/.config/pexels/key && unset K
```
- Key ElevenLabs: [elevenlabs.io](https://elevenlabs.io/) → Profile → API Keys
- Key Pexels (gratis): [pexels.com/api](https://www.pexels.com/api/)
- Alternatifnya, pakai environment variable `ELEVENLABS_API_KEY` / `PEXELS_API_KEY`.

> Jangan tempel API key di chat Claude, dan jangan commit key ke repo.

---

## 🚀 Cara pakai

Buka Claude Code di folder scene, lalu minta dengan bahasa biasa. Contoh:

- *"Buat learning video dari folder ini."*
- *"Buat VO dari script.txt pakai voice Arunika, lalu jadikan learning video."*
- *"Proses folder SC1 sampai SC5 dengan style yang sama."*
- *"Jedanya terlalu cepat, tambah jeda antar paragraf."* (untuk revisi)

**Isi folder scene yang dikenali:**

| File | Contoh nama |
|---|---|
| Script polos atau transkrip Whisper | `script.txt`, `transcript_VO SC3.txt` |
| VO rekaman (opsional kalau ada script) | `VO SC3.mp3` |
| Bumper | `Bumper In ....mp4`, `Bumper Out ....mp4` |
| Gambar scene (nama file menjelaskan momennya) | `bagas put every graph at once.png` |
| Footage tambahan (opsional) | `*.mp4`, `*.mov` |

---

## 🔧 Konfigurasi

`config.default.json` berisi preset bersama tim. Untuk pengaturan pribadi, buat `config.json` di folder skill. File ini otomatis diabaikan git dan hanya perlu berisi bagian yang ingin diubah:

```json
{
  "elevenlabs": { "voice_id": "o5s6XRBkPSTD4syv6mZg" },
  "pauses": { "sentence": 0.5, "paragraph": 1.2 }
}
```

| Kunci | Default | Fungsi |
|---|---|---|
| `elevenlabs.voice_id` | – | Voice default (wajib untuk jalur script) |
| `elevenlabs.model_id` | `eleven_v3` | Model TTS (v3 mendukung audio tags) |
| `pauses.sentence` / `paragraph` | 0.4 / 1.0 s | Jeda napas |
| `pauses.lead_in` / `tail` | 0.3 / 0.6 s | Hening di awal dan akhir VO |
| `subtitle.*` | pill `#2796A3`, Poppins Bold 44, y = 1000 | Preset subtitle |
| `subtitle.max_chars` | 56 | Panjang maksimum satu baris subtitle |
| `export.resolution` / `fps` | 720p / 30 | Output video |
| `bumper_gain` | 0.63 (≈ −4 dB) | Koreksi volume bumper |

---

## 🎨 House style

| Elemen | Nilai |
|---|---|
| Background | `#F6F8F9` + dot grid halus, kartu putih |
| Warna utama | Teal `#2796A3`, teal muda `#7CC6CE`, ink `#1D2B36` |
| Aksen | Amber `#F2A541` (sorotan), merah `#E25C5C` (gagal / ≠) |
| Font MG | Plus Jakarta Sans (800 judul, 700 label) |
| Subtitle | Pill `#2796A3`, teks `#FFFFFF`, Poppins Bold, 1 baris, di tengah bawah |
| Output | 16:9, 1280×720, 30 fps |
| Tempo | +0,4 s antarkalimat, +1,0 s antarparagraf |

Detail lengkap ada di [`references/house-style.md`](references/house-style.md).

---

## 🩺 Troubleshooting

| Gejala | Solusi |
|---|---|
| `ElevenLabs error 401` | Key salah atau tertempel ganda. Simpan ulang key dengan perintah di atas dan tempel sekali saja. |
| `No voice id` | Isi `elevenlabs.voice_id` di `config.json`, atau sebutkan voice-nya saat meminta. |
| `PEXELS_API_KEY is not set` | Simpan key Pexels (lihat bagian Instalasi). |
| Tesseract `missing_fonts` | Font tidak kompatibel dengan renderer. Pakai Poppins atau Inter (lihat `pitfalls.md`). |
| Audio clipping di bumper | Turunkan `bumper_gain`. |
| `tsrct not found` | Instal Tesseract CLI sesuai skill `tesseract-video`, atau set env `TSRCT`. |

Daftar lengkap jebakan teknis ada di [`references/pitfalls.md`](references/pitfalls.md).

---

## 🙏 Credit

Skill ini dibangun di atas karya dan layanan berikut:

| Komponen | Peran | Sumber |
|---|---|---|
| **Claude Code** (Anthropic) | Agen yang menjalankan skill, menulis motion graphic, dan meninjau hasil | [claude.com/claude-code](https://claude.com/claude-code) |
| **HyperFrames** (HeyGen) | Framework video dari HTML untuk motion graphic, beserta skill `hyperframes`, `hyperframes-core`, dan `hyperframes-cli` | [github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes), Apache-2.0 |
| **Tesseract** (Mirage) | Editor dan renderer video lokal untuk perakitan, subtitle, dan export, beserta skill `tesseract-video` dan `tesseract-motion` | [github.com/mirage-hq/tesseract](https://github.com/mirage-hq/tesseract) |
| **tts-script-enhancer** (by [@entuds](https://github.com/entuds)) | Skill untuk menambahkan audio tags ke script tanpa mengubah kata | Skill buatan pemilik repo ini |
| **ElevenLabs** | Text-to-speech dengan timestamp per karakter | [elevenlabs.io](https://elevenlabs.io/) |
| **Pexels** | Footage dan foto stock gratis | [pexels.com](https://www.pexels.com/), [lisensi](https://www.pexels.com/license/) |
| **GSAP** (GreenSock) | Runtime animasi di HyperFrames | [gsap.com](https://gsap.com/) |
| **FFmpeg** | Olah dan analisis audio/video | [ffmpeg.org](https://ffmpeg.org/) |
| **Plus Jakarta Sans** (Tokotype) | Font motion graphic | [SIL OFL 1.1](assets/fonts/OFL-PlusJakartaSans.txt) |
| **Poppins** (Indian Type Foundry) | Font subtitle | [SIL OFL 1.1](assets/fonts/OFL-Poppins.txt) |

House style, alur, dan preset disusun untuk produksi learning video **Telkom CorpU**.

