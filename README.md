<div align="center">

# ВАРТА /// VARTA

### Real-Time Tactical Surveillance for Ukraine

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg?style=flat-square)](LICENSE)
[![Single File](https://img.shields.io/badge/Single_HTML_File-00ff88.svg?style=flat-square)](#quick-start)
[![No Setup](https://img.shields.io/badge/No_Setup_Required-ff2952.svg?style=flat-square)](#quick-start)
[![6 Sources](https://img.shields.io/badge/6_Live_Data_Sources-ffb020.svg?style=flat-square)](#data-sources)

<br>

<img src="assets/screenshot.png" alt="VARTA Dashboard" width="900">

<br>

*A military command center in your browser — monitoring Ukraine's airspace, frontlines, and threats in real time.*

<br>

[**Live Demo**](https://clmrie.github.io/varta) · [Report Bug](https://github.com/clmrie/varta/issues) · [Request Feature](https://github.com/clmrie/varta/issues)

</div>

---

## What is VARTA?

**VARTA** (*Варта* — Ukrainian for "The Guard") is a live dashboard that tracks the war in Ukraine from **6 independent sources** — and displays everything on a single interactive map.

Air raid sirens. Russian frontline positions. Fires detected from space. Earthquake sensors. Air pollution. Breaking news. All updating automatically, all in one place, all free to use.

---

## Features

<table>
<tr>
<td width="50%">

### 🛰️ Fires Detected from Space
Uses NASA satellite imagery to spot active fires and thermal anomalies across Ukraine — including infrastructure hits and explosions visible from orbit.

### 📡 Live Air Raid Alerts
Tracks active sirens across all 26 Ukrainian oblasts in real time. Color-coded by severity. Precise down to individual cities.

### 🔴 Russian Frontline Positions
Shows exactly where Russian-occupied territory is, updated daily from [DeepStateMap](https://github.com/cyterat/deepstate-map-data). Bright red borders mark the frontline.

</td>
<td width="50%">

### 🌍 Earthquake & Explosion Detection
Monitors seismic activity across Ukraine using US Geological Survey sensors — helping distinguish natural earthquakes from military explosions.

### 🌫️ Air Quality After Strikes
Tracks air pollution levels (PM2.5 and PM10) across 6 major cities. Critical for understanding the environmental impact of attacks.

### 📰 Live Breaking News
Automatically pulls English-language news from major Ukrainian outlets, sorted by urgency. Click any headline to read the full article.

</td>
</tr>
</table>

### Plus...

- **🔗 Smart Alert Correlation** — When satellites detect fire in a region that also has active sirens and seismic activity, VARTA automatically flags it as a confirmed strike
- **🔔 Desktop Notifications** — Get notified instantly when something critical happens
- **🔊 Audio Warnings** — Audible alert tones for high-severity events
- **🗺️ City-Level Precision** — 48 Ukrainian cities mapped with exact coordinates
- **💾 Remembers Your Settings** — Your preferences are saved between visits
- **📱 Works on Any Screen** — Desktop, tablet, or phone

---

## Data Sources

| What | Source | Updates |
|------|--------|---------|
| **Air Raid Alerts** | [alerts.in.ua](https://alerts.in.ua) | Real-time |
| **News** | [Ukrainska Pravda](https://www.pravda.com.ua/eng/) + [UNIAN](https://www.unian.net/) | Every refresh |
| **Satellite Fires** | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) | Every 3–6 hours |
| **Seismic Activity** | [USGS](https://earthquake.usgs.gov/) | Real-time |
| **Air Quality** | [Open-Meteo](https://open-meteo.com/) | Every 15 minutes |
| **Frontline** | [DeepStateMap](https://github.com/cyterat/deepstate-map-data) | Daily |

All data comes from **free, publicly available sources**. No accounts or setup needed.

---

## Quick Start

```bash
git clone https://github.com/clmrie/varta.git
open varta/index.html
```

That's it. Open the file in any browser and you're live.

Want to share it? Deploy it on **GitHub Pages** for free:

1. Fork this repo
2. Go to **Settings → Pages**
3. Set source to **Deploy from branch → `main` → `/ (root)`**
4. Your dashboard is now live at `https://yourusername.github.io/varta`

---

## Disclaimer

> VARTA aggregates publicly available data for **informational purposes only**. It is not a military system. Data accuracy depends on upstream providers (alerts.in.ua, NASA, USGS, DeepStateMap). Frontline positions are approximate and updated daily. **Do not make safety-critical decisions based solely on this dashboard.** Always follow official instructions from Ukrainian authorities.

---

## License

[MIT](LICENSE) — Free to use, modify, and share.

---

<br>

<div align="center">

# 🇺🇦 Українською

</div>

## Що таке ВАРТА?

**ВАРТА** — це інтерактивна панель моніторингу, яка відстежує війну в Україні в реальному часі з **6 незалежних джерел** — і відображає все на одній карті.

Повітряні тривоги. Позиції російського фронту. Пожежі, виявлені з космосу. Сейсмічні датчики. Якість повітря. Останні новини. Все оновлюється автоматично, все в одному місці, все безкоштовно.

---

## Можливості

<table>
<tr>
<td width="50%">

### 🛰️ Пожежі з космосу
Супутники NASA виявляють активні пожежі та термальні аномалії по всій Україні — включаючи удари по інфраструктурі та вибухи, видимі з орбіти.

### 📡 Повітряні тривоги
Відстежує активні сирени у всіх 26 областях у реальному часі. Кольорове кодування за рівнем загрози. Точність до окремих міст.

### 🔴 Позиції російського фронту
Щоденне оновлення окупованих територій з [DeepStateMap](https://github.com/cyterat/deepstate-map-data). Яскраво-червоні лінії позначають лінію фронту.

</td>
<td width="50%">

### 🌍 Землетруси та вибухи
Моніторинг сейсмічної активності за допомогою датчиків Геологічної служби США — допомагає відрізнити природні землетруси від військових вибухів.

### 🌫️ Якість повітря після ударів
Відстежує рівень забруднення повітря (PM2.5 та PM10) у 6 великих містах. Важливо для оцінки екологічних наслідків атак.

### 📰 Стрічка новин
Автоматично збирає англомовні новини з основних українських видань, відсортовані за терміновістю. Натисніть на заголовок, щоб прочитати повну статтю.

</td>
</tr>
</table>

### А також...

- **🔗 Розумна кореляція** — Коли супутники виявляють пожежу в регіоні, де також є активна тривога і сейсмічна активність, ВАРТА автоматично позначає це як підтверджений удар
- **🔔 Сповіщення на робочий стіл** — Миттєве повідомлення про критичні події
- **🔊 Звукові сигнали** — Для подій високого рівня загрози
- **🗺️ Точність до міста** — 48 українських міст з точними координатами
- **💾 Запам'ятовує налаштування** — Ваші параметри зберігаються між візитами
- **📱 Працює на будь-якому екрані** — Комп'ютер, планшет чи телефон

---

## Швидкий старт

```bash
git clone https://github.com/clmrie/varta.git
open varta/index.html
```

Це все. Відкрийте файл у будь-якому браузері — і панель моніторингу працює.

---

## Застереження

> ВАРТА збирає загальнодоступні дані **виключно з інформаційною метою**. Це не військова система. Точність даних залежить від постачальників (alerts.in.ua, NASA, USGS, DeepStateMap). Позиції фронту є приблизними та оновлюються щодня. **Не приймайте рішень щодо безпеки виключно на основі цієї панелі.** Завжди дотримуйтесь офіційних вказівок українських органів влади.

---

<div align="center">

🇺🇦

**Слава Україні!**

*Створено з відкритими даними та відкритими серцями.*

<sub>ВАРТА — "The Guard" — Стоїть на варті, щоб вам не довелося.</sub>

</div>
