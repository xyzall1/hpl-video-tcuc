# House style: Telkom CorpU storytelling learning videos

## Look
- **White-dominant.** Background `#F6F8F9` with a faint dot grid. Cards are white with a `#DDE5EA` border and a soft shadow, radius 14–22 px.
- **Palette:** ink `#1D2B36`, muted `#8A99A6`, primary teal `#2796A3` (the same colour as the subtitle pill), light teal `#7CC6CE`, pale `#E8F4F5`. Accents are used sparingly: amber `#F2A541` for a highlight or the "floating" element, red `#E25C5C` for failures and ≠.
- **Type:** Plus Jakarta Sans for motion graphics (800 for headlines, 700 for labels). Headline 64–76 px, big numbers 110–300 px, pill text 34 px. Tag labels are uppercase teal, letter-spacing .14em.
- **Scene images** (hand-drawn stick-figure scenes) are shown full-frame, cover-scaled, with a 350 ms crossfade and a slow 5 % push-in.

## Motion
- Entrances use `popIn` (back.out) for objects and `rise` (power3.out) for text. Scene fades are 0.35 s.
- Land each key reveal on the spoken word it illustrates (use times from `timing.json`).
- One idea per beat. Change the visual at least every ~4 s. Keep text on screen long enough to read (≥ 1.5 s after it finishes entering).
- Typical beat recipes: count-up number; grid of mini-chart tiles (`miniTile` kinds 0 = bars, 1 = line, 2 = pie, 3 = table); a lens or highlight over a crowd; a mock dashboard with a cursor click and ripple that updates linked charts; before/after (15 → 9); a triangle for trade-offs; ≠ cards for inconsistency; a loading bar with a timer; laptop → phone.

## Layout zones (1920×1080 canvas)
- Title zone: y 90–230, left-aligned at x 120–160, or centred.
- Content: y 250–880.
- **Subtitle zone: y ≥ 940. Keep motion-graphic content out of it.** Bottom pills in the motion graphics sit at `top: 830px`.

## Subtitle preset (fixed for this series)
- Pill background `#2796A3`, text `#FFFFFF`, fully rounded (radius = height / 2).
- Poppins Bold 44 px ("scale 60 %"), pill height 76, horizontal padding 38. Centred horizontally, pill centre at y = 1000.
- At most one line: split sentences at commas, then balance on words, max ~56 characters.
- Keep the pill up through the breathing pause until the next cue starts.
- Correct typos and capitalise names ("Bagas"). Never change the spoken meaning.

## Structure
Bumper In (with its audio) → VO section → Bumper Out (with its audio). Output 16:9, 1280×720, 30 fps.

## Pacing
Breathing pauses: +0.4 s between sentences and +1.0 s at a paragraph or topic change. The speaking rate itself is never changed.
