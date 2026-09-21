import { useState } from "react";
import BodyMap from "../../components/BodyMap";

const elements = {
  "ไฟ 4": "ปริณามัคคี สันตัปปัคคี ปริทัยหัคคี ชีรณัคคี".split(" "),
  "ลม 6": "อุทธังคมาวาตา อโธคมาวาตา กุจฉิสยาวาตา โกฏฐาสยาวาตา อัสสาสะปัสสาสะวาตา อังคมังคานุสารีวาตา".split(" "),
  "น้ำ 12": "ปิตตัง เสมหัง บุพโพ โลหิตัง เสโท เมโท อัสสุ วสา เขโฬ สิงฆานิกา ลสิกา มุตตัง".split(" "),
  "ดิน 20": "เกศา โลมา นขา ทันตา ตะโจ มังสัง นหารู อัฏฐิ อัฏฐิมิญชัง วักกัง หทยัง ยกนัง กิโลมกัง ปิหกัง ปัปผาสัง อันตัง อันตคุณัง อุทริยัง กรีสัง มัตถเกมัตถลุงคัง".split(" "),
};
const coordinates = "พัทธะปิตตะ อพัทธะปิตตะ กำเดา หทัยวาตะ สัตถกะวาตะ สุมนาวาตะ ศอเสมหะ อุระเสมหะ คูถเสมหะ หทัยวัตถุ อุทริยะ กรีสะ".split(" ");

