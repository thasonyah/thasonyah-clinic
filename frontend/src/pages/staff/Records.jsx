import { useEffect, useState } from "react";
import { api } from "../../api/client";
import BodyMap from "../../components/BodyMap";
import OpdFields from "../design/OpdFields";

const blankPatient = () => ({
  name: "",
  birth_date: "",
  birth_lunar_month: "",
  birth_lunar_phase: "",
  gestation_months: "",
  phone: "",
  provider_id: "",
  address: "",
  allergies: "",
  emergency_contact: "",
});
const blankNote = () => ({ chief_complaint: "", notes: "", opd: {} });

function ZodiacSummary({ snapshot }) {
  if (!snapshot || snapshot.status !== "calculated") {
    return (
      <p className="subtle">
        จักรราศี: รอข้อมูลเดือนจันทรคติ ช่วงเกิด และจำนวนเดือนในครรภ์
      </p>
    );
  }
  const birth = snapshot.birth_element;
  const waxing = snapshot.conception_element?.waxing;
  const waning = snapshot.conception_element?.waning;
  return (
    <div className="notice zodiac-summary">
      <strong>จักรราศีสมุฏฐาน</strong>
      <p>
        แรกคลอด เดือน {snapshot.birth_month} {snapshot.birth_phase}: {birth.element} · {birth.condition} · {birth.mixed_with}
      </p>
      <p>
        เดือนปฏิสนธิ {snapshot.conception_month} จากอยู่ในครรภ์ {snapshot.gestation_months} เดือน
      </p>
      <p>
        ปฏิสนธิข้างขึ้น: {waxing.element} · {waxing.condition} · {waxing.mixed_with}
      </p>
      <p>
        ปฏิสนธิข้างแรม: {waning.element} · {waning.condition} · {waning.mixed_with}
      </p>
      <small>
        บันทึกอัตโนมัติจากกฎ thai-traditional-birth-and-conception-elements-v2 ไม่ใช้แทนการวินิจฉัย
      </small>
    </div>
  );
}

