# AGENTS.md: HPL CMS workbook

Instructions for any coding agent that can run shell commands and read and write local files (Codex CLI, Cursor, Gemini CLI, …). The same workflow is packaged for Claude as `SKILL.md`; this file mirrors it.
Requires Python 3.9+ with openpyxl. Use `scripts/build_cms.py` to write the workbook; do not build the Excel file by hand, so the format and credit block stay identical.


# Workbook CMS HPL

Skill root = folder file ini (`$SKILL`). Hasilnya satu file `.xlsx` per kompetensi, **satu sheet per level** (mis. `TC262 L1`, `TC262 L2`, `TC262 L3`), satu baris per LU. Contoh lengkap: `examples/TC262_SMP.json` (Strategic Media Planning L1–L3).

## Kolom (urutan tetap)
| Kolom | Isi |
|---|---|
| No | 1, 2, 3, … |
| LU | `KB1 · Modul 1` |
| Course Design | Nama course per KB, persis dari course plan/tracker user (mis. "Fondasi Strategic Media Planning"). Jangan mengarang; tanyakan bila belum ada. |
| Course Description | 2 kalimat: "Course ini membangun/membahas/mengenalkan … mulai dari …, …, hingga … ." lalu "Setelah mengikuti course ini, peserta mampu …" (mengikuti kata kerja KB). |
| Learning Content Title | = Judul Modul |
| Text Core | Per KB: **"Konten ini berfokus pada penjelasan "** + isi Key Behaviour (KB) kompetensi. Ubah kata kerja awal KB agar nyambung: "Mampu menjelaskan X" → "X"; "Menerapkan …" → "penerapan …"; "Mengidentifikasi/Menganalisis/Merancang/Melakukan …" → "cara mengidentifikasi/…". Sisanya sama persis dengan KB (perbaiki salah ketik saja, mis. "merespon" → "merespons"). Sama untuk semua LU dalam satu KB. |
| Judul Modul | Judul modul/LU dari course plan |
| Judul Video | Judul video final (dari file/script video) |
| Caption Video | Kredit video + baris kosong + isi caption |
| Judul Audio | Judul audio final (NotebookLM) |
| Caption Audio | Kredit audio + baris kosong + isi caption |
| Judul Artikel | Judul artikel; **harus berbeda dari Judul Modul** (lebih spesifik, boleh pakai pola "X: Y") |

## Kredit caption (ditambahkan otomatis oleh script)
```
Produced with the support of Artificial Intelligence (AI) tools: Claude.
Learning content created by Rosa Nur Aliana Sawafi.
Reviewed by Zidny Aghniya.

<isi caption>
```
Audio memakai tool `NotebookLM`. Nama pembuat, reviewer, dan tool diatur di `credits` pada data JSON; tanyakan ke user bila kompetensinya dibuat/di-review orang lain.

## Isi caption
- **Video:** 2–3 kalimat. Buka dengan kalimat pemantik yang dekat dengan masalah nyata, lalu "Video ini mengajak Anda memahami / membahas / menguraikan …" berisi poin utama video. Contoh: "Iklan yang bagus belum tentu efektif. Video ini mengajak Anda memahami apa itu strategic media planning, bedanya dengan media buying, …".
- **Audio:** 2 kalimat. "Dengarkan pembahasan tentang … . Audio ini membahas/menjelaskan/membantu Anda … ."
- Isi diambil dari konten sebenarnya (script/VO video, ringkasan audio, modul), bukan dikarang. Bahasa Indonesia baku, sapaan "Anda", istilah teknis Inggris boleh tanpa italic. Tanpa emoji, tanpa hashtag.

## Langkah
1. Kumpulkan sumber: daftar KB kompetensi per level (tabel KB dari user), nama course (Course Design), judul modul, dan konten final tiap LU (video, audio, artikel). Tanyakan hanya yang belum ada.
2. Tulis data ke JSON mengikuti `examples/TC262_SMP.json` (caption tanpa kredit).
3. **Sampel dulu:** bangun satu level, tunjukkan beberapa baris ke user, minta persetujuan sebelum level lain.
```bash
python3 "$SKILL/scripts/build_cms.py" build data.json "_CMS/CMS_<KODE>_<Kompetensi>_L1-L3.xlsx"
```
   Script memberi peringatan `CEK:` bila Text Core tidak berawalan benar, Judul Artikel = Judul Modul, judul kembar, caption terlalu panjang/pendek, atau ada tanda `[..]`. Perbaiki semua sebelum menyerahkan.
4. Tambahkan level berikutnya sebagai sheet baru di file yang sama, dengan aturan yang sama.
5. Revisi workbook yang sudah ada: `build_cms.py dump <file.xlsx> data.json` → ubah JSON → `build` lagi (format tetap seragam). Simpan salinan file lama sebelum menimpa.
6. Kirim file ke user dan ringkas perubahannya.

Format: header teal `#2796A3` teks putih tebal, teks rata atas dan wrap, border tipis, freeze di kolom C baris 2, lebar kolom tetap. Jangan ubah urutan kolom karena dipakai untuk upload.
