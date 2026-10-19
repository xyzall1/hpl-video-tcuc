# AGENTS.md: HPL CMS workbook

Instructions for any coding agent that can run shell commands and read and write local files (Codex CLI, Cursor, Gemini CLI, …). The same workflow is packaged for Claude as `SKILL.md`; this file mirrors it (in Indonesian).
Requires Python 3.9+ with openpyxl and python-docx, and Node.js for `npx hyperframes transcribe`. Always write the workbook with `scripts/build_cms.py`; never build the Excel file by hand. If a step is blocked by a sandbox (e.g. transcription), stop and ask the user to approve running it outside the sandbox.


# Workbook CMS HPL

Skill root = folder file ini (`$SKILL`). Hasil: satu `.xlsx` per kompetensi, **satu sheet per level** (`TC229 L1`, `TC229 L2`, …), **satu baris per section/LU**. Contoh data: `examples/TC229_L1.json`.

## Kolom (urutan dari kiri, tetap)
| Kolom | Isi |
|---|---|
| Learning Content Title | Nama modul/section |
| Text Core Learning Content | **"Konten ini berfokus pada pembahasan mengenai "** + KB (dari Dirkom, kata kerja awal disesuaikan) |
| Judul Video | Judul video final |
| Deskripsi Video | Kredit + baris kosong + deskripsi ajakan |
| Judul Audio | Judul audio final |
| Deskripsi Audio | Kredit + baris kosong + deskripsi ajakan |
| Judul Artikel | Judul dari dokumen artikel (heading pertama) |
| Section Title | Nama modul/section (sama dengan Learning Content Title) |
| Nama Course | Nama course dari course plan / course design |
| Deskripsi Course | **"Course ini berfokus pada pembahasan mengenai "** + KB (sama dengan Text Core) |
| Learning Path Title | `<Nama kompetensi> <Level>`, mis. "User Interface Design Fundamental" (3 per kompetensi) |
| Learning Path Description | `Learning Path for <Nama kompetensi>: <Level>`, tanpa deskripsi tambahan |

**KB → frasa:** "Mampu menjelaskan X" → "X"; "Menerapkan …" → "penerapan …"; "Membuat …" → "cara membuat …"; "Mengidentifikasi/Menganalisis/Merancang/Melakukan/Menjalankan …" → "cara mengidentifikasi/…". Sisanya verbatim dari Dirkom; hanya perbaiki salah ketik nyata (mis. "digunakanseperti" → "digunakan seperti", "merespon" → "merespons").

## Kredit deskripsi video/audio — selalu input dari user
```
Produced with the support of Artificial Intelligence (AI) tools: <tool>.
Learning content created by <pembuat>.
Reviewed by <reviewer>.

<deskripsi>
```
Tanyakan **pembuat dan reviewer** setiap kompetensi baru (jangan pakai nama default). Tool default: Claude (video), NotebookLM (audio); konfirmasi bila konten dari pihak lain.

## Deskripsi video & audio: kalimat ajakan (2–3 kalimat)
1. Pertanyaan pemantik dari situasi yang dekat dengan peserta.
2. "Yuk, tonton video ini / dengarkan diskusi ini dan pahami/pelajari …" + poin utama konten.
3. "Mari …" ajakan penutup ke penerapan.
Contoh video: "Pernah menekan tombol lalu ragu apakah data sudah terkirim? Yuk, tonton video ini dan pahami fondasi user interface, mulai dari … hingga … . Mari mulai merancang dari kebutuhan pengguna melalui pendekatan human-centered design."
Isi diambil dari konten sebenarnya (script/VO sendiri, atau transkrip). Bahasa Indonesia baku, sapaan "Anda", tanpa emoji/hashtag. Gaya ajakan **hanya** untuk deskripsi video & audio.

## Alur A — konten dibuat sendiri (sesuai course design)
Sumber utama: **course design** (workbook ADDIE / course plan / tracker).
1. KB: `python3 "$SKILL/scripts/collect.py" kb <kode> <level>`.
2. Nama course & nama modul/topik: `python3 "$SKILL/scripts/collect.py" addie <design.xlsx> <level>` (sheet "Design-Topik"); atau dari tracker yang ditempel user.
3. Judul video/audio/artikel dan bahan deskripsi: dari file produksi sendiri (script/naskah VO, judul audio NotebookLM, artikel).
4. Tanyakan pembuat & reviewer, lalu lanjut ke **Bangun**.

## Alur B — konten dari pihak lain (folder atau link)
Input dari user: **kode kompetensi + level**, **folder/link konten per section**, **nama course per KB** (tidak ada di Dirkom maupun file konten; bila belum ada, kosongkan — kolom ditandai kuning — dan beri usulan nama ≤ 8 kata untuk dipilih), **pembuat & reviewer**.
1. KB: `collect.py kb <kode> <level>`. Section n → KB dan modul sesuai urutan (section 1 = KB1 · Modul 1 bila tidak ada keterangan lain; konfirmasi bila ragu).
2. Per section: `python3 "$SKILL/scripts/collect.py" folder "<folder section>"` → judul dari nama file video/audio (rapikan: buang nomor urut, "(1)", underscore), judul artikel dari heading dokumen, transkrip video & audio (HyperFrames transcribe, bahasa Indonesia; abaikan kalimat ulang/halusinasi di akhir transkrip).
3. Link: file di OneDrive/SharePoint tersinkron dibaca langsung; link lain dibuka/diunduh dengan izin user (sebut nama file, sumber, ukuran) ke folder kerja sementara, lalu proses seperti folder. Link yang perlu login: user login sendiri di browser.
4. Nama modul: dari course plan bila ada; jika tidak, dari nama file artikel ("Artikel modul_ … <judul>") atau judul artikel — konfirmasi ke user.
5. Lanjut ke **Bangun**.

## Bangun
1. Tulis data JSON seperti `examples/TC229_L1.json` (deskripsi tanpa kredit; `courses.<KB>.kb` = frasa KB).
2. **Sampel dulu** (satu section atau satu level), tunjukkan, minta persetujuan:
```bash
python3 "$SKILL/scripts/build_cms.py" build data.json "<folder kompetensi>/_CMS/CMS_<KODE>_<Kompetensi>.xlsx"
```
   `CEK:` memperingatkan kredit kosong, nama course kosong, KB yang masih berawalan kata kerja, deskripsi tanpa "Yuk/Mari", dan sisa tanda `[..]`. Selesaikan atau laporkan ke user.
3. Level berikutnya = sheet baru di file yang sama. Revisi: ubah JSON lalu `build` ulang; simpan salinan file lama sebelum menimpa.
4. Kirim file dan tabel ringkas isinya; tandai yang perlu dikonfirmasi user.

Format: header teal `#2796A3` teks putih tebal, teks rata atas dan wrap, border tipis, freeze kolom A & baris 1, sel wajib yang kosong berwarna kuning. Jangan ubah urutan kolom (dipakai untuk upload).
