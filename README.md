# 📦 Discoverium Bridge

Discoverium Bridge is an automated, community-driven pipeline that bridges standard GitHub APK releases with the Discoverium Android app. 

It automatically parses GitHub repositories, extracts Android package metadata (like Package IDs and Icons), and generates Discoverium-compatible JSON configurations hosted on a static API.

🌐 **[View the Live Repo Browser](https://discoverium.repo.hamo.dev/)**

---

## 🛠️ How it Works

1. **The Engine:** A Python bot runs daily (or whenever triggered) via GitHub Actions.
2. **The Extraction:** It downloads the latest APKs, uses Android's `aapt` to extract metadata and rasterized icons, and builds JSON configurations.
3. **The API:** Data is saved to the `website/public/data` directory, automatically serving as a static, cache-busting API.
4. **The Frontend:** The frontend website consumes this API to provide a seamless browsing experience with 1-click "Add to Obtainium" support.

---

## ➕ How to Add an App

Want to see your favorite open-source Android app added to the browser? 

1. Fork this repository.
2. Open the `track_repos.txt` file in the root directory.
3. Add the GitHub repository path (e.g., `author/repo`) to a new line.
4. Submit a Pull Request!

Once merged, our automated GitHub Action will instantly fetch the APKs, extract the metadata, and publish the app to the live website.

---

## 📂 Project Architecture

- `/scripts/` — The Python backend engine and APK parsers.
- `/website/` — The frontend HTML/JS/CSS.
- `/website/public/data/` — The automatically generated static API and extracted app icons.
- `.github/workflows/` — CI/CD pipelines that tie everything together.