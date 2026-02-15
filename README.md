# 🔬 Katman Portal — GA4 Analytics Pipeline

**katmanportal.com** web sitesi için uçtan uca analitik veri toplama ve görselleştirme pipeline'ı.

Bu proje, [Katman Portal](https://katmanportal.com) web sitesinin tüm sayfalarını tarar, Google Analytics 4 (GA4) API'den trafik verilerini çeker ve interaktif HTML dashboard'lar oluşturur.

---

## 📁 Proje Yapısı

```
Katman/
├── find_property_id.py      # GA4 Property ID bulma aracı
├── analytics_helper.py      # GA4 API wrapper (veri çekme)
├── katman_full_crawler.py   # Website crawler (sitemap + BFS)
├── generate_report.py       # HTML dashboard oluşturucu
├── requirements.txt         # Python bağımlılıkları
├── .gitignore               # Git hariç tutma kuralları
│
├── Crawled_Data/            # (üretilir) İndirilen HTML sayfaları
├── data_cache/              # (üretilir) GA4 API önbelleği (.pkl)
├── exported_data/           # (üretilir) Parquet & Excel çıktılar
└── dashboard/               # (üretilir) HTML dashboard dosyaları
```

---

## 🧱 Gereksinimler

### Yazılım
- **Python 3.10+**
- Paketler: `requirements.txt` dosyasına bakınız

### Google Analytics 4 Erişimi
1. Bir **Google Cloud projesi** oluşturun
2. **Google Analytics Data API v1** ve **Google Analytics Admin API** hizmetlerini etkinleştirin
3. **Service Account** oluşturun ve JSON anahtarını indirin
4. Service Account e-posta adresini GA4 property'sine **Okuyucu** (Viewer) olarak ekleyin

> ⚠️ **Güvenlik**: Service account JSON dosyasını (`*.json`) **asla** GitHub'a yüklemeyin. Bu dosya `.gitignore` ile hariç tutulmuştur.

---

## 🚀 Kurulum

### 1. Repoyu Klonlayın

```bash
git clone https://github.com/katmanportal1/trafik.git
cd trafik
```

### 2. Sanal Ortam Oluşturun (Önerilir)

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Service Account Anahtarını Yerleştirin

Google Cloud Console'dan indirdiğiniz JSON dosyasını proje kök dizinine koyun. Dosya adını scriptlerde güncelleyin:

```python
# analytics_helper.py ve find_property_id.py içinde:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "SIZIN_SERVICE_ACCOUNT.json"
```

### 5. Property ID'yi Bulun

```bash
python find_property_id.py
```

Çıktıda görünen Property ID'yi `analytics_helper.py` dosyasındaki `PROPERTY_ID` değişkenine yazın:

```python
PROPERTY_ID = "SIZIN_PROPERTY_ID"
```

---

## 📖 Kullanım

Pipeline **sıralı** olarak aşağıdaki adımları içerir:

### Adım 1: Web Sitesini Tarayın

```bash
python katman_full_crawler.py
```

**Ne yapar?**
- `katmanportal.com/sitemap.xml` adresinden sayfa URL'lerini çeker
- BFS (Breadth-First Search) ile tüm iç linkleri takip eder
- Her sayfanın HTML'ini `Crawled_Data/` klasörüne kaydeder
- Sayfa meta verilerini (başlık, yazar, kategori) `katman_crawled_index.xlsx` dosyasına yazar

**Çıktılar:**
| Dosya/Klasör | Açıklama |
|---|---|
| `Crawled_Data/*.html` | İndirilen HTML sayfaları |
| `katman_crawled_index.xlsx` | Sayfa index'i (URL, başlık, yazar, kategori) |
| `crawler.log` | Crawl işlem kaydı |

### Adım 2: GA4 Verilerini Kontrol Edin

```bash
python analytics_helper.py
```

**Ne yapar?**
- GA4 API bağlantısını test eder
- Son 30 günün trafik verilerini çeker
- Ülke ve şehir bazlı dağılımı gösterir
- Verileri `exported_data/` klasörüne kaydeder

**Çıktılar:**
| Dosya/Klasör | Açıklama |
|---|---|
| `exported_data/*.xlsx` | Grup bazlı Excel raporları |
| `exported_data/*.parquet` | Grup bazlı Parquet dosyaları |
| `data_cache/*.pkl` | API yanıt önbelleği |

### Adım 3: Dashboard Oluşturun

```bash
python generate_report.py
```

**Ne yapar?**
- GA4'ten yıllık ve aylık trafik verileri çeker
- Plotly ile interaktif grafikler oluşturur
- Bootstrap tabanlı HTML dashboard sayfaları üretir
- Her ay ve yıl için ayrı sayfa oluşturur

**Çıktılar:**
| Dosya | Açıklama |
|---|---|
| `dashboard/index.html` | Ana dashboard sayfası |
| `dashboard/katman_dashboard_2025.html` | 2025 yıllık rapor |
| `dashboard/katman_dashboard_2025_01.html` | Ocak 2025 aylık rapor |
| ... | Her ay için ayrı HTML dosyası |

> 💡 `dashboard/index.html` dosyasını tarayıcıda açarak dashboard'u görüntüleyebilirsiniz.

---

## 🔧 Script Detayları

### `find_property_id.py`
GA4 hesabınızdaki tüm property'leri listeler. İlk kurulumda Property ID'yi bulmak için kullanılır.

### `analytics_helper.py`
`AnalyticsHelper` sınıfı ile GA4 API'ye erişim sağlar:

| Metot | Açıklama |
|---|---|
| `get_daily_traffic()` | Günlük oturum ve kullanıcı sayıları |
| `get_top_pages()` | En çok görüntülenen sayfalar |
| `get_countries()` | Ülke bazlı trafik dağılımı |
| `get_tr_cities()` | Türkiye şehir bazlı trafik |
| `get_traffic_sources()` | Trafik kaynakları |
| `get_grouped_top_pages()` | Kategori bazlı en popüler sayfalar |
| `get_grouped_monthly_pages()` | Kategori bazlı aylık trafik |
| `get_downloads()` | Dosya indirme istatistikleri |

Tüm API yanıtları `data_cache/` klasöründe `.pkl` olarak önbelleklenir.

### `katman_full_crawler.py`
Asenkron (asyncio + aiohttp) hibrit crawler:
- **Sitemap seed**: Bilinen URL'lerden başlar
- **BFS discovery**: Sayfadaki iç linkleri takip eder
- Paralel indirme (`CONCURRENCY=10`)
- Otomatik fragment/duplicate temizleme

### `generate_report.py`
`ReportGenerator` sınıfı ile HTML dashboard üretir:
- Plotly.js grafikleri (çizgi, pasta, bar)
- Bootstrap 5 sayfa düzeni
- Sidebar navigasyon (yıl/ay seçimi)
- Kategori bazlı detay tabloları

---

## 📊 Kategori Grupları

Dashboard aşağıdaki Katman Portal kategorilerini izler:

| Grup | URL Prefix |
|---|---|
| Güncel | `/category/guncel` |
| Dünya | `/category/dunya` |
| Türkiye | `/category/turkiye` |
| Eşitsizlik | `/category/esitsizlik` |
| İklim | `/category/iklim` |
| Sanayi | `/category/sanayi` |
| Bölüşüm | `/category/bolusum` |
| Teori | `/category/teori` |
| Makro Politika | `/category/makro-politika` |
| Para & Finans | `/category/parafinans` |
| Maliye | `/category/maliye` |
| Sosyal Politika | `/category/sosyalpolitika` |
| Metodoloji | `/category/metodoloji` |
| Tarih | `/category/tarih` |
| Küresel | `/category/kuresel` |
| Kitap Tanıtım | `/category/kitap-tanit` |

---

## 🔄 Tekrarlanabilirlik

Başka birinin bu pipeline'ı çalıştırması için:

1. **Google Cloud** hesabı oluşturun ve API'leri etkinleştirin
2. **Service Account** oluşturup JSON anahtarını indirin
3. GA4 property'sine service account'u ekleyin
4. Bu repoyu klonlayıp bağımlılıkları yükleyin
5. JSON dosya adını ve Property ID'yi güncelleyin
6. Scriptleri sırasıyla çalıştırın: `find_property_id.py` → `katman_full_crawler.py` → `analytics_helper.py` → `generate_report.py`

---

## 📜 Lisans

Bu proje eğitim ve araştırma amaçlıdır.

---

## 📬 İletişim

Sorularınız için: [katmanportal.com/iletisim](https://katmanportal.com/iletisim)
