# Gold Trading Analytics 📈

ระบบรวบรวม วิเคราะห์ และทดลองพยากรณ์ราคาทองคำจากข้อมูลตลาดจริง พร้อมเว็บ Dashboard

> **สถานะ:** โปรเจกต์เพื่อการศึกษาและทดลอง Machine Learning ไม่ใช่คำแนะนำในการลงทุน และโมเดลยังไม่ผ่านเกณฑ์อนุมัติสำหรับใช้ซื้อขายจริง

## จุดเด่น
- **Data Pipeline:** Apache Airflow จัดการการดึงและประมวลผลข้อมูล
- **Data Storage:** PostgreSQL และระบบจัดเก็บข้อมูลประกอบ
- **Machine Learning:** เปรียบเทียบ Ridge Regression, Random Forest และ Histogram Gradient Boosting กับ Baseline
- **Dashboard:** เว็บแสดงกราฟราคาทองคำ ข้อมูลตลาด ผลการทดลองพยากรณ์ และตัวชี้วัด
- **Data:** Gold Futures และตัวแปรตลาด เช่น Silver Futures, DXY, USD/THB, S&P 500, US10Y Yield, VIX และ WTI

## ภาพรวมการทำงาน
```text
Market Data Sources
        ↓
Apache Airflow / Data Ingestion
        ↓
Data Processing / PostgreSQL
        ↓
Machine Learning & Backtesting
        ↓
FastAPI / Web Dashboard
```

## วิธีรันบนเครื่อง
หลังเพิ่มซอร์สโค้ดครบแล้ว:
```powershell
copy .env.example .env
docker compose up -d --build
```
- Dashboard: http://localhost:8002
- API Docs: http://localhost:8002/docs
- Airflow: http://localhost:8081

**หมายเหตุ:** `localhost` ใช้ได้เฉพาะบนเครื่องที่รัน Docker ไม่ใช่ลิงก์เว็บสาธารณะ GitHub Repository แสดงโค้ดและเอกสารเท่านั้น

## ผลการทดลองเบื้องต้น
| Model | MAE (ประมาณ) |
|---|---:|
| Ridge Regression | 27.285 |
| Baseline | 27.299 |
| Random Forest | 27.316 |
| Histogram Gradient Boosting | 27.413 |

ผลดังกล่าวเป็นการทดลองย้อนหลัง ไม่ยืนยันความสามารถในการทำนายราคาในอนาคต

## ข้อมูลผู้จัดทำ
โปรเจกต์ด้าน Data Engineering, Machine Learning และ Data Visualization เพื่อการศึกษา

---
**Source code และไฟล์ประกอบอยู่ระหว่างการอัปโหลด**