export default function OpdFields({ tab, fields, bind, live = false, disabled = false }) {
  const [medicines, setMedicines] = useState(() => Array.from({length:Math.max(1,...Object.keys(fields || {}).map(k=>Number(k.match(/^ยา (\d+) ·/)?.[1] || 0)))},(_,i)=>i+1));
  const field = (label, type = "text") => <label className="field" key={label}>{label}{type === "textarea" ? <textarea rows="3" maxLength="5000" {...bind(label)} /> : <input type={type} step={type === "number" ? "any" : undefined} maxLength="5000" {...bind(label)} />}</label>;
  const choice = (label, values) => <label className="field" key={label}>{label}<select {...bind(label)}><option value="">ยังไม่ได้บันทึก</option>{values.map(v => <option key={v}>{v}</option>)}</select></label>;
  const section = (title, children) => <details className="opd-section"><summary>{title}</summary>{children}</details>;
  const status = ["กำเริบ", "หย่อน", "พิการ", "ไม่พบความผิดปกติ", "ยังไม่ได้ประเมิน"];
  return <div className="opd-fields">
    <p className="subtle">รายละเอียด OPD ตามแบบฟอร์มอ้างอิง · เปิดหมวดที่ต้องการบันทึก</p>
    <div hidden={tab !== "ซักประวัติ"}>
      {section("ข้อมูลส่วนบุคคลและการติดต่อ", <>
        <div className="field-row">{field("ชื่อเล่น")}{field("เพศ / เพศสภาพ")}{!live && field("วันเกิด (ค.ศ.)", "date")}{field("สถานภาพ")}{!live && field("โทรศัพท์", "tel")}{field("อีเมล", "email")}{field("LINE ID")}{field("อาชีพ")}</div>
        {field("ที่อยู่ที่ติดต่อได้", "textarea")}{field("สถานที่เกิดและเติบโต (ตำบล / อำเภอ / จังหวัด)")}
        <p className="subtle">{live ? "ใช้วันเกิดและโทรศัพท์จากทะเบียนหลัก อายุแสดงในหัวบันทึก ส่วนจักรราศียังรอตรวจรับกฎจันทรคติ" : "อายุ วันเกิดจันทรคติ และจักรราศีเป็นช่องอัตโนมัติในระบบจริง — ต้นแบบยังไม่คำนวณ"}</p>
      </>)}
      {section("ประวัติการเกิดและสุขภาพ", <>
        <div className="field-row">{field("อยู่ในครรภ์มารดา (เดือน)", "number")}{choice("ลักษณะการคลอด", ["คลอดปกติ", "ผ่าคลอด", "ไม่ทราบ"])}{choice("อิริยาบถประจำ", ["ยืน", "เดิน", "นั่ง", "นอน", "หลายอิริยาบถ"])}</div>
        {["ประวัติการอยู่ไฟ", "ประวัติประจำเดือน", "โรคประจำตัว", "โรคทางพันธุกรรมและประวัติครอบครัว", "ประวัติเจ็บป่วยในอดีต", "ประวัติเจ็บป่วยปัจจุบัน / อาการเรื้อรัง", "ประวัติแพ้ยาและอาการแพ้"].map(label => field(label, "textarea"))}
        <p className="subtle">ข้อมูลที่ไม่เกี่ยวข้องให้ระบุ “ไม่เกี่ยวข้อง” และข้อมูลที่ไม่ทราบให้ระบุ “ไม่ทราบ”</p>
      </>)}
    </div>
    <div hidden={tab !== "ตรวจและประเมิน"}>
      {section("สัญญาณชีพและข้อมูลการตรวจ", <div className="field-row">{field("วันที่ตรวจ", "date")}{field("ครั้งที่", "number")}{field("น้ำหนัก (กก.)", "number")}{field("ส่วนสูง (ซม.)", "number")}{field("ความดันตัวบน (mmHg)", "number")}{field("ความดันตัวล่าง (mmHg)", "number")}</div>)}
      {section("สมุฏฐานและมูลเหตุของโรค", <>
        {field("มูลเหตุการเกิดโรค", "textarea")}{field("ธาตุปฏิสนธิ (หลัก)")}{field("ธาตุกำเนิด (รอง)")}
        <p className="subtle">ผู้รักษาบันทึกผลประเมินเอง ข้อมูลนี้ไม่ใช่ผลวินิจฉัยอัตโนมัติ</p>
        { ["อุตุ", "อายุ", "กาล", "ประเทศ", "อาชีพ", "อิริยาบถ", "อารมณ์"].map(x => field(`สมุฏฐานด้าน${x} (ปถวี / อาโป / วาโย / เตโช)`, "textarea")) }
      </>)}
      {section("ตรีธาตุและพิกัดธาตุ", <>
        <p className="subtle">คงลำดับแถวตามแบบฝึกงาน แต่ละช่องให้ผู้รักษาระบุผล</p>
        {[ ["ปิตตะ", "วาตะ", "เสมหะ"], ["วาตะ", "เสมหะ", "ปิตตะ"], ["เสมหะ", "ปิตตะ", "วาตะ"] ].map((row, i) => <div className="field-row" key={i}>{row.map(x => field(`ตรีธาตุ แถว ${i + 1} · ${x}`))}</div>)}
        <div className="field-row">{coordinates.map(x => choice(`พิกัดธาตุ · ${x}`, status))}</div>
      </>)}
      {section("รูปธาตุ 42", <>{Object.entries(elements).map(([group, names]) => <fieldset className="opd-element-group" key={group}><legend>{group}</legend><div className="field-row">{names.map(x => choice(`รูปธาตุ · ${x}`, status))}</div></fieldset>)}</>)}
      {section("วินิจฉัยและการประเมินต่อเนื่อง", <>
        {["เอกโทษ", "ทุวันโทษ", "ตรีโทษ"].map(x => field(`${x} — พิกัด / ตรีธาตุ / กำเริบ หย่อน พิการ / รูปธาตุ`, "textarea"))}
        {["อาการทางรูป", "อาการทางนาม", "ประเมินอาการที่อาจเกิดขึ้นในอนาคต", "คำวินิจฉัยของแพทย์ (Dx)", "ตำราและเหตุผลประกอบการประเมิน"].map(x => field(x, "textarea"))}
      </>)}
    </div>
    <div hidden={tab !== "แผนการดูแล"}>
      {section("แผนการรักษาและหัตถเวชกรรมไทย", <>
        {["รุ", "ล้อม", "รักษา", "หัตถการ"].map(x => field(`แผนการรักษา · ${x}`, "textarea"))}
        {field("ตำแหน่งปวด (ด้านหน้า / หลัง / ซ้าย / ขวา)", "textarea")}
        {live ? <BodyMap disabled={disabled} value={fields["ผังตำแหน่งปวด"]||""} onChange={value=>bind("ผังตำแหน่งปวด").onChange({target:{value}})} /> : <p className="subtle">ต้นแบบใช้ข้อความระบุตำแหน่ง</p>}
        {field("โรคทางหัตถเวชกรรมไทย")}{field("สูตรนวด", "textarea")}{field("หัตถการอื่น ๆ", "textarea")}
        {choice("คะแนนปวดหลังรับบริการ (0–10)", Array.from({length:11}, (_,i)=>String(i)))}
      </>)}
      {section("เภสัชกรรมไทยและรายการยา", <>
        {medicines.map((id, i) => <fieldset className="opd-element-group" key={id}><legend>ยารายการที่ {i + 1}</legend><div className="field-row">{["ชื่อตำรับยา", "จำนวนและหน่วย", "ขนาดรับประทาน", "เวลารับประทาน", "ระยะเวลารับประทาน", "หมายเหตุ"].map(x => field(`ยา ${id} · ${x}`))}</div></fieldset>)}
        <button type="button" className="secondary" onClick={() => setMedicines(ids => [...ids, ids.length + 1])}>เพิ่มรายการยา</button>
        {field("ตำรับปรุงเฉพาะราย / ยาต้ม / ยาอื่น ๆ", "textarea")}
      </>)}
      {section("สรุปผล ติดตาม และผู้บันทึก", <>
        {field("สรุปหลังการรักษา", "textarea")}{field("การรักษาครั้งติดตาม", "textarea")}{field("วันนัดติดตาม", "date")}{field("ผู้รักษา / เลขที่ใบประกอบวิชาชีพ")}{field("ผู้ฝึกงาน / ชั้นปี (ถ้ามี)")}
        {choice("สถานะความยินยอมรับการรักษา", ["ยังไม่ได้รับความยินยอม", "ได้รับความยินยอมแล้ว", "ปฏิเสธ"])}
        <p className="subtle">{live ? "ช่องนี้บันทึกสถานะที่เจ้าหน้าที่รับทราบ ยังต้องเก็บเอกสารยินยอมที่ลงนามตามกระบวนการคลินิก" : "ต้นแบบยังไม่รับลายเซ็นหรือเก็บหลักฐานความยินยอม ฉบับจริงต้องเก็บเวลา ผู้ลงนาม และรุ่นเอกสาร"}</p>
      </>)}
    </div>
  </div>;
}
