import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import "./home.css";

const clinic = {
  phone: "082-203-5330",
  lineId: "@thasonyahclinic",
  lineUrl: "https://lin.ee/WOmtGMv",
  facebookUrl: "https://www.facebook.com/thasonyahclinic",
  mapsUrl: "https://maps.app.goo.gl/58aG53PrNvA9M4249",
  servicesUrl:
    "https://script.google.com/macros/s/AKfycbwaqh0sQ9Qwo2NnOdk4fUtafdQIcOf1kp6ikGLUavulzMUMcvZ8qlfhHY0h1PH5wk5K/exec?page=services",
  address:
    "189 อาคาร Inter View ห้องร้านค้า 1 หมู่ 7 ต.บางบ่อ อ.บางบ่อ จ.สมุทรปราการ 10560",
};

const openingDays = [
  ["ศุกร์", "10.00-22.00 น."],
  ["เสาร์", "10.00-22.00 น."],
  ["อาทิตย์", "10.00-22.00 น."],
  ["จันทร์", "10.00-22.00 น."],
];

const fallbackServices = [
  { id: "thai-diagnosis", name: "ตรวจประเมินแพทย์แผนไทย", price: 0, minutes: 30 },
  { id: "thai-massage", name: "นวดไทยและหัตถการบำบัด", price: 0, minutes: 60 },
  { id: "herbal-compress", name: "ประคบสมุนไพร", price: 0, minutes: 30 },
  { id: "toksen", name: "ตอกเส้นและดูแลเฉพาะทาง", price: 0, minutes: 60 },
];

const careItems = [
  "ออฟฟิศซินโดรมและอาการปวดคอบ่าไหล่",
  "ปวดหลัง ปวดเอว กล้ามเนื้อตึงจากการใช้งาน",
  "ฟื้นฟูสมดุลธาตุและให้คำแนะนำการดูแลตนเอง",
  "วางแผนหัตถการและติดตามผลอย่างเป็นระบบ",
];

const process = [
  "เลือกบริการและเวลาที่สะดวก",
  "ส่งคำขอจองคิวจากหน้าเว็บ",
  "เจ้าหน้าที่ตรวจสอบและติดต่อยืนยัน",
  "เข้ารับบริการตามเวลานัดหมาย",
];

const serviceDescriptions = {
  "ตรวจประเมินแพทย์แผนไทย":
    "ซักประวัติ ตรวจธาตุเจ้าเรือน จักรราศีสมุฏฐาน และประเมินอาการก่อนวางแผนดูแล",
  "นวดไทยและหัตถการบำบัด":
    "ดูแลอาการตึง ปวดเมื่อย คอ บ่า ไหล่ หลัง และกล้ามเนื้อ ด้วยหัตถการที่เหมาะกับแต่ละราย",
  ประคบสมุนไพร:
    "ใช้ความร้อนและสมุนไพรไทยช่วยผ่อนคลายกล้ามเนื้อ ส่งเสริมการไหลเวียน และฟื้นฟูร่างกาย",
  "ตอกเส้นและดูแลเฉพาะทาง":
    "บริการเฉพาะด้านสำหรับผู้ที่ต้องการฟื้นฟูอาการเรื้อรัง โดยประเมินความเหมาะสมก่อนทำทุกครั้ง",
};

const todayBangkok = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Bangkok",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());

const formatMoney = (value) =>
  Number(value) > 0 ? `${Number(value).toLocaleString("th-TH")} บาท` : "สอบถามราคา";