export function ageAt(birth, today = new Date()) {
  if (!birth) return null;
  const [y, m, d] = birth.split("-").map(Number);
  return (
    today.getFullYear() -
    y -
    (today.getMonth() + 1 < m ||
    (today.getMonth() + 1 === m && today.getDate() < d)
      ? 1
      : 0)
  );
}
export default function Records({ token, user, onError, onDirty, onBusy }) {
  const [patientEditing, setPatientEditing] = useState(null);
  const [patients, setPatients] = useState([]),
    [providers, setProviders] = useState([]),
    [selected, setSelected] = useState(null),
    [visits, setVisits] = useState([]),
    [consents, setConsents] = useState([]);
  const [query, setQuery] = useState(""),
    [draft, setDraft] = useState(blankPatient),
    [note, setNote] = useState(blankNote),
    [editing, setEditing] = useState(null),
    [baseline, setBaseline] = useState(JSON.stringify(blankNote()));
  const [tab, setTab] = useState("ซักประวัติ"),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [confirmSign, setConfirmSign] = useState(null);
  const [amendments, setAmendments] = useState({}),
    [amendId, setAmendId] = useState(null),
    [amend, setAmend] = useState({ reason: "", text: "" });
  const [consentDraft, setConsentDraft] = useState({
    file: null,
    note: "",
    visit_id: "",
  });
  const dirty =
    Object.values(draft).some(Boolean) ||
    JSON.stringify(note) !== baseline ||
    Boolean(amend.reason || amend.text) ||
    Boolean(consentDraft.file || consentDraft.note);
  const config = { headers: { Authorization: `Bearer ${token}` } };
  useEffect(() => {
    onDirty(dirty);
  }, [dirty, onDirty]);
  useEffect(() => {
    if (!dirty) return;
    const warn = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  useEffect(() => {
    let opened = [];
    const before = () => {
      opened = [...document.querySelectorAll(".saved-opd")].filter(
        (x) => !x.open,
      );
      opened.forEach((x) => {
        x.open = true;
      });
    };
    const after = () => {
      opened.forEach((x) => {
        x.open = false;
      });
    };
    window.addEventListener("beforeprint", before);
    window.addEventListener("afterprint", after);
    return () => {
      window.removeEventListener("beforeprint", before);
      window.removeEventListener("afterprint", after);
    };
  }, []);
  const explain = (e) =>
    ({
      403: "บัญชีนี้ไม่มีสิทธิ์เข้าถึงทะเบียนหรือบันทึกนี้",
      404: "ไม่พบบันทึกหรือคุณไม่ได้รับมอบหมาย กรุณาโหลดรายการใหม่",
      409: "บันทึกมีการเปลี่ยนแปลงหรือยืนยันแล้ว กรุณาเปิดข้อมูลล่าสุด",
      422: "ตรวจช่องข้อมูล วันเกิด ค่าสัญญาณชีพ และความยาวข้อความอีกครั้ง",
    })[e.response?.status] || onError(e);
  const run = async (action) => {
    setBusy(true);
    onBusy(true);
    setMessage("");
    try {
      await action();
    } catch (e) {
      setMessage(explain(e));
    } finally {
      setBusy(false);
      onBusy(false);
    }
  };
  const resetNote = () => {
    setNote(blankNote());
    setBaseline(JSON.stringify(blankNote()));
    setEditing(null);
  };
  const load = async () => {
    const result = await api.get("/patients", {
      ...config,
      params: { q: query, limit: 100 },
    });
    setPatients(result.data);
  };
  useEffect(() => {
    run(async () => {
      await load();
      if (user.role === "reception")
        setProviders((await api.get("/patients/providers", config)).data);
    });
  }, [token, user.role]);
  const loadVisits = async (p) => {
    const result = await api.get(`/patients/${p.id}/visits`, config);
    setVisits(result.data);
    const history = await Promise.all(
      result.data
        .filter((v) => v.signed_at)
        .map(async (v) => [
          v.id,
          (await api.get(`/visits/${v.id}/amendments`, config)).data,
        ]),
    );
    setAmendments(Object.fromEntries(history));
  };
  const loadConsents = async (p) => {
    setConsents((await api.get(`/patients/${p.id}/consents`, config)).data);
  };
  const openPatient = async (p) => {
    setSelected(null);
    setConsents([]);
    setConsentDraft({ file: null, note: "", visit_id: "" });
    if (user.role === "practitioner") await loadVisits(p);
    else {
      setVisits([]);
      setAmendments({});
    }
    await loadConsents(p);
    setSelected(p);
    resetNote();
    setAmendId(null);
    setConfirmSign(null);
  };
  const downloadConsent = async (item) => {
    const result = await api.get(`/patients/${selected.id}/consents/${item.id}`, {
      ...config,
      responseType: "blob",
    });
    const url = URL.createObjectURL(result.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = item.filename;
    link.click();
    URL.revokeObjectURL(url);
  };
  const field = (label, key, type = "text") => (
    <label className="field">
      {label}
      <input
        type={type}
        value={draft[key]}
        maxLength={key === "name" ? 200 : key === "phone" ? 40 : 2000}
        required={key === "name"}
        onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
      />
    </label>
  );
  return (
    <section aria-busy={busy}>
      <fieldset className="module-fields" disabled={busy}>
        <div className="no-print">
          <h2>ทะเบียนและบันทึกการตรวจ</h2>
          <p className="subtle">
            {user.role === "practitioner"
              ? "คนไข้ที่ได้รับมอบหมายให้คุณดูแล"
              : "ลงทะเบียนคนไข้และเลือกผู้รักษาที่รับผิดชอบ"}
          </p>
          {message && (
            <p className="notice" role="status">
              {message}
            </p>
          )}
          {dirty && (
            <div className="notice">
              <p>
                มีข้อมูลที่ยังไม่บันทึก
                กรุณาบันทึกหรือละทิ้งก่อนเปลี่ยนคนไข้หรือเมนู
              </p>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => {
                  resetNote();
                  setDraft(blankPatient());
                  setPatientEditing(null);
                  setAmend({ reason: "", text: "" });
                  setAmendId(null);
                  setConsentDraft({ file: null, note: "", visit_id: "" });
                }}
              >
                ละทิ้งข้อมูลที่ยังไม่บันทึก
              </button>
            </div>
          )}
          {user.role === "reception" && (
            <details
              className="opd-section"
              open={patientEditing ? true : undefined}
            >
              <summary>
                {patientEditing
                  ? `แก้ไขทะเบียน · ${patientEditing.name}`
                  : "ลงทะเบียนคนไข้ใหม่"}
              </summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(async () => {
                    const payload = {
                      ...draft,
                      birth_date: draft.birth_date || null,
                      birth_lunar_month: draft.birth_lunar_month || null,
                      birth_lunar_phase: draft.birth_lunar_phase || null,
                      gestation_months: draft.gestation_months || null,
                    };
                    if (patientEditing)
                      await api.patch(
                        `/patients/${patientEditing.id}`,
                        {
                          ...payload,
                          expected_version: patientEditing.version,
                        },
                        config,
                      );
                    else await api.post("/patients", payload, config);
                    setPatientEditing(null);
                    setDraft(blankPatient());
                    await load();
                    setMessage("บันทึกทะเบียนแล้ว");
                  });
                }}
              >
                <div className="field-row">
                  {field("ชื่อ–นามสกุล", "name")}
                  {field("วันเกิด (ค.ศ.)", "birth_date", "date")}
                  <label className="field">
                    เดือนเกิดจันทรคติ
                    <select
                      value={draft.birth_lunar_month}
                      onChange={(e) =>
                        setDraft({ ...draft, birth_lunar_month: e.target.value })
                      }
                    >
                      <option value="">ยังไม่ทราบ</option>
                      {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                        <option key={m} value={m}>
                          เดือน {m}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    ช่วงเกิด
                    <select
                      value={draft.birth_lunar_phase}
                      onChange={(e) =>
                        setDraft({ ...draft, birth_lunar_phase: e.target.value })
                      }
                    >
                      <option value="">ยังไม่ทราบ</option>
                      <option value="ข้างขึ้น">ข้างขึ้น</option>
                      <option value="ข้างแรม">ข้างแรม</option>
                    </select>
                  </label>
                  <label className="field">
                    อยู่ในครรภ์กี่เดือน
                    <select
                      value={draft.gestation_months}
                      onChange={(e) =>
                        setDraft({ ...draft, gestation_months: e.target.value })
                      }
                    >
                      <option value="">ยังไม่ทราบ</option>
                      {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                        <option key={m} value={m}>
                          {m} เดือน
                        </option>
                      ))}
                    </select>
                  </label>
                  {field("โทรศัพท์", "phone", "tel")}
                  <label className="field">
                    ผู้รักษา
                    <select
                      required
                      disabled={Boolean(patientEditing)}
                      value={draft.provider_id}
                      onChange={(e) =>
                        setDraft({ ...draft, provider_id: e.target.value })
                      }
                    >
                      <option value="">เลือกผู้รักษา</option>
                      {providers.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.email}
                        </option>
                      ))}
                    </select>
                  </label>
                  {field("ที่อยู่", "address")}
                  {field(
                    "ประวัติแพ้ยา / อาการแพ้ (ระบุไม่ทราบได้)",
                    "allergies",
                  )}
                  {field("ผู้ติดต่อฉุกเฉินและโทรศัพท์", "emergency_contact")}
                </div>
                {!providers.length && (
                  <p>ให้ผู้ดูแลเพิ่มบัญชีผู้รักษาก่อนลงทะเบียน</p>
                )}
                <div className="form-actions">
                  <button
                    className="primary"
                    disabled={busy || !providers.length}
                  >
                    บันทึกทะเบียน
                  </button>
                </div>
              </form>
            </details>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              run(load);
            }}
          >
            <label className="field">
              ค้นหาชื่อ เบอร์โทร หรือรหัสคนไข้
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
            <div className="form-actions">
              <button className="secondary" disabled={busy}>
                ค้นหา / โหลดล่าสุด
              </button>
            </div>
          </form>
          <ul className="service-list">
            {patients.map((p) => (
              <li key={p.id}>
                <div>
                  <strong>{p.name}</strong>
                  <p>
                    วันเกิด {p.birth_date || "ไม่ทราบ"} ·{" "}
                    {p.phone || "ไม่มีเบอร์โทร"}
                  </p>
                </div>
                {user.role === "reception" && (
                  <div className="service-actions">
                    <button
                      className="secondary"
                      disabled={busy || dirty}
                      onClick={() => run(async () => openPatient(p))}
                    >
                      เอกสารของ {p.name}
                    </button>
                    <button
                      className="secondary"
                      disabled={busy || dirty}
                      onClick={() => {
                        setPatientEditing(p);
                        setDraft(
                          Object.fromEntries(
                            Object.keys(blankPatient()).map((k) => [
                              k,
                              p[k] || "",
                            ]),
                          ),
                        );
                      }}
                    >
                      แก้ไขทะเบียนของ {p.name}
                    </button>
                  </div>
                )}
                {user.role === "practitioner" && (
                  <button
                    className="secondary"
                    disabled={busy || dirty}
                    onClick={() => run(async () => openPatient(p))}
                  >
                    เปิดบันทึกของ {p.name}
                  </button>
                )}
              </li>
            ))}
          </ul>
          {!patients.length && <p>ไม่พบคนไข้ในรายการที่คุณมีสิทธิ์เข้าถึง</p>}
          <p className="subtle">แสดงสูงสุด 100 รายการต่อการค้นหา</p>
        </div>
        {selected && (
          <section className="panel form-panel">
            <h2>ใบบันทึกประวัติ · {selected.name}</h2>
            <p>
              วันเกิด {selected.birth_date || "ไม่ทราบ"} · อายุ{" "}
              {ageAt(selected.birth_date) ?? "ไม่ทราบ"} ปี · โทร{" "}
              {selected.phone || "ไม่ทราบ"}
            </p>
            <p>แพ้ยา: {selected.allergies || "ยังไม่บันทึก"}</p>
            <ZodiacSummary snapshot={selected.zodiac_snapshot} />
            <div className="no-print">
              <h3>เอกสารยินยอมและไฟล์แนบ</h3>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(async () => {
                    const data = new FormData();
                    data.append("file", consentDraft.file);
                    data.append("note", consentDraft.note);
                    if (consentDraft.visit_id)
                      data.append("visit_id", consentDraft.visit_id);
                    await api.post(`/patients/${selected.id}/consents`, data, {
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    setConsentDraft({ file: null, note: "", visit_id: "" });
                    await loadConsents(selected);
                    setMessage("แนบเอกสารยินยอมแล้ว");
                  });
                }}
              >
                <div className="field-row">
                  <label className="field">
                    ไฟล์ PDF / JPEG / PNG ไม่เกิน 5 MB
                    <input
                      type="file"
                      accept="application/pdf,image/jpeg,image/png"
                      required
                      onChange={(e) =>
                        setConsentDraft({
                          ...consentDraft,
                          file: e.target.files?.[0] || null,
                        })
                      }
                    />
                  </label>
                  {user.role === "practitioner" && (
                    <label className="field">
                      ผูกกับการตรวจ
                      <select
                        value={consentDraft.visit_id}
                        onChange={(e) =>
                          setConsentDraft({
                            ...consentDraft,
                            visit_id: e.target.value,
                          })
                        }
                      >
                        <option value="">แนบกับประวัติคนไข้เท่านั้น</option>
                        {visits.map((v) => (
                          <option key={v.id} value={v.id}>
                            {new Date(v.created_at).toLocaleString("th-TH")} ·{" "}
                            {v.chief_complaint}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                </div>
                <label className="field">
                  หมายเหตุเอกสาร
                  <textarea
                    maxLength="1000"
                    value={consentDraft.note}
                    onChange={(e) =>
                      setConsentDraft({ ...consentDraft, note: e.target.value })
                    }
                  />
                </label>
                <div className="form-actions">
                  <button
                    className="primary"
                    disabled={busy || !consentDraft.file}
                  >
                    แนบเอกสารยินยอม
                  </button>
                </div>
              </form>
            </div>
            {consents.length > 0 && (
              <ul className="service-list">
                {consents.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.filename}</strong>
                      <p>
                        {new Date(item.created_at).toLocaleString("th-TH")} ·{" "}
                        {(item.size_bytes / 1024).toFixed(1)} KB ·{" "}
                        {item.content_type}
                      </p>
                      {item.note && <p className="record-text">{item.note}</p>}
                    </div>
                    <button
                      className="secondary no-print"
                      disabled={busy}
                      onClick={() => run(async () => downloadConsent(item))}
                    >
                      ดาวน์โหลด
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="no-print">
              <div className="form-actions">
                {user.role === "practitioner" && (
                  <button
                    className="secondary"
                    disabled={busy || dirty}
                    onClick={() =>
                      run(async () => {
                        await api.post(
                          `/patients/${selected.id}/print-log`,
                          {},
                          config,
                        );
                        window.print();
                      })
                    }
                  >
                    พิมพ์ประวัติ / บันทึก PDF
                  </button>
                )}
              </div>
              {user.role === "practitioner" && (
                <>
                  <h3>
                    {editing ? "แก้ไขร่างการตรวจ" : "บันทึกการตรวจครั้งใหม่"}
                  </h3>
                  <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(async () => {
                    const result = editing
                      ? await api.patch(
                          `/visits/${editing.id}`,
                          { ...note, expected_version: editing.version },
                          config,
                        )
                      : await api.post(
                          `/patients/${selected.id}/visits`,
                          note,
                          config,
                        );
                    setVisits((rows) =>
                      editing
                        ? rows.map((v) =>
                            v.id === editing.id ? result.data : v,
                          )
                        : [result.data, ...rows],
                    );
                    resetNote();
                    setMessage("บันทึกฉบับร่างลงฐานข้อมูลแล้ว");
                  });
                }}
              >
                <fieldset disabled={busy}>
                  <label className="field">
                    อาการสำคัญ
                    <textarea
                      required
                      maxLength="2000"
                      value={note.chief_complaint}
                      onChange={(e) =>
                        setNote({ ...note, chief_complaint: e.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    บันทึกเพิ่มเติม
                    <textarea
                      maxLength="20000"
                      value={note.notes}
                      onChange={(e) =>
                        setNote({ ...note, notes: e.target.value })
                      }
                    />
                  </label>
                  <nav className="clinical-tabs" aria-label="หมวดใบบันทึก">
                    {["ซักประวัติ", "ตรวจและประเมิน", "แผนการดูแล"].map((t) => (
                      <button
                        type="button"
                        key={t}
                        aria-pressed={tab === t}
                        onClick={() => setTab(t)}
                      >
                        {t}
                      </button>
                    ))}
                  </nav>
                  <OpdFields
                    disabled={busy}
                    key={editing?.id || "new"}
                    live
                    tab={tab}
                    fields={note.opd}
                    bind={(label) => ({
                      value: note.opd[label] || "",
                      onChange: (e) =>
                        setNote({
                          ...note,
                          opd: { ...note.opd, [label]: e.target.value },
                        }),
                    })}
                  />
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      {editing ? "บันทึกการแก้ไขร่าง" : "เก็บร่างการตรวจ"}
                    </button>
                    {editing && (
                      <button
                        type="button"
                        className="secondary"
                        disabled={dirty}
                        onClick={resetNote}
                      >
                        ปิดการแก้ไข
                      </button>
                    )}
                  </div>
                </fieldset>
                  </form>
                </>
              )}
            </div>
            {user.role === "practitioner" && <h3>ประวัติการตรวจ</h3>}
            {visits.map((v) => (
              <article className="opd-section" key={v.id}>
                <h3>
                  {new Date(v.created_at).toLocaleString("th-TH")} ·{" "}
                  {v.signed_at ? "ยืนยันแล้ว" : "ฉบับร่าง"} · รุ่น {v.version}
                </h3>
                <p>ผู้บันทึก {user.email}</p>
                <p>{v.chief_complaint}</p>
                <p className="record-text">{v.notes}</p>
                {v.bmi && <p>BMI: {v.bmi} กก./ม²</p>}
                <details className="saved-opd">
                  <summary>รายละเอียด OPD ที่บันทึก</summary>
                  <dl>
                    {Object.entries(v.opd || {})
                      .filter(([, val]) => val)
                      .map(([k, val]) => (
                        <div key={k}>
                          <dt>{k}</dt>
                          <dd className="record-text">
                            {k === "ผังตำแหน่งปวด" ? (
                              <BodyMap readOnly value={val} />
                            ) : (
                              val
                            )}
                          </dd>
                        </div>
                      ))}
                  </dl>
                </details>
                {(amendments[v.id] || []).map((a) => (
                  <div key={a.id}>
                    <strong>
                      เพิ่มเติม {new Date(a.created_at).toLocaleString("th-TH")}
                    </strong>
                    <p>เหตุผล: {a.reason}</p>
                    <p className="record-text">{a.text}</p>
                  </div>
                ))}
                <div className="no-print form-actions">
                  {!v.signed_at ? (
                    <>
                      <button
                        className="secondary"
                        disabled={busy || dirty}
                        onClick={() => {
                          const next = {
                            chief_complaint: v.chief_complaint,
                            notes: v.notes,
                            opd: v.opd || {},
                          };
                          setNote(next);
                          setBaseline(JSON.stringify(next));
                          setEditing(v);
                          setConfirmSign(null);
                        }}
                      >
                        แก้ไขร่าง
                      </button>
                      <button
                        className="secondary"
                        disabled={busy || dirty}
                        onClick={() => setConfirmSign(v.id)}
                      >
                        ตรวจทานและยืนยัน
                      </button>
                    </>
                  ) : (
                    <button
                      className="secondary"
                      disabled={busy || dirty}
                      onClick={() => {
                        setAmendId(v.id);
                        setAmend({ reason: "", text: "" });
                      }}
                    >
                      เพิ่มบันทึกแนบท้าย
                    </button>
                  )}
                </div>
                {confirmSign === v.id && (
                  <div className="notice no-print">
                    <p>
                      ตรวจทานชื่อคนไข้และรายละเอียดทุกช่องก่อนยืนยัน
                      ฉบับยืนยันแก้ทับไม่ได้ แต่เพิ่มบันทึกแนบท้ายได้
                    </p>
                    <button
                      className="primary"
                      disabled={busy || dirty}
                      onClick={() =>
                        run(async () => {
                          const r = await api.post(
                            `/visits/${v.id}/sign`,
                            { expected_version: v.version },
                            config,
                          );
                          setVisits((rows) =>
                            rows.map((x) => (x.id === v.id ? r.data : x)),
                          );
                          if (editing?.id === v.id) resetNote();
                          setConfirmSign(null);
                          setMessage("ยืนยันบันทึกแล้ว");
                        })
                      }
                    >
                      ยืนยันฉบับนี้
                    </button>{" "}
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => setConfirmSign(null)}
                    >
                      กลับไปตรวจทาน
                    </button>
                  </div>
                )}
                {amendId === v.id && (
                  <form
                    className="no-print"
                    onSubmit={(e) => {
                      e.preventDefault();
                      run(async () => {
                        const r = await api.post(
                          `/visits/${v.id}/amendments`,
                          amend,
                          config,
                        );
                        setAmendments((all) => ({
                          ...all,
                          [v.id]: [...(all[v.id] || []), r.data],
                        }));
                        setAmend({ reason: "", text: "" });
                        setAmendId(null);
                        setMessage("เก็บบันทึกแนบท้ายโดยคงฉบับเดิมแล้ว");
                      });
                    }}
                  >
                    <label className="field">
                      เหตุผลที่เพิ่มเติม
                      <input
                        required
                        maxLength="1000"
                        value={amend.reason}
                        onChange={(e) =>
                          setAmend({ ...amend, reason: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      ข้อความแนบท้าย
                      <textarea
                        required
                        maxLength="20000"
                        value={amend.text}
                        onChange={(e) =>
                          setAmend({ ...amend, text: e.target.value })
                        }
                      />
                    </label>
                    <div className="form-actions">
                      <button className="primary" disabled={busy}>
                        บันทึกแนบท้าย
                      </button>
                    </div>
                  </form>
                )}
              </article>
            ))}
          </section>
        )}
      </fieldset>
    </section>
  );
}
