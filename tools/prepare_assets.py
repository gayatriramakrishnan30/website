"""One-time asset preparation.

Copies media from the Notion export (../Notion) into static/, giving files clean
names, converting images to WebP (max 1600px) and rendering PDF first pages to
images. Run from the `website/` folder:

    python tools/prepare_assets.py

Safe to re-run; existing outputs are overwritten.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

try:
    import pymupdf  # PyMuPDF
except ImportError:  # pragma: no cover
    pymupdf = None

ROOT = Path(__file__).resolve().parent.parent          # website/
NOTION = ROOT.parent / "Notion" / "Private & Shared"
PORTFOLIO = next(NOTION.glob("Gayatri*Portfolio"), None)  # folder name has a curly apostrophe
if PORTFOLIO is None or not PORTFOLIO.is_dir():
    sys.exit(f"Notion export not found under {NOTION}")
PROJ = PORTFOLIO / "Projects"
CC = next(PROJ.glob("Content Creation*"))  # content-creation media folder (not the .md)
if CC.is_file():
    CC = next(p for p in PROJ.glob("Content Creation*") if p.is_dir())

STATIC = ROOT / "static"
MAX_W = 1600


def proj_dir(prefix: str) -> Path:
    return next(p for p in PROJ.iterdir() if p.is_dir() and prefix in p.name)


def to_webp(src: Path, dst: Path, max_w: int = MAX_W, quality: int = 82) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGBA") if im.mode in ("P", "LA") else im
        if im.mode == "RGBA":
            # flatten transparency onto white so WebP stays small and predictable
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=quality, method=6)
    print(f"  img  {dst.relative_to(ROOT)}")


def pdf_page(src: Path, dst: Path, page: int = 0, zoom: float = 2.0) -> None:
    if pymupdf is None:
        print(f"  SKIP (pymupdf missing) {src.name}")
        return
    tmp = dst.with_suffix(".png")
    with pymupdf.open(src) as doc:
        pix = doc[page].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        pix.save(tmp)
    to_webp(tmp, dst)
    tmp.unlink()


def redact(path: Path, boxes: list[tuple[int, int, int, int]], label: str | None = None,
           sample: str = "left") -> None:
    """Paint over boxes using a colour sampled just left of (or just inside) each box."""
    from PIL import ImageDraw, ImageFont

    with Image.open(path) as im:
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
        for x0, y0, x1, y1 in boxes:
            pt = (max(x0 - 4, 0), y0 + 2) if sample == "left" else (x0 + 12, y0 + 12)
            fill = im.getpixel(pt)
            d.rectangle((x0, y0, x1, y1), fill=fill)
            if label:
                try:
                    font = ImageFont.truetype("arialbd.ttf", 30)
                except OSError:
                    font = ImageFont.load_default()
                w = d.textlength(label, font=font)
                if w > x1 - x0 - 20:
                    words = label.split(", ")
                    for i, line in enumerate(words):
                        lw = d.textlength(line, font=font)
                        d.text((x0 + (x1 - x0 - lw) / 2, (y0 + y1) / 2 - 40 + i * 44), line, fill=(20, 40, 60), font=font)
                else:
                    d.text((x0 + (x1 - x0 - w) / 2, (y0 + y1) / 2 - 16), label, fill=(20, 40, 60), font=font)
        im.save(path, "WEBP", quality=82, method=6)
    print(f"  redacted {path.relative_to(ROOT)}")


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  copy {dst.relative_to(ROOT)}")


def main() -> None:
    img = STATIC / "img"
    media = STATIC / "media"

    print("Portrait")
    photo = PORTFOLIO / "Photo_GayatriRamakrishnan_1.jpg"
    to_webp(photo, img / "photo.webp", max_w=900, quality=85)
    with Image.open(photo) as im:
        im.convert("RGB").resize((900, 900), Image.LANCZOS).save(img / "photo.jpg", quality=85, optimize=True)
    print("  img  static/img/photo.jpg")

    print("Project images")
    projects = {
        "enhertu": (proj_dir("Enhertu"), "Screenshot_2025-06-27_194733.png"),
        "cold-chain": (proj_dir("Cold Chain"), "dashboard_screenshot.png"),
        "neurocrine": (proj_dir("Neurocrine"), "Screenshot_2025-06-27_225841.png"),
        "endolysa": (proj_dir("Endolysa"), "StrategicMarketing_EndoLysa.png"),
        "gutglow": (proj_dir("GutGlow"), "Screenshot_2025-10-31_082713.png"),
        "fda-ema": (proj_dir("FDA vs EMA"), "Regulatory_Affairs_EUvsUSA.png"),
        "bersync": (proj_dir("BerSync"), "bersync.png"),
        "flycarb": (proj_dir("Flycarb"), "Screenshot_2025-10-31_085749.png"),
        "sortsmart": (proj_dir("SortSmart"), "SmartSort1.png"),
    }
    for slug, (folder, name) in projects.items():
        to_webp(folder / name, media / "projects" / f"{slug}.webp")

    print("Creative: testblu")
    tb = {
        "testblu-dog-1": "SocialMedia_1.png",
        "testblu-dog-2": "SocialMedia_2.png",
        "testblu-dog-3": "SocialMedia_3.png",
        "testblu-event-dmea": "DMEA_2026.jpg",
        "testblu-event-june": "June_2026_Events.png",
        "testblu-event-gitex": "GITEX_Europe_2026.png",
        "testblu-service-1": "1.png",
        "testblu-service-2": "2.png",
        "testblu-service-3": "3.png",
        "testblu-service-4": "4.png",
        "testblu-service-5": "5.png",
        "misc-commercial-cofounder": "Commercial_Co-Founder.png",
        "misc-felmo-quote": "felmo_quote_1.png",
        "testblu-flyer-1": "Flyer_Page1.png",
        "testblu-flyer-2": "Flyer_Page2.png",
        "testblu-poster": "testblu_poster.png",
    }
    for out, name in tb.items():
        to_webp(CC / name, media / "creative" / f"{out}.webp")
    pdf_page(CC / "Events_April_2026.pdf", media / "creative" / "testblu-event-april.webp", zoom=1.5)

    print("Creative: Enactus")
    en = {
        "enactus-fun-fact": "Fair_bear_fun_fact.png",
        "enactus-new-semester": "Happy_New_semester.png",
        # Pitch event carousel
        "enactus-pitch-1": "2 1.png", "enactus-pitch-2": "4 1.png", "enactus-pitch-3": "6.png",
        "enactus-pitch-4": "8.png", "enactus-pitch-5": "10.png",
        # Why join carousel
        "enactus-join-1": "1 1.png", "enactus-join-2": "5 1.png", "enactus-join-3": "2 2.png",
        "enactus-join-4": "6 1.png", "enactus-join-5": "3 1.png", "enactus-join-6": "7.png",
        "enactus-join-7": "4 2.png",
        # World Cup carousel
        "enactus-worldcup-1": "1 2.png", "enactus-worldcup-2": "2 3.png",
        "enactus-worldcup-3": "3 2.png", "enactus-worldcup-4": "4 3.png",
        # Departments carousel
        "enactus-teams-1": "1 3.png", "enactus-teams-2": "5 2.png", "enactus-teams-3": "2 4.png",
        "enactus-teams-4": "6 2.png", "enactus-teams-5": "3 3.png", "enactus-teams-6": "7 1.png",
        "enactus-teams-7": "4 4.png", "enactus-teams-8": "8 1.png",
    }
    for out, name in en.items():
        to_webp(CC / name, media / "creative" / f"{out}.webp")
    copy(CC / "what_does_sustainability_mean_1.mp4", media / "creative" / "enactus-sustainability-reel.mp4")

    print("Creative: science communication")
    sc = {
        "scicomm-women-in-science": "IntlDayofWomenInSc_LinkedIn_FyoniBio_1.png",
        "scicomm-cell-cultivation": "CellCultivationSys_Visual_GreenElephantBiotech_GayatriRamakrishnan.png",
        "scicomm-zebrafinch-male": "b7a312e4-7d14-40f2-9bce-12fa541b06dd.png",
        "scicomm-zebrafinch-female": "020525af-7565-43f7-9852-195406895fd8.png",
        "scicomm-zebrafinch-song": "ZF_directedSong.png",
        "scicomm-smartsort": "SmartSort.png",
    }
    for out, name in sc.items():
        to_webp(CC / name, media / "creative" / f"{out}.webp")

    print("Creative: academic")
    copy(CC / "direct_carbonation_4step_titles.mp4", media / "creative" / "academic-direct-carbonation.mp4")
    copy(CC / "Gut_Health_Revelation.mp4", media / "creative" / "academic-gut-health.mp4")
    pdf_page(CC / "ALT_mindMap.pdf", media / "creative" / "academic-alt-mindmap.webp")
    copy(CC / "ALT_mindMap.pdf", STATIC / "docs" / "academic-alt-mindmap.pdf")
    # These two posters contain student roll numbers / an old email address (and classmates'
    # names + IDs), so only a redacted image is published, never the original PDF.
    pdf_page(CC / "lacOperon_Poster.pdf", media / "creative" / "academic-lac-operon.webp")
    redact(media / "creative" / "academic-lac-operon.webp", [
        (879, 52, 975, 84),     # "(192133)" roll number after the name
        (600, 112, 1010, 142),  # old student email line
    ])
    pdf_page(CC / "SCT_infographic.pdf", media / "creative" / "academic-stem-cell-therapy.webp")
    redact(media / "creative" / "academic-stem-cell-therapy.webp", [
        (1150, 2010, 1597, 2250),  # group members' names + roll numbers
    ], label="Group project, St. Xavier's College", sample="inside")
    for stale in ("academic-lac-operon.pdf", "academic-stem-cell-therapy.pdf"):
        (STATIC / "docs" / stale).unlink(missing_ok=True)

    print("Writing")
    blog = proj_dir("Blog writing")
    pdf_page(blog / "CellCultivationSys_GayatriRamakrishnan.pdf", media / "creative" / "writing-cell-cultivation.webp")
    copy(blog / "CellCultivationSys_GayatriRamakrishnan.pdf", STATIC / "docs" / "writing-cell-cultivation.pdf")

    print("Certificates (public ones only; the Enactus certificate shows date of birth, so it is not published)")
    copy(PORTFOLIO / "SciXplore_Certificate.pdf", STATIC / "docs" / "certificate-scixplore.pdf")
    copy(PORTFOLIO / "SummerSchool_Certificate.pdf", STATIC / "docs" / "certificate-tu-berlin-summer-school.pdf")

    print("Done.")


if __name__ == "__main__":
    main()
