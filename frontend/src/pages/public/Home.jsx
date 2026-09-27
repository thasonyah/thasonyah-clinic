import { Link } from "react-router-dom";
import "./home.css";

const services = [
  {
    title: "ตรวจประเมินแบบแพทย์แผนไทย",
    text: "ซักประวัติ ตรวจธาตุเจ้าเรือน จักรราศีสมุฏฐาน และประเมินอาการก่อนวางแผนดูแล",
  },
  {
    title: "นวดไทยและหัตถการบำบัด",
    text: "ดูแลอาการตึง ปวดเมื่อย คอ บ่า ไหล่ หลัง และกล้ามเนื้อ ด้วยหัตถการที่เหมาะกับแต่ละราย",
  },
  {
    title: "ประคบสมุนไพรและอบสมุนไพร",
    text: "ใช้ความร้อนและสมุนไพรไทยช่วยผ่อนคลายกล้ามเนื้อ ส่งเสริมการไหลเวียน และฟื้นฟูร่างกาย",
  },
  {
    title: "ตอกเส้นและการดูแลเฉพาะทาง",
    text: "บริการเฉพาะด้านสำหรับผู้ที่ต้องการฟื้นฟูอาการเรื้อรัง โดยประเมินความเหมาะสมก่อนทำทุกครั้ง",
  },
];

const careItems = [
  "ออฟฟิศซินโดรมและอาการปวดคอบ่าไหล่",
  "ปวดหลัง ปวดเอว กล้ามเนื้อตึงจากการใช้งาน",
  "ฟื้นฟูสมดุลธาตุและให้คำแนะนำการดูแลตนเอง",
  "วางแผนหัตถการและติดตามผลอย่างเป็นระบบ",
];

const process = [
  "ลงทะเบียนและซักประวัติสุขภาพ",
  "ตรวจประเมินตามแนวแพทย์แผนไทย",
  "เลือกหัตถการหรือคำแนะนำที่เหมาะสม",
  "บันทึกผลและนัดติดตามเมื่อจำเป็น",
];

export default function Home() {
  return (
    <div className="public-home">
      <header className="public-nav" aria-label="เมนูหลัก">
        <a className="public-brand" href="#top" aria-label="ธสัญญา คลินิก หน้าแรก">
          <img src="/brand/thasonyah-logo.jpg" alt="" width="52" height="52" />
          <span>
            <strong>ธสัญญา คลินิก</strong>
            <small>การแพทย์แผนไทย</small>
          </span>
        </a>
        <nav>
          <a href="#services">บริการ</a>
          <a href="#process">ขั้นตอนรับบริการ</a>
          <a href="#contact">ติดต่อ</a>
          <Link to="/staff">สำหรับเจ้าหน้าที่</Link>
        </nav>
      </header>

      <main id="top">
        <section className="public-hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow">Thai Traditional Medicine Clinic</p>
            <h1 id="hero-title">ธสัญญา คลินิกการแพทย์แผนไทย</h1>
            <p className="hero-lead">
              ดูแลอาการปวดเมื่อย ฟื้นฟูสมดุลร่างกาย และวางแผนการดูแลด้วยศาสตร์แพทย์แผนไทย
              โดยบันทึกประวัติและติดตามผลอย่างเป็นระบบ
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="https://www.facebook.com/thasonyahclinic" target="_blank" rel="noreferrer">
                ติดต่อคลินิก
              </a>
              <a className="secondary-link" href="#services">
                ดูบริการของเรา
              </a>
            </div>
            <p className="safe-note">
              กรณีเจ็บป่วยฉุกเฉิน กรุณาติดต่อสถานพยาบาลใกล้บ้านหรือสายด่วน 1669
            </p>
          </div>
          <aside className="hero-card" aria-label="แนวทางการดูแล">
            <img src="/brand/thasonyah-logo.jpg" alt="ตราสัญลักษณ์ธสัญญา คลินิก" />
            <div>
              <span>Clinic care system</span>
              <strong>ตรวจ · วินิจฉัย · หัตถการ · ติดตามผล</strong>
              <p>
                ระบบภายในรองรับ OPD card, จักรราศีอัตโนมัติ, ตารางนัดหมาย, คลังยา และชำระเงิน
              </p>
            </div>
          </aside>
        </section>

        <section className="public-section" id="services" aria-labelledby="services-title">
          <div className="section-heading">
            <p className="eyebrow">Services</p>
            <h2 id="services-title">บริการหลักของคลินิก</h2>
            <p>
              เจ้าหน้าที่จะประเมินอาการก่อนรับบริการทุกครั้ง เพื่อเลือกแนวทางดูแลที่เหมาะกับคนไข้แต่ละราย
            </p>
          </div>
          <div className="service-grid">
            {services.map((service) => (
              <article className="service-card" key={service.title}>
                <h3>{service.title}</h3>
                <p>{service.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="split-section" aria-labelledby="care-title">
          <div>
            <p className="eyebrow">Care focus</p>
            <h2 id="care-title">เหมาะสำหรับผู้ที่ต้องการดูแลอะไรบ้าง</h2>
            <p>
              คลินิกเน้นการซักประวัติ ตรวจประเมิน และเลือกหัตถการตามอาการจริง ไม่ใช้แนวทางเดียวกับทุกคน
            </p>
          </div>
          <ul className="care-list">
            {careItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="public-section process-section" id="process" aria-labelledby="process-title">
          <div className="section-heading">
            <p className="eyebrow">Process</p>
            <h2 id="process-title">ขั้นตอนการรับบริการ</h2>
          </div>
          <ol className="process-list">
            {process.map((item, index) => (
              <li key={item}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{item}</strong>
              </li>
            ))}
          </ol>
        </section>

        <section className="contact-section" id="contact" aria-labelledby="contact-title">
          <div>
            <p className="eyebrow">Contact</p>
            <h2 id="contact-title">ติดต่อและนัดหมาย</h2>
            <p>
              สามารถติดต่อคลินิกผ่านเพจ Facebook เพื่อสอบถามเวลาให้บริการ นัดหมาย หรือส่งข้อมูลเบื้องต้นก่อนเข้ารับบริการ
            </p>
          </div>
          <div className="contact-actions">
            <a className="primary-link" href="https://www.facebook.com/thasonyahclinic" target="_blank" rel="noreferrer">
              เปิดเพจ Facebook
            </a>
            <Link className="secondary-link" to="/staff">
              เข้าระบบเจ้าหน้าที่
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
