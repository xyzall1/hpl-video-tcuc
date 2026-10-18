---
name: hpl-thumbnail
description: Buat thumbnail konten HPL/Telkom CorpU — cover kompetensi, cover course, thumbnail video & artikel (16:9, 1920×1080) dan thumbnail audio (1:1, 1080×1080) — sesuai deck Thumbnail_HPL_16x9.pptx / Thumbnail_HPL_1x1_Audio.pptx, dengan judul diambil dari workbook CMS. Gunakan saat diminta "buat thumbnail", "cover course", "cover kompetensi", "thumbnail video/artikel/audio", atau batch thumbnail per level.
---

# Thumbnail HPL

Skill root = folder file ini (`$SKILL`). Render memakai HyperFrames snapshot (`npx hyperframes snapshot`), jadi butuh Node + hyperframes seperti skill video.

## Aturan desain (dari deck user)
- **Ukuran:** 16:9 1920×1080 untuk cover kompetensi, cover course, video, artikel. 1:1 1080×1080 untuk audio.
- **Warna per level = kecerahan background** (aturan user): Fundamental = **terang kedua**, Intermediate = **paling gelap**, Developing = paling terang. (Deck sendiri memakai yang paling terang untuk Fundamental — aturan user yang dipakai.)
- **Teks:** Arial Bold putih + bayangan. Label berwarna terang dari palet (mis. #FCD34D untuk kuning), huruf kapital, letter-spacing lebar. Ukuran judul: cover 46pt, course 40pt, konten 32pt; audio 23pt rata tengah di bawah.
- **Ornamen per kompetensi = pilihan user, disebut dengan nama:** cincin, diagram, grafik, heksagon, kubus, orbit, panah, piramida, sarang, satelit, tabung, target, tumpukan (`--ornament=<nama>`). Semuanya diambil persis dari deck (`ornaments.json`) dan punya versi 16:9 serta 1:1, jadi thumbnail audio otomatis memakai ornamen yang sama. Pratinjau: `$SKILL/ornaments_preview.jpg`.
- **Untuk kompetensi baru, tanyakan warna dan ornamen sekaligus** dalam satu pertanyaan singkat, misalnya "Mau warna dan ornamen apa? Warna: kuning, tosca, biru, ungu, hijau, pink. Ornamen: cincin, diagram, grafik, heksagon, kubus, orbit, panah, piramida, sarang, satelit, tabung, target, tumpukan." Kirim `ornaments_preview.jpg` bersama pertanyaan itu karena nama ornamen sulit dibayangkan. Catat pilihan di memori supaya tidak ditanya ulang.
- Pengecualian lama: TC262 Strategic Media Planning = kuning, ornamen heksagon untuk 16:9 dan tumpukan untuk audio (`--audio-ornament=tumpukan`), karena sudah terlanjur dibuat begitu.
- **Warna per kompetensi = pilihan user, disebut dengan nama warna:** **kuning, tosca, biru, ungu, hijau, pink** (`--palette=<nama>`; alias: oranye = kuning, biru muda = tosca, merah muda = pink). Sebut warna dengan nama saja, tanpa kode hex atau tabel. Satu kompetensi = satu warna di semua level. Pratinjau semua warna × level ada di `$SKILL/palettes_preview.jpg` (kirim hanya bila user minta lihat).
- Catatan teknis: background per warna di `bg/<amber|cyan|blue|violet|emerald|rose>_<bright|mid|dark>.jpg` (+ `sq_` untuk 1:1); ornamen = warna utama, label = warna terangnya. Cyan dark dan emerald 1:1 bright/mid dibuat dari varian lain warna yang sama karena tidak ada di deck.
- Judul tidak dipotong di tanda hubung (kata seperti "Output-nya" tetap utuh).

## Sumber judul (workbook CMS, satu sheet per level)
| Thumbnail | Isi |
|---|---|
| Cover kompetensi | label = nama level (FUNDAMENTAL/DEVELOPING/INTERMEDIATE), judul = nama kompetensi |
| Cover course n | label = `COURSE n – <KOMPETENSI>`, judul = kolom **Course Design** (urutan kemunculan) |
| Video | kolom **Judul Video** |
| Artikel | kolom **Judul Artikel** |
| Audio (1:1) | kolom **Judul Audio** |
Kolom **LU** berformat `KB1 · Modul 1`. Jangan mengetik ulang judul; selalu baca dari workbook supaya ejaan sama.

## Penamaan file
`<KODE>_L<n>_00_Cover Kompetensi - <Kompetensi> (<Level>).png`
`<KODE>_L<n>_0<k>_Cover Course <k> - <Course Design>.png`
`<KODE>_L<n>_KB<k>_M<m>_{Video|Artikel|Audio} - <Judul>.png`
Tanda `: / ? \ * " < > |` dibuang dari nama file (judul di gambar tetap utuh). Simpan per level: `_thumbnail/out/L1`, `L2`, `L3`.

## Langkah
1. Pastikan workbook CMS punya kolom di atas, lalu tanyakan warna dan ornamen kompetensi (lihat Aturan desain) bila belum pernah dipilih.
2. Kerjakan **satu level dulu** (user biasanya minta begitu), lalu tunjukkan contact sheet:
```bash
python3 "$SKILL/scripts/batch_from_cms.py" <CMS.xlsx> "TC262 L1" fundamental TC262_L1 "Strategic Media Planning" _thumbnail/out/L1 --palette=kuning --ornament=heksagon --audio-ornament=tumpukan
```
3. Lihat contact sheet (`_thumbnail/out/TC262_L1_contact_sheet.jpg`): judul tidak terpotong/keluar kotak, label benar, background sesuai level. Kirim ke user dan daftar nama file **per LU** (cover course di awal tiap KB; video, artikel, audio per LU).
4. Setelah disetujui, lanjut level berikutnya dengan level/sheet/kode yang sesuai.

Satu thumbnail saja:
```bash
python3 "$SKILL/scripts/make_thumb.py" out.png <fundamental|developing|intermediate> <nama ornamen> "<Judul>" ["<LABEL>"] [--size=cover|course|content] [--format=square] [--palette=kuning|tosca|biru|ungu|hijau|pink]
```
Untuk membantu user mencari file, gunakan reveal di Finder dan sebutkan kata kunci pencarian (mis. `Cover Course`, `KB3_M2`).
