# ขอบเขตที่ตรวจสอบจากระบบจริง

Repository: `intasan/gold-trading`
ฐาน source ที่ตรวจ: `2526905216cfc732aa7538c7a5ce69ca810dad82`

**สถานะ: ยังไม่มีระบบที่รันได้**

Repository มีเพียง README และ index.html; ไม่มี Airflow DAG, API, Compose, model หรือข้อมูลจริงสำหรับยืนยันตัวเลขเดิม

## แหล่งหลักฐาน

- [evidence/source-audit.json](../evidence/source-audit.json)

## Traceability จาก source

| ไฟล์ที่ตรวจ | ขอบเขตที่ยืนยันได้ |
|---|---|
| [index.html](../index.html) | พบ source ใน commit ข้างต้น; การมีไฟล์ไม่ใช่การทดสอบผ่าน |

## เกณฑ์ตรวจรับ BA / SA

| เกณฑ์ | หลักฐาน / สถานะ |
|---|---|
| ขอบเขตปัจจุบันตรงกับ source | ยังไม่มีระบบที่รันได้ |
| End-to-end ด้วยข้อมูลจริง | Repository มีเพียง README และ index.html; ไม่มี Airflow DAG, API, Compose, model หรือข้อมูลจริงสำหรับยืนยันตัวเลขเดิม |
| ผลการทดสอบที่ทำซ้ำได้ | อ่าน command, stdout, exit code ใน evidence; syntax check ไม่ใช่ runtime test |
| ข้อมูลจริงและ provenance | เฉพาะราคาทองใน live-verification.txt ที่มี URL/เวลา publication; ไม่ใช้ fixture เป็นข้อมูลจริง |
| UAT โดยเจ้าของงานหรือผู้ใช้งาน | ยังไม่ได้ดำเนินการในรอบนี้ |

## ข้อจำกัดการแสดงผลงาน

ผล unit tests เป็นการตรวจ logic โดยมี fixture ตาม suite เดิม ไม่ใช่หลักฐานธุรกรรมจริง การฝึกโมเดลจริง การทำงานของอุปกรณ์จริง หรือการรับรองจากผู้ใช้ ไม่สร้างข้อมูลธุรกิจทดแทนข้อมูลที่ขาด และไม่อนุมานว่าไม่มีข้อมูลเท่ากับปลอดภัย
