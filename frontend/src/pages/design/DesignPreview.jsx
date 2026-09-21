import { useState, useEffect } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import "./design.css";
import OpdFields from "./OpdFields";
import ServiceCatalog, { initialServices } from "./ServiceCatalog";

const paths = {
  today: "M3 4h18v17H3z M7 2v4 M17 2v4 M3 9h18 M7 13h3 M14 13h3 M7 17h3",
  calendar: "M3 5h18v16H3z M7 2v6 M17 2v6 M3 10h18 M8 14h2 M14 14h2",
  patients:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M20 8v6 M17 11h6",
  treatment: "M9 3h6v6h6v6h-6v6H9v-6H3V9h6z",
  palette:
    "M12 3a9 9 0 1 0 0 18h1a2 2 0 0 0 0-4h-1a2 2 0 0 1 0-4h5a4 4 0 0 0 4-4c0-3-4-6-9-6z M7 8h.01 M7 13h.01 M12 7h.01",
  search: "M21 21l-5-5 M10 17a7 7 0 1 0 0-14 7 7 0 0 0 0 14",
  arrow: "M5 12h14 M14 7l5 5-5 5",
  plus: "M12 5v14 M5 12h14",
  clock: "M12 8v4l3 2 M21 12a9 9 0 1 0-18 0 9 9 0 0 0 18 0",
  leaf: "M4 20C2 8 9 3 20 4c1 11-4 18-14 14 M5 19L16 8",
  check: "M5 12l4 4L19 6",
};
function Icon({ name, ...props }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <path d={paths[name] || paths.leaf} />
    </svg>
  );
}
const nav = [
  ["today", "งานวันนี้"],
  ["calendar", "นัดหมาย"],
  ["patients", "ประวัติคนไข้"],
  ["treatment", "ห้องตรวจ"],
  ["services", "จัดการหัตถการ"],
  ["palette", "สีและองค์ประกอบ"],
];
const people = [
  {
    id: "DEMO-001",
    name: "ผู้รับบริการตัวอย่าง 01",
    initial: "01",
    time: "09:00",
    service: "นวดไทย · 60 นาที",
    doctor: "ผู้รักษา A",
    bed: "เตียง 01",
    state: "รอเข้ารับบริการ",
    tone: "waiting",
  },
  {
    id: "DEMO-002",
    name: "ผู้รับบริการตัวอย่าง 02",
    initial: "02",
    time: "09:30",
    service: "ประคบสมุนไพร · 30 นาที",
    doctor: "ผู้รักษา B",
    bed: "เตียง 02",
    state: "กำลังรับบริการ",
    tone: "active",
  },
  {
    id: "DEMO-003",
    name: "ผู้รับบริการตัวอย่าง 03",
    initial: "03",
    time: "10:00",
    service: "ตรวจติดตามอาการ · 30 นาที",
    doctor: "ผู้รักษา A",
    bed: "ห้องตรวจ",
    state: "ยืนยันนัดแล้ว",
    tone: "neutral",
  },
  {
    id: "DEMO-004",
    name: "ผู้รับบริการตัวอย่าง 04",
    initial: "04",
    time: "10:30",
    service: "นวดไทย · 60 นาที",
    doctor: "ผู้รักษา B",
    bed: "เตียง 02",
    state: "ยืนยันนัดแล้ว",
    tone: "neutral",
  },
];
function Badge({ tone = "neutral", children }) {
  return (
    <span className={`badge ${tone}`}>
      <span />
      {children}
    </span>
  );
}
function Person({ person = people[0] }) {
  return (
    <div className="person">
      <span className="avatar">{person.initial}</span>
      <span>
        <strong>{person.name}</strong>
        <small>{person.id}</small>
      </span>
    </div>
  );
}
export default function DesignPreview() {
  const location = useLocation();
  const navigate = useNavigate();
  const section = location.pathname.split("/")[2] || "today";
  const [services, setServices] = useState(initialServices);
  const [selectedPatient, setSelectedPatient] = useState(people[0]);
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState("ทั้งหมด");
  const filtered = people.filter(
    (p) =>
      (p.name + p.id).includes(query) &&
      (section !== "today" || filter === "ทั้งหมด" || p.state === filter),
  );
  const flash = (message) => setNotice(message);
  useEffect(() => {
    setNotice("");
  }, [section]);
  const openPatient = (p) => {
    setSelectedPatient(p);
    setQuery("");
    navigate("/design/patients");
  };
  return (
    <div className="clinic-preview">
      <a className="skip" href="#workspace">
        ข้ามไปเนื้อหา
      </a>
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <img src="/brand/thasonyah-logo.jpg" alt="โลโก้ธสัญญา คลินิก" />
          </span>
          <div>
            <strong>ธสัญญา</strong>
            <small>คลินิกการแพทย์แผนไทย</small>
          </div>
        </div>
        <div className="branch-label">พื้นที่ทำงานคลินิก</div>
        <nav aria-label="เมนูต้นแบบ">
          {nav.map(([key, label]) => (
            <NavLink
              key={key}
              to={`/design/${key}`}
              className={({ isActive }) =>
                isActive ? "nav-item selected" : "nav-item"
              }
            >
              <Icon name={key} />
              <span>{label}</span>
              {key === "today" && <b>4</b>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <Icon name="leaf" />
          <p>
            ทุกการดูแล
            <br />
            <strong>เริ่มจากความเข้าใจ</strong>
          </p>
          <span>THASONYAH CLINIC</span>
        </div>
        <div className="staff">
          <span className="avatar">ท</span>
          <div>
            <strong>ทีมดูแลคลินิก</strong>
            <small>บัญชีแสดงตัวอย่าง</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            คลินิก /{" "}
            <strong>
              {nav.find((n) => n[0] === section)?.[1] || "งานวันนี้"}
            </strong>
          </span>
          <div className="topbar-right">
            <span className="branch-dot" />
            สาขาหลัก <span className="divider" />
            10 กันยายน 2569
          </div>
        </header>
        <div className="demo-strip">
          ต้นแบบสำหรับตรวจดีไซน์ · คนไข้สมมติ · ยังไม่บันทึกลงระบบจริง
        </div>
        <main id="workspace">
          <div className="page-heading">
            <div>
              <h1>
                {{
                  today: "ดูแลทุกนัดหมาย อย่างใส่ใจ",
                  calendar: "ตารางนัดหมาย",
                  patients: "ประวัติผู้รับบริการ",
                  treatment: "ห้องตรวจแพทย์แผนไทย",
                  services: "จัดการหัตถการ",
                  palette: "สีและองค์ประกอบธสัญญา",
                }[section] || "งานวันนี้"}
              </h1>
              <p>
                {
                  {
                    today:
                      "งานของคลินิกวันนี้ พร้อมให้ทีมดูแลต่อได้อย่างราบรื่น",
                    calendar: "เห็นเวลาของผู้รักษาและเตียงในที่เดียว",
                    patients: "ข้อมูลสำคัญและการดูแลต่อเนื่องในทุกครั้งที่มา",
                    treatment: "ตรวจ ประเมิน และวางแผนการดูแลอย่างเป็นลำดับ",
                    services: "เพิ่ม แก้ไขราคาและเวลา หรือปิดใช้งานหัตถการ",
                    palette: "เรียบ สะอาด อบอุ่น และอ่านได้ชัดในทุกหน้าจอ",
                  }[section]
                }
              </p>
            </div>
            {section === "today" && (
              <button
                className="primary"
                onClick={() => navigate("/design/calendar")}
              >
                <Icon name="plus" />
                ดูตารางนัดหมาย
              </button>
            )}
          </div>
          {notice && (
            <div className="notice" role="status">
              {notice}
              <button onClick={() => setNotice("")} aria-label="ปิดข้อความ">
                ปิด
              </button>
            </div>
          )}
          {section === "today" && (
            <>
              <div className="daily-summary">
                <div>
                  <strong>4</strong>
                  <span>นัดหมายวันนี้</span>
                </div>
                <div>
                  <strong>1</strong>
                  <span>รอเข้ารับบริการ</span>
                </div>
                <div>
                  <strong>1</strong>
                  <span>กำลังรับบริการ</span>
                </div>
                <div className="summary-note">
                  <Icon name="clock" />
                  <span>
                    นัดหมายถัดไป
                    <br />
                    <strong>10:00 น. · ตรวจติดตามอาการ</strong>
                  </span>
                </div>
              </div>
              <div className="today-grid">
                <section className="panel appointments">
                  <div className="panel-title">
                    <h2>นัดหมายและคิววันนี้</h2>
                    <span className="subtle">4 รายการ</span>
                  </div>
                  <div className="toolbar">
                    <div className="tabs" aria-label="กรองสถานะ">
                      {["ทั้งหมด", "รอเข้ารับบริการ", "กำลังรับบริการ"].map(
                        (f) => (
                          <button
                            key={f}
                            className={filter === f ? "current" : ""}
                            aria-pressed={filter === f}
                            onClick={() => setFilter(f)}
                          >
                            {f}
                          </button>
                        ),
                      )}
                    </div>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>เวลา / ผู้รับบริการ</th>
                          <th>บริการ</th>
                          <th>สถานะ</th>
                          <th>
                            <span className="sr-only">เปิดประวัติ</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((p) => (
                          <tr key={p.id}>
                            <td>
                              <div className="time-person">
                                <time>{p.time}</time>
                                <Person person={p} />
                              </div>
                            </td>
                            <td>
                              {p.service}
                              <small>
                                {p.doctor} · {p.bed}
                              </small>
                            </td>
                            <td>
                              <Badge tone={p.tone}>{p.state}</Badge>
                            </td>
                            <td>
                              <button
                                className="icon-button"
                                aria-label={`เปิดประวัติ ${p.id}`}
                                onClick={() => openPatient(p)}
                              >
                                <Icon name="arrow" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
                <aside className="next-patient">
                  <div className="next-top">
                    <Icon name="leaf" />
                    <span>พร้อมดูแลรายถัดไป</span>
                  </div>
                  <h2>
                    เริ่มการดูแล
                    <br />
                    ด้วยข้อมูลที่ครบถ้วน
                  </h2>
                  <Person />
                  <dl>
                    <div>
                      <dt>บริการ</dt>
                      <dd>นวดไทย 60 นาที</dd>
                    </div>
                    <div>
                      <dt>ผู้ดูแล</dt>
                      <dd>ผู้รักษา A</dd>
                    </div>
                    <div>
                      <dt>พื้นที่บริการ</dt>
                      <dd>เตียง 01</dd>
                    </div>
                  </dl>
                  <button
                    className="light-button"
                    onClick={() => {
                      setSelectedPatient(people[0]);
                      navigate("/design/treatment");
                    }}
                  >
                    เปิดหน้าตรวจ
                    <Icon name="arrow" />
                  </button>
                  <p className="next-foot">
                    ตรวจประวัติและข้อควรระวังก่อนเริ่มบริการ
                  </p>
                </aside>
              </div>
              <section className="bottom-note">
                <Icon name="check" />
                <div>
                  <strong>ข้อมูลการดูแล อยู่ในที่เดียวกัน</strong>
                  <p>จากประวัติคนไข้ สู่การตรวจรักษา และนัดติดตามครั้งต่อไป</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => navigate("/design/palette")}
                >
                  ดูคู่มือธีม <Icon name="arrow" />
                </button>
              </section>
            </>
          )}
          {section === "calendar" && (
            <section className="panel">
              <div className="panel-title">
                <div>
                  <h2>พฤหัสบดี 10 กันยายน 2569</h2>
                  <span className="subtle">
                    ตัวอย่างมุมมองรายวัน · 09:00–12:00 น.
                  </span>
                </div>
                <Badge tone="active">ผู้รักษา 2 คน</Badge>
              </div>
              <div className="calendar-scroll">
                <div className="calendar-grid">
                  <div className="calendar-head">เวลา</div>
                  <div className="calendar-head">
                    ผู้รักษา A <small>เตียง 01 / ห้องตรวจ</small>
                  </div>
                  <div className="calendar-head">
                    ผู้รักษา B <small>เตียง 02</small>
                  </div>
                  {["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"].map(
                    (time, i) => (
                      <div className="calendar-row" key={time}>
                        <time>{time}</time>
                        {[0, 1].map((col) => {
                          const p = people.find(
                            (p) =>
                              p.time === time &&
                              p.doctor === `ผู้รักษา ${col ? "B" : "A"}`,
                          );
                          const occupied =
                            (i === 1 && col === 0) || (i === 4 && col === 1);
                          return (
                            <div className="calendar-cell" key={col}>
                              {p ? (
                                <button
                                  className={`booking ${p.tone}`}
                                  onClick={() => openPatient(p)}
                                >
                                  <strong>{p.name}</strong>
                                  <span>{p.service}</span>
                                  <small>{p.bed}</small>
                                </button>
                              ) : occupied ? (
                                <span className="continuation">
                                  ต่อเนื่องจากช่วงก่อนหน้า
                                </span>
                              ) : (
                                <button
                                  className="open-slot"
                                  onClick={() =>
                                    flash(
                                      `ช่องเวลา ${time} น. — ตัวอย่างการเลือกเวลานัดหมาย ยังไม่สร้างนัดจริง`,
                                    )
                                  }
                                >
                                  เลือกเวลาว่าง
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ),
                  )}
                </div>
              </div>
            </section>
          )}
          {section === "patients" && (
            <>
              <label className="searchbox">
                <Icon name="search" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="ค้นหารหัสหรือชื่อในข้อมูลตัวอย่าง"
                  aria-label="ค้นหาคนไข้ตัวอย่าง"
                />
              </label>
              <div className="patient-grid">
                <section className="panel patient-list">
                  <h2>ผู้รับบริการตัวอย่าง</h2>
                  {filtered.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedPatient(p)}
                      aria-pressed={selectedPatient.id === p.id}
                    >
                      <Person person={p} />
                      <Icon name="arrow" />
                    </button>
                  ))}
                  {!filtered.length && (
                    <p className="empty">ไม่พบรายการ ลองค้นด้วย DEMO หรือ 01</p>
                  )}
                </section>
                <section className="panel record">
                  <div className="panel-title">
                    <Person person={selectedPatient} />
                    <Badge tone="active">ประวัติตัวอย่าง</Badge>
                  </div>
                  <div className="record-details">
                    <div>
                      <small>อายุ</small>
                      <strong>42 ปี (สมมติ)</strong>
                    </div>
                    <div>
                      <small>การติดตาม</small>
                      <strong>อาการคอ บ่า ไหล่</strong>
                    </div>
                    <div>
                      <small>การประเมินแพ้ยา</small>
                      <strong>ยังไม่ได้ประเมิน</strong>
                    </div>
                  </div>
                  <div className="clinical-alert">
                    ควรทบทวนประวัติแพ้ยาและยาที่ใช้อยู่ก่อนให้บริการ
                  </div>
                  <h2>ประวัติการดูแล</h2>
                  <div className="history-item">
                    <span className="history-date">
                      10 ก.ย.<small>2569</small>
                    </span>
                    <div>
                      <strong>นัดตรวจและนวดไทย</strong>
                      <p>รอผู้รักษาประเมินอาการก่อนเริ่มบริการ</p>
                    </div>
                    <Badge tone="waiting">วันนี้</Badge>
                  </div>
                  <div className="history-item">
                    <span className="history-date">
                      3 ก.ย.<small>2569</small>
                    </span>
                    <div>
                      <strong>ติดตามอาการคอ บ่า ไหล่</strong>
                      <p>ตัวอย่างบันทึกการรับบริการครั้งก่อน</p>
                    </div>
                  </div>
                  <div className="zodiac-note">
                    <Icon name="palette" />
                    <div>
                      <strong>จักรราศีสมุฏฐาน</strong>
                      <p>
                        บันทึกอัตโนมัติจากวันเกิดเมื่อเปิดใช้กฎที่ตรวจสอบแล้ว
                      </p>
                      <small>ต้นแบบนี้ยังไม่คำนวณราศีหรือสรุปผลวินิจฉัย</small>
                    </div>
                  </div>
                  <button
                    className="primary"
                    onClick={() => navigate("/design/treatment")}
                  >
                    ไปหน้าตรวจ <Icon name="arrow" />
                  </button>
                </section>
              </div>
            </>
          )}
          {section === "treatment" && (
            <Treatment
              flash={flash}
              person={selectedPatient}
              services={services}
              key={selectedPatient.id}
            />
          )}
          {section === "services" && <ServiceCatalog services={services} setServices={setServices} flash={flash} />}
          {section === "palette" && (
            <>
              <div className="palette-board">
                {[
                  [
                    "#2C398D",
                    "น้ำเงินครามธสัญญา",
                    "อิงโลโก้ · ปุ่มและการนำทาง",
                  ],
                  ["#F5F2EC", "ครีมกระดาษ", "อิงบรรยากาศภาพปก"],
                  ["#E9EDF5", "น้ำเงินหม่นอ่อน", "พื้นข้อมูลและพื้นที่ประกอบ"],
                  ["#A48D69", "ทรายธรรมชาติ", "รายละเอียดโทนอุ่นจากภาพปก"],
                ].map(([color, title, desc]) => (
                  <div key={color}>
                    <div
                      className="swatch"
                      style={{ backgroundColor: color }}
                    />
                    <h2>{title}</h2>
                    <p>{desc}</p>
                    <code>{color}</code>
                  </div>
                ))}
              </div>
              <div className="theme-grid">
                <section className="panel theme-sample">
                  <h2>ตัวอักษรที่อ่านได้ชัด</h2>
                  <p className="type-large">ดูแลอย่างเข้าใจ</p>
                  <p>
                    เว้นระยะให้ภาษาไทยอ่านง่าย ใช้ฟอนต์ไม่มีเชิงที่คุ้นเคย
                    และน้ำหนักช่วยแบ่งลำดับข้อมูล
                  </p>
                  <small>หัวเรื่อง 28 px · หัวข้อ 19 px · เนื้อหา 15 px</small>
                </section>
                <section className="panel theme-sample">
                  <h2>ปุ่มและสถานะ</h2>
                  <div className="sample-buttons">
                    <button
                      className="primary"
                      onClick={() =>
                        flash("ตัวอย่างปุ่มหลัก — ยังไม่บันทึกข้อมูลจริง")
                      }
                    >
                      บันทึกตัวอย่าง
                    </button>
                    <button className="secondary" onClick={() => setNotice("")}>
                      ยกเลิก
                    </button>
                    <button disabled>ยังไม่พร้อม</button>
                  </div>
                  <div className="sample-buttons">
                    <Badge tone="active">กำลังรับบริการ</Badge>
                    <Badge tone="waiting">รอรับบริการ</Badge>
                    <Badge tone="danger">ต้องตรวจสอบ</Badge>
                  </div>
                  <label className="field">
                    ตัวอย่างช่องกรอก
                    <input placeholder="ระบุข้อความ" />
                  </label>
                </section>
              </div>
            </>
          )}
        </main>
        <footer>
          ธสัญญา คลินิกการแพทย์แผนไทย{" "}
          <span>ต้นแบบภาพลักษณ์และหน้าจอ · เวอร์ชัน 01</span>
        </footer>
      </div>
    </div>
  );
}
function Treatment({ flash, person, services }) {
  const [tab, setTab] = useState("ซักประวัติ");
  const [note, setNote] = useState("");
  const [fields, setFields] = useState({});
  const bind = (name) => ({
    value: fields[name] || "",
    onChange: (e) => setFields({ ...fields, [name]: e.target.value }),
  });
  return (
    <>
      <div className="visit-banner">
        <Person person={person} />
        <span>รับบริการวันนี้ · {person.service}</span>
        <Badge tone="waiting">รอการประเมิน</Badge>
      </div>
      <div className="clinical-tabs">
        {["ซักประวัติ", "ตรวจและประเมิน", "แผนการดูแล"].map((t) => (
          <button
            className={t === tab ? "current" : ""}
            key={t}
            aria-pressed={t === tab}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="treatment-grid">
        <section className="panel form-panel">
          <h2>{tab}</h2>
          {tab === "ซักประวัติ" ? (
            <>
              <label className="field">
                อาการสำคัญ
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="ตัวอย่าง: บันทึกอาการที่ผู้รับบริการแจ้ง"
                  rows="4"
                />
              </label>
              <div className="field-row">
                <label className="field">
                  ระยะเวลาที่มีอาการ
                  <input {...bind("duration")} placeholder="เช่น 1 สัปดาห์" />
                </label>
                <label className="field">
                  คะแนนปวดก่อนรับบริการ
                  <select {...bind("pain")}>
                    <option value="">ยังไม่ได้ประเมิน</option>
                    {Array.from({ length: 11 }, (_, i) => (
                      <option key={i}>{i}</option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="field">
                ประวัติสุขภาพและสิ่งที่เกี่ยวข้อง
                <textarea
                  {...bind("history")}
                  rows="3"
                  placeholder="อาหาร การนอน การขับถ่าย อิริยาบถ และยาที่ใช้อยู่"
                />
              </label>
            </>
          ) : tab === "ตรวจและประเมิน" ? (
            <>
              <p className="subtle">ผลตรวจและการตีความตามตำราแยกบันทึกจากกัน</p>
              <label className="field">
                ผลตรวจร่างกาย
                <textarea
                  {...bind("exam")}
                  rows="4"
                  placeholder="บันทึกผลตรวจที่พบ"
                />
              </label>
              <label className="field">
                การประเมินธาตุและสมุฏฐาน
                <textarea
                  {...bind("assessment")}
                  rows="3"
                  placeholder="ระบุผลประเมิน เหตุผล และตำราที่อ้างอิง"
                />
              </label>
            </>
          ) : (
            <>
              <label className="field">
                เป้าหมายการดูแล
                <textarea
                  {...bind("goals")}
                  rows="4"
                  placeholder="ระบุเป้าหมายที่ตกลงกับผู้รับบริการ"
                />
              </label>
              <label className="field">
                คำแนะนำและการติดตาม
                <textarea
                  {...bind("advice")}
                  rows="3"
                  placeholder="ร่างคำแนะนำสำหรับผู้รักษาตรวจยืนยัน"
                />
              </label>
            </>
          )}
          {tab === "แผนการดูแล" && <label className="field">หัตถการจากรายการคลินิก<select {...bind("serviceId")}><option value="">เลือกหัตถการ</option>{services.filter(s => s.active || s.id === fields.serviceId).map(s => <option key={s.id} value={s.id} disabled={!s.active}>{s.name} · {s.price.toLocaleString("th-TH")} บาท · {s.minutes} นาที{!s.active ? " (ปิดใช้งาน)" : ""}</option>)}</select></label>}
          <OpdFields tab={tab} fields={fields} bind={bind} />
          <div className="form-actions">
            <span>ข้อมูลในฟอร์มนี้เป็นตัวอย่าง</span>
            <button
              className="primary"
              onClick={() =>
                flash(
                  "แสดงตัวอย่างการบันทึกแล้ว — ไม่มีการส่งหรือเก็บข้อมูลลงระบบจริง",
                )
              }
            >
              <Icon name="check" />
              ทดลองบันทึกร่าง
            </button>
          </div>
        </section>
        <aside className="panel context-panel">
          <h2>ข้อมูลประกอบการดูแล</h2>
          <div className="context-block">
            <strong>ประวัติแพ้ยา</strong>
            <Badge tone="waiting">ยังไม่ได้ประเมิน</Badge>
            <p>ทบทวนข้อมูลกับผู้รับบริการก่อนเริ่มรักษา</p>
          </div>
          <div className="context-block">
            <strong>จักรราศีสมุฏฐาน</strong>
            <p>ระบบจะใช้วันเกิดในทะเบียนคำนวณและบันทึกให้อัตโนมัติ</p>
            <span className="subtle">รอตรวจสอบกฎจากเอกสารต้นฉบับ</span>
          </div>
          <div className="context-block">
            <strong>ผู้ยืนยันบันทึก</strong>
            <p>ผู้รักษาที่ได้รับมอบหมาย</p>
            <small>ฉบับที่ลงนามแล้วจะเก็บประวัติการแก้ไข</small>
          </div>
        </aside>
      </div>
    </>
  );
}
