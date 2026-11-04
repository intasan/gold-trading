# Gold Trading Analytics

ระบบ ETL และ Dashboard สำหรับงานวิจัยข้อมูลราคาทองคำ **รันด้วยข้อมูลจริงแล้วบน SQLite** พร้อมการทดลอง ML แบบเรียงเวลา ไม่ใช่ระบบซื้อขายอัตโนมัติ

[เปิด Dashboard](https://intasan.github.io/gold-trading/) · [Verified scope](docs/VERIFIED_SCOPE.md) · [แหล่งข้อมูล](docs/DATA_SOURCES.md) · [Model card](docs/MODEL_CARD.md)

## สิ่งที่ทำงานได้จริง

- ดึง World Bank Pink Sheet: Gold / Silver / Platinum แบบ **monthly average, USD/troy oz**
- ดึง Gold API: XAU / XAG แบบ **spot quote** พร้อมเวลาที่ Provider อัปเดต
- ดึง Frankfurter: **USD/THB daily reference rate** แยกจากราคาทองไทย
- ตรวจ unit, instrument, date, positive/finite price และ key ก่อน transactional UPSERT
- แหล่งหนึ่งล้มเหลวไม่ทำลายข้อมูลเดิม; สถานะเป็น partial / failed ตามผลจริง
- Database → JSON/CSV export → Dashboard พร้อมตัวกรองโลหะ/ช่วงเวลา ตาราง CSV และสถานะ Pipeline
- Optional local Python API อ่านฐานข้อมูลโดยตรง; หน้า Pages อ่าน snapshot ที่ Export แล้ว ไม่ได้สตรีมราคาสด
- Feature engineering จากข้อมูลก่อนหน้า และ expanding-window ML evaluation เทียบ naive baseline

ผลรอบที่ตรวจ: 2,406 observations (ประวัติ 801 เดือน × 3 โลหะ + spot 2 รายการ + FX 1 รายการ). จำนวนนี้เป็น snapshot ของรอบที่บันทึก ไม่ใช่จำนวนสดตลอดเวลา

**ML ไม่ชนะ baseline:** holdout 36 เดือน, MAE model ≈133.60 เทียบ naive ≈129.53 USD/troy oz. จึงไม่ promote และไม่เผยแพร่ point forecast ดูตัวเลขจริงและช่วงทดสอบใน [model-evaluation.json](evidence/model-evaluation.json). ไม่อ้างว่าสามารถทำกำไรหรือพยากรณ์ Spot ได้

## เริ่มรัน (Python 3.12)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m goldtrading refresh
python -m goldtrading inspect
python -m goldtrading serve
```

เปิด `http://127.0.0.1:8000/` สำหรับ snapshot หรือ `http://127.0.0.1:8000/?mode=api` สำหรับการอ่าน DB ผ่าน API

คำสั่งแยกแต่ละขั้น:

```bash
python -m goldtrading ingest
python -m goldtrading model
python -m goldtrading export
```

ใช้ `--db` **ก่อน**ชื่อคำสั่ง เช่น `python -m goldtrading --db data/other.db refresh`. `DATABASE_URL` รองรับ SQLite path หรือ PostgreSQL URL; อย่าใส่ข้อมูลลับใน Git

หาก network ไม่พร้อม ใช้ข้อมูลจริงที่บันทึกไว้โดยระบุว่าเป็น Replay:

```bash
python -m goldtrading --db data/replay.db replay
python -m goldtrading --db data/replay.db model
python -m goldtrading --db data/replay.db export
```

Replay ไม่ใช่การดึงข้อมูลสด และไม่มีการสร้างราคาเติมช่องว่าง

## PostgreSQL / Docker (มี Source แต่ยังไม่รันใน Work รอบนี้)

```bash
cp .env.example .env
# Windows: copy .env.example .env
# ตั้ง POSTGRES_PASSWORD เป็นรหัสสุ่มแบบ URL-safe ใน .env
# ห้าม commit .env
docker compose up -d postgres
docker compose run --rm pipeline
docker compose up -d dashboard
```

เปิด `http://127.0.0.1:8000/?mode=api`. ใช้ named volumes เก็บ Postgres และ raw/export data. หากใช้ password ที่มี reserved URL characters ต้อง encode ให้ถูกต้องก่อนสร้าง DATABASE_URL. ห้ามใช้ `docker compose down -v` หากต้องเก็บข้อมูล

## Airflow (Optional / ยังไม่ทดสอบ Runtime)

`dags/gold_analytics_dag.py` สำหรับ Airflow 2.10.x มี extract/validate/load → model readiness/evaluation → export. ค่า `schedule=None` จึงเริ่มด้วย Manual Trigger. ตั้ง `GOLD_PROJECT_DIR`, `GOLD_PIPELINE_PYTHON` ไปยัง Python 3.12 venv ที่ติดตั้ง dependencies และ `DATABASE_URL` ตามต้องการ. ไม่มีการอ้างว่ารัน Airflow UI ผ่านแล้ว

## ทดสอบและหลักฐาน

```bash
python -m unittest discover -s tests -v
python tools/check_snapshot.py
python -m tools.verify_runtime
python -m tools.verify_api
```

- [Unit/integration tests](evidence/unit-tests.txt): ใช้สำเนาข้อมูลจริงที่บันทึกไว้; กรณี outage/invalid value เป็น fault injection ใน DB ชั่วคราวเท่านั้น
- [Actual live ingest](evidence/live-refresh.txt), [SQL coverage](evidence/database-summary.json), [UPSERT/persistence checks](evidence/runtime-verification.json), [HTTP API checks](evidence/api-tests.json)
- [Published CSV](data/published/observations.csv), [snapshot JSON](data/published/snapshot.json), [hash manifest](data/published/manifest.json)

GitHub Actions มี CI และ workflow **Refresh real market data** ที่เริ่มด้วย `workflow_dispatch` เท่านั้น ยังไม่ได้ตั้งรันตามเวลาอัตโนมัติ

## ขอบเขตที่ต้องอ่านก่อนประเมินผลงาน

- World Bank ที่ดึงได้ระบุ Updated on October 02, 2026 และข้อมูลล่าสุด September 2026; ไม่ติดป้ายว่าเป็นราคาวันนี้
- Monthly history, spot quotes และ FX reference rate เป็นคนละชุดข้อมูล ไม่รวมกราฟ/หน่วยอย่างผิดความหมาย
- ML ใช้ข้อมูล monthly ปี 2000 เป็นต้นไปและ features ที่ lag แล้ว ข้อมูลเป็น current-vintage ไม่ใช่ point-in-time backtest
- ยังไม่ทดสอบ PostgreSQL, Docker หรือ Airflow runtime ในสภาพแวดล้อม Work นี้; SQLite, CLI, local HTTP API และ Web Dashboard มีหลักฐานแยกกัน
- งานรอบนี้พัฒนาจาก concept repository ปัจจุบัน ไม่ใช่การกู้คืนระบบเก่าหรือผลทดสอบเดิม

หน้า showcase เดิมและ scope เก่าเก็บไว้ใน `docs/archive/` โดยระบุว่าเป็น concept ที่ยังไม่มี runtime ยืนยัน