export default function Home() {
  const [services, setServices] = useState(fallbackServices);
  const [booking, setBooking] = useState({
    serviceKey: fallbackServices[0].id,
    date: todayBangkok(),
    time: "10:00",
    fullName: "",
    phone: "",
    lineId: "",
    note: "",
  });
  const [submitState, setSubmitState] = useState({ status: "idle", message: "" });

  useEffect(() => {
    let alive = true;
    api
      .get("/public/services")
      .then((response) => {
        if (!alive || !Array.isArray(response.data) || !response.data.length) return;
        const liveServices = response.data.map((service) => ({
          id: service.id,
          name: service.name,
          price: Number(service.price),
          minutes: service.minutes,
          live: true,
        }));
        setServices(liveServices);
        setBooking((current) => ({ ...current, serviceKey: liveServices[0].id }));
      })
      .catch(() => {
        if (alive) setServices(fallbackServices);
      });
    return () => {
      alive = false;
    };
  }, []);

  const selectedService = useMemo(
    () => services.find((service) => String(service.id) === String(booking.serviceKey)) || services[0],
    [booking.serviceKey, services],
  );

  const submitBooking = async (event) => {
    event.preventDefault();
    setSubmitState({ status: "loading", message: "กำลังส่งคำขอจองคิว…" });
    const start = new Date(`${booking.date}T${booking.time}:00+07:00`);
    const minutes = Number(selectedService?.minutes || 60);
    try {
      const response = await api.post("/public/bookings", {
        request_id: crypto.randomUUID(),
        full_name: booking.fullName,
        phone: booking.phone,
        line_id: booking.lineId,
        service_id: selectedService?.live ? selectedService.id : null,
        service_name: selectedService?.name || "สอบถามบริการ",
        preferred_starts_at: start.toISOString(),
        preferred_ends_at: new Date(start.getTime() + minutes * 60000).toISOString(),
        note: booking.note,
      });
      setSubmitState({
        status: "success",
        message: `ส่งคำขอจองแล้ว เลขอ้างอิง ${response.data.id.slice(0, 8)} เจ้าหน้าที่จะติดต่อยืนยันอีกครั้ง`,
      });
      setBooking((current) => ({ ...current, fullName: "", phone: "", lineId: "", note: "" }));
    } catch (error) {
      const status = error.response?.status;
      setSubmitState({
        status: "error",
        message:
          status === 422
            ? "กรุณาเลือกวันจันทร์/ศุกร์/เสาร์/อาทิตย์ เวลา 10.00-22.00 น. และตรวจเบอร์โทรอีกครั้ง"
            : status === 429
              ? "ส่งคำขอบ่อยเกินไป กรุณารอสักครู่แล้วลองใหม่"
              : "ยังส่งคำขอไม่ได้ กรุณาติดต่อคลินิกผ่าน LINE หรือโทรศัพท์",
      });
    }
  };

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
          <a href="#booking">จองคิว</a>
          <a href="#services">บริการ</a>
          <a href="#contact">ติดต่อ</a>
          <Link to="/staff">สำหรับเจ้าหน้าที่</Link>
        </nav>
      </header>

      <main id="top">
        <section className="public-hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <h1 id="hero-title">ธสัญญา คลินิกการแพทย์แผนไทย</h1>
            <p className="hero-lead">
              ดูแลอาการปวดเมื่อย ฟื้นฟูสมดุลร่างกาย และวางแผนการดูแลด้วยศาสตร์แพทย์แผนไทย
              พร้อมระบบจองคิวและติดตามผลที่เป็นระเบียบ
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#booking">
                จองคิวเอง
              </a>
              <a className="secondary-link" href={clinic.lineUrl} target="_blank" rel="noreferrer">
                LINE {clinic.lineId}
              </a>
            </div>
            <p className="safe-note">
              กรณีเจ็บป่วยฉุกเฉิน กรุณาติดต่อสถานพยาบาลใกล้บ้านหรือสายด่วน 1669
            </p>
          </div>
          <aside className="hero-card" aria-label="ข้อมูลคลินิก">
            <img src="/brand/thasonyah-logo.jpg" alt="ตราสัญลักษณ์ธสัญญา คลินิก" />
            <div>
              <strong>ตรวจ · วินิจฉัย · หัตถการ · ติดตามผล</strong>
              <p>
                {clinic.phone} · เปิดจันทร์ ศุกร์ เสาร์ อาทิตย์ เวลา 10.00-22.00 น.
              </p>
              <p>
                ผู้ประกอบวิชาชีพ: นางปิยฉัตร ธสัญญา · สาขาการแพทย์แผนไทย · ใบอนุญาต พท.น.10497
              </p>
            </div>
          </aside>
        </section>

        <section className="booking-panel" id="booking" aria-labelledby="booking-title">
          <div className="booking-copy">
            <h2 id="booking-title">จองคิวเข้ารับบริการ</h2>
            <p>
              เลือกบริการและเวลาที่ต้องการ ระบบจะส่งคำขอให้เจ้าหน้าที่ตรวจสอบและติดต่อยืนยันก่อนเข้ารับบริการ
            </p>
            <ul className="opening-list" aria-label="เวลาเปิดบริการ">
              {openingDays.map(([day, hours]) => (
                <li key={day}>
                  <span>{day}</span>
                  <strong>{hours}</strong>
                </li>
              ))}
            </ul>
          </div>
          <form className="booking-form" onSubmit={submitBooking}>
            <label>
              บริการที่ต้องการ
              <select
                value={booking.serviceKey}
                onChange={(event) => setBooking({ ...booking, serviceKey: event.target.value })}
              >
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name} · {service.minutes} นาที · {formatMoney(service.price)}
                  </option>
                ))}
              </select>
            </label>
            <div className="booking-row">
              <label>
                วันที่
                <input
                  type="date"
                  min={todayBangkok()}
                  required
                  value={booking.date}
                  onChange={(event) => setBooking({ ...booking, date: event.target.value })}
                />
              </label>
              <label>
                เวลา
                <input
                  type="time"
                  min="10:00"
                  max="22:00"
                  required
                  value={booking.time}
                  onChange={(event) => setBooking({ ...booking, time: event.target.value })}
                />
              </label>
            </div>
            <label>
              ชื่อ-นามสกุล
              <input
                required
                minLength="2"
                maxLength="200"
                value={booking.fullName}
                onChange={(event) => setBooking({ ...booking, fullName: event.target.value })}
              />
            </label>
            <div className="booking-row">
              <label>
                เบอร์โทร
                <input
                  required
                  inputMode="tel"
                  minLength="8"
                  maxLength="40"
                  value={booking.phone}
                  onChange={(event) => setBooking({ ...booking, phone: event.target.value })}
                />
              </label>
              <label>
                LINE ID ถ้ามี
                <input
                  maxLength="120"
                  placeholder="เช่น @thasonyahclinic"
                  value={booking.lineId}
                  onChange={(event) => setBooking({ ...booking, lineId: event.target.value })}
                />
              </label>
            </div>
            <label>
              อาการหรือหมายเหตุเพิ่มเติม
              <textarea
                rows="3"
                maxLength="1000"
                value={booking.note}
                onChange={(event) => setBooking({ ...booking, note: event.target.value })}
              />
            </label>
            <button className="primary-link booking-submit" disabled={submitState.status === "loading"}>
              {submitState.status === "loading" ? "กำลังส่ง…" : "ส่งคำขอจองคิว"}
            </button>
            {submitState.message && (
              <p className={`booking-result ${submitState.status}`} role="status">
                {submitState.message}
              </p>
            )}
          </form>
        </section>

        <section className="public-section" id="services" aria-labelledby="services-title">
          <div className="section-heading">
            <h2 id="services-title">บริการหลักของคลินิก</h2>
            <p>
              เจ้าหน้าที่จะประเมินอาการก่อนรับบริการทุกครั้ง เพื่อเลือกแนวทางดูแลที่เหมาะกับคนไข้แต่ละราย
            </p>
          </div>
          <div className="service-grid">
            {services.slice(0, 8).map((service) => (
              <article className="service-card" key={service.id}>
                <h3>{service.name}</h3>
                <p>{serviceDescriptions[service.name] || "ตรวจประเมินก่อนทำหัตถการและให้คำแนะนำตามอาการ"}</p>
                <span>
                  {service.minutes} นาที · {formatMoney(service.price)}
                </span>
              </article>
            ))}
          </div>
          <div className="section-actions">
            <a className="secondary-link" href={clinic.servicesUrl} target="_blank" rel="noreferrer">
              ดูรายการบริการเดิม
            </a>
          </div>
        </section>

        <section className="split-section" aria-labelledby="care-title">
          <div>
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
            <h2 id="contact-title">ติดต่อและเดินทาง</h2>
            <p>{clinic.address}</p>
            <p>โทร {clinic.phone} · LINE {clinic.lineId}</p>
          </div>
          <div className="contact-actions">
            <a className="primary-link" href={clinic.lineUrl} target="_blank" rel="noreferrer">
              เปิด LINE OA
            </a>
            <a className="secondary-link" href={clinic.mapsUrl} target="_blank" rel="noreferrer">
              เปิด Google Maps
            </a>
            <a className="secondary-link" href={clinic.facebookUrl} target="_blank" rel="noreferrer">
              Facebook
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}
