# Gayatri Ramakrishnan: portfolio website

The source for **https://gayatriramakrishnan30.github.io**.

Every time you save a change to GitHub, the site rebuilds and goes live by itself, usually within about a minute. You never edit HTML. All the text lives in a few plain files in `content/`.

---

## Where everything lives

| What you want to change | File |
|---|---|
| Headline, intro, numbers strip, about text, education, skills, languages, certifications, "beyond work" | `content/site.yaml` |
| Jobs and roles (the experience timeline) | `content/experience.yaml` |
| A project or case study | `content/projects/<name>.md` (one file per project) |
| The creative gallery (designs, videos, writing) | `content/creative.yaml` |
| Images, PDFs, videos | `static/media/…`, `static/docs/…` |
| Colours and fonts | `static/css/style.css` (the `:root` section at the top) |

You don't normally need to touch the `templates/` folder (page layouts) or `build.py`.

### Editing tips
- **YAML files** (`.yaml`): keep the indentation exactly as it is, using spaces, never tabs. Lines that start with `#` are notes and never appear on the site. If a line contains a colon `:`, wrap the text in quotes.
- **Project files** (`.md`): the block between the two `---` lines holds the settings (title, summary, tags…). Everything below it is the case-study text in Markdown: `## Heading`, `- bullet`, `**bold**`, `[link text](https://…)`.

### Common tasks

**Change a job or add a new one.** Open `content/experience.yaml` and copy an existing role block, including its `- id:` line. Give it a new unique `id`, then edit it.

**Add a project.** Copy any file in `content/projects/`, rename it (e.g. `my-new-project.md`; the file name becomes the web address), and edit the settings:
- `functions` is any of `strategy`, `bd`, `analytics`, `regulatory`, `marketing`. These drive the filters on the Work page.
- `featured: true` puts the project on the home page. Keep it to about 6.
- `order` sets the position (lower numbers come first).
- `has_page: false` with `link: /#exp-…` makes a card that points to a timeline entry instead of its own page.
- `image` is optional; add the picture under `static/media/projects/`.
- `draft: true` hides the project without deleting it.

**Add a downloadable CV.** Put a PDF *without your phone number* at `static/docs/cv.pdf` and set `cv: /static/docs/cv.pdf` in `site.yaml`. A "CV" button then appears in the hero.

**Change your photo or headline.** Replace `static/img/photo.jpg` and `photo.webp` (square or portrait). Then run `python tools/make_og.py` on your computer to refresh the LinkedIn preview image.

---

## Editing directly on github.com (no software needed)
1. Open the repository on github.com and click into the file you want, e.g. `content/experience.yaml`.
2. Click the pencil icon (Edit), make the change, then click **Commit changes**.
3. Check the **Actions** tab: a green tick means the site is live. A red cross means something in the file couldn't be read, often the YAML indentation. Click the run to see which file is at fault.

## Editing on your computer (with a preview)
One-time setup: install Python, then run `pip install -r requirements.txt` in this folder.

```
python build.py --serve
```
Open http://localhost:8000 to see the site, and press Ctrl+C to stop. The build also checks every internal link and tells you if one is broken. When you're happy, publish with **GitHub Desktop**: write a short summary, click **Commit to main**, then **Push origin**.

---

## One-time setup (first publish)
1. Install **GitHub Desktop** (desktop.github.com) and sign in as `gayatriramakrishnan30`.
2. *File → Add local repository* → choose this `website` folder → when asked, click **create a repository**. Then click **Publish repository**, name it exactly `gayatriramakrishnan30.github.io`, and **untick "Keep this code private"**.
3. On github.com, open the repository → **Settings → Pages** → under *Build and deployment*, set **Source: GitHub Actions**.
4. Open the **Actions** tab and wait for the green tick, then visit https://gayatriramakrishnan30.github.io.
5. Paste the link into https://www.linkedin.com/post-inspector/ to check the preview card. Then add it to LinkedIn: *Edit intro → Website*, and/or the *Featured* section.

## Privacy notes
- The site shows only your Gmail, LinkedIn and GitHub. The phone number and student email are deliberately left out.
- The Enactus certificate shows your date of birth, so it isn't published (it's listed as "available on request"). The lac operon poster and stem-cell infographic images have roll numbers, an old email and classmates' IDs redacted, and their original PDFs aren't published.
- Fonts are self-hosted (no Google Fonts requests), and there are no cookies or analytics.

## Tools
- `tools/prepare_assets.py`: one-time import of media from the old Notion export (`../Notion`). Only needed again if you re-export from Notion.
- `tools/make_og.py`: regenerates `static/img/og-image.png`, the LinkedIn/social preview card.
