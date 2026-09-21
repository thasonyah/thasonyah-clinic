import { useEffect, useState } from "react";
import { api } from "../../api/client";

export const bangkokDate = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Bangkok",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
const names = {
  booked: "นัดหมายแล้ว",
  arrived: "รอตรวจ",
  in_service: "กำลังรับบริการ",
  completed: "เสร็จสิ้น",
  cancelled: "ยกเลิก",
};
const actions = {
  reception: { booked: ["arrived", "cancelled"], arrived: ["cancelled"] },
  practitioner: { arrived: ["in_service"], in_service: ["completed"] },
};
const actionNames = {
  arrived: "รับเข้าคิว",
  in_service: "เริ่มบริการ",
  completed: "จบบริการ",
  cancelled: "ยกเลิกนัด",
};
export default function Scheduling({ token, user, onError, onDirty, onBusy }) {
  const [day, setDay] = useState(bangkokDate),
    [appointments, setAppointments] = useState([]),
    [patients, setPatients] = useState([]),
    [resources, setResources] = useState([]);
  const [name, setName] = useState(""),
    [query, setQuery] = useState(""),
    [draft, setDraft] = useState({
      patient_id: "",
      resource_id: "",
      time: "09:00",
      minutes: 60,
      request_id: crypto.randomUUID(),
    });
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [cancel, setCancel] = useState(null);
  const [moving, setMoving] = useState(null);
  const config = { headers: { Authorization: `Bearer ${token}` } },
    dirty = Boolean(draft.patient_id || name || moving);
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
  const run = async (action) => {
    setBusy(true);
    onBusy(true);
    setMessage("");
    try {
      await action();
    } catch (e) {
      setMessage(
        e.response?.status === 409
          ? "เวลานี้มีนัดซ้อน หรือสถานะเปลี่ยนแล้ว กรุณาโหลดรายการล่าสุดแล้วเลือกใหม่"
          : e.response?.status === 422
            ? "ตรวจวัน เวลา ระยะเวลา และห้อง/เตียงอีกครั้ง"
            : onError(e),
      );
    } finally {
      setBusy(false);
      onBusy(false);
    }
  };
  const load = async () => {
    setResources((await api.get("/resources", config)).data);
    if (user.role !== "admin")
      setAppointments(
        (await api.get("/appointments", { ...config, params: { day } })).data,
      );
  };
  const search = async () =>
    setPatients(
      (
        await api.get("/patients", {
          ...config,
          params: { q: query, limit: 100 },
        })
      ).data,
    );
  useEffect(() => {
    run(async () => {
      await load();
      if (user.role === "reception") await search();
    });
  }, [token, day]);
  const change = (a, status) =>
    run(async () => {
      const r = await api.patch(
        `/appointments/${a.id}/status`,
        { status, expected_version: a.version },
        config,
      );
      setAppointments((rows) => rows.map((x) => (x.id === a.id ? r.data : x)));
      setCancel(null);
      setMessage("อัปเดตสถานะแล้ว");
    });
  return (
    <section aria-busy={busy}>
      <fieldset className="module-fields" disabled={busy}>
        <h2>{user.role === "admin" ? "ห้องและเตียง" : "นัดหมายและคิว"}</h2>
        <p className="subtle">
          เวลาไทย (Asia/Bangkok) · ตรวจเวลาซ้อนของคนไข้ ผู้รักษา และห้อง/เตียง
        </p>
        {message && (
          <p className="notice" role="status">
            {message}
          </p>
        )}
        {dirty && (
          <div className="notice">
            <p>มีข้อมูลที่ยังไม่บันทึก</p>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => {
                setName("");
                setMoving(null);
                setDraft({
                  ...draft,
                  patient_id: "",
                  request_id: crypto.randomUUID(),
                });
              }}
            >
              ละทิ้งรายการที่ยังไม่บันทึก
            </button>
          </div>
        )}
        {user.role === "admin" ? (
          <>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                run(async () => {
                  await api.post("/resources", { name }, config);
                  setName("");
                  await load();
                  setMessage("เพิ่มห้อง/เตียงแล้ว");
                });
              }}
            >
              <label className="field">
                ชื่อห้องหรือเตียง
                <input
                  required
                  maxLength="150"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <div className="form-actions">
                <button className="primary" disabled={busy}>
                  เพิ่มห้อง/เตียง
                </button>
              </div>
            </form>
            <ul className="service-list">
              {resources.map((r) => (
                <li key={r.id}>
                  <div>
                    <strong>{r.name}</strong>
                    <p>
                      {r.active ? "เปิดรับนัดใหม่" : "ปิดรับนัดใหม่"} ·
                      นัดเดิมคงอยู่
                    </p>
                  </div>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() =>
                      run(async () => {
                        await api.patch(
                          `/resources/${r.id}/status`,
                          { active: !r.active },
                          config,
                        );
                        await load();
                        setMessage("อัปเดตห้อง/เตียงแล้ว");
                      })
                    }
                  >
                    {r.active ? "ปิดรับนัดใหม่" : "เปิดรับนัดใหม่"}
                  </button>
                </li>
              ))}
            </ul>
            {!resources.length && (
              <p>
                ยังไม่มีห้องหรือเตียง
                เพิ่มชื่อทรัพยากรที่คลินิกใช้ร่วมกันเพื่อป้องกันจองซ้อน
              </p>
            )}
          </>
        ) : (
          <>
            <div className="field-row">
              <label className="field">
                วันที่ดูคิว (ค.ศ.)
                <input
                  type="date"
                  required
                  value={day}
                  disabled={busy || dirty}
                  onChange={(e) => {
                    if (e.target.value) setDay(e.target.value);
                  }}
                />
              </label>
              <div className="form-actions">
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => run(load)}
                >
                  โหลดคิวล่าสุด
                </button>
              </div>
            </div>
            {user.role === "reception" && (
              <details className="opd-section">
                <summary>สร้างนัดหมาย</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(search);
                  }}
                >
                  <label className="field">
                    ค้นหาคนไข้ก่อนเลือก
                    <input
                      type="search"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </label>
                  <div className="form-actions">
                    <button className="secondary" disabled={busy}>
                      ค้นหาคนไข้
                    </button>
                  </div>
                </form>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(async () => {
                      const start = new Date(`${day}T${draft.time}:00+07:00`);
                      const r = await api.post(
                        "/appointments",
                        {
                          patient_id: draft.patient_id,
                          resource_id: draft.resource_id || null,
                          request_id: draft.request_id,
                          starts_at: start.toISOString(),
                          ends_at: new Date(
                            start.getTime() + Number(draft.minutes) * 60000,
                          ).toISOString(),
                        },
                        config,
                      );
                      setDraft({
                        ...draft,
                        patient_id: "",
                        request_id: crypto.randomUUID(),
                      });
                      await load();
                      setMessage(
                        `บันทึกนัดหมายของ ${r.data.patient_name} แล้ว`,
                      );
                    });
                  }}
                >
                  <div className="field-row">
                    <label className="field">
                      คนไข้
                      <select
                        required
                        value={draft.patient_id}
                        onChange={(e) =>
                          setDraft({ ...draft, patient_id: e.target.value })
                        }
                      >
                        <option value="">เลือกคนไข้</option>
                        {patients.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} ·{" "}
                            {p.phone || p.birth_date || p.id.slice(0, 8)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      เวลาเริ่ม
                      <input
                        required
                        type="time"
                        value={draft.time}
                        onChange={(e) =>
                          setDraft({ ...draft, time: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      ระยะเวลา (นาที)
                      <input
                        required
                        type="number"
                        min="1"
                        max="480"
                        value={draft.minutes}
                        onChange={(e) =>
                          setDraft({ ...draft, minutes: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      ห้อง / เตียง
                      <select
                        value={draft.resource_id}
                        onChange={(e) =>
                          setDraft({ ...draft, resource_id: e.target.value })
                        }
                      >
                        <option value="">ไม่ใช้ห้อง/เตียงร่วม</option>
                        {resources
                          .filter((r) => r.active)
                          .map((r) => (
                            <option key={r.id} value={r.id}>
                              {r.name}
                            </option>
                          ))}
                      </select>
                    </label>
                  </div>
                  <p className="subtle">
                    ใช้ผู้รักษาที่ได้รับมอบหมายในทะเบียนคนไข้ หากย้ายเวลา
                    ใช้ปุ่มเลื่อนนัด ระบบจะเก็บนัดเดิมไว้หากช่วงเวลาใหม่ไม่ว่าง
                  </p>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      บันทึกนัดหมาย
                    </button>
                  </div>
                </form>
              </details>
            )}
            {moving && (
              <RescheduleForm
                appointment={moving}
                resources={resources}
                busy={busy}
                onCancel={() => setMoving(null)}
                onSave={(payload) =>
                  run(async () => {
                    await api.patch(
                      `/appointments/${moving.id}`,
                      payload,
                      config,
                    );
                    setMoving(null);
                    await load();
                    setMessage("เลื่อนนัดสำเร็จ คืนช่วงเวลาเดิมแล้ว");
                  })
                }
              />
            )}
            <ul className="service-list">
              {appointments.map((a) => (
                <li key={a.id}>
                  <div>
                    <strong>
                      {new Date(a.starts_at).toLocaleTimeString("th-TH", {
                        timeZone: "Asia/Bangkok",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      –
                      {new Date(a.ends_at).toLocaleTimeString("th-TH", {
                        timeZone: "Asia/Bangkok",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      · {a.patient_name}
                    </strong>
                    <p>
                      {names[a.status]} ·{" "}
                      {resources.find((r) => r.id === a.resource_id)?.name ||
                        "ไม่ใช้ห้อง/เตียงร่วม"}
                    </p>
                    {cancel === a.id && (
                      <p>ยืนยันยกเลิกนัดนี้เพื่อคืนช่วงเวลาให้ว่าง?</p>
                    )}
                  </div>
                  <div className="form-actions">
                    {user.role === "reception" && a.status === "booked" && (
                      <button
                        className="secondary"
                        disabled={busy || dirty}
                        onClick={() => setMoving(a)}
                      >
                        เลื่อนนัด
                      </button>
                    )}
                    {(actions[user.role]?.[a.status] || []).map((s) => (
                      <button
                        key={s}
                        className={s === "cancelled" ? "secondary" : "primary"}
                        disabled={busy}
                        onClick={() =>
                          s === "cancelled" && cancel !== a.id
                            ? setCancel(a.id)
                            : change(a, s)
                        }
                      >
                        {s === "cancelled" && cancel === a.id
                          ? "ยืนยันยกเลิกนัด"
                          : actionNames[s]}
                      </button>
                    ))}
                    {cancel === a.id && (
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={() => setCancel(null)}
                      >
                        เก็บนัดเดิม
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            {!appointments.length && <p>ยังไม่มีนัดหมายในวันที่เลือก</p>}
            <p className="subtle">แสดงสูงสุด 500 นัดต่อวัน</p>
          </>
        )}
      </fieldset>
    </section>
  );
}

function RescheduleForm({ appointment, resources, busy, onCancel, onSave }) {
  const initial = new Date(
    new Date(appointment.starts_at).getTime() + 7 * 60 * 60 * 1000,
  )
    .toISOString()
    .slice(0, 16);
  const [when, setWhen] = useState(initial),
    [minutes, setMinutes] = useState(
      (new Date(appointment.ends_at) - new Date(appointment.starts_at)) / 60000,
    ),
    [resource, setResource] = useState(appointment.resource_id || "");
  return (
    <section className="panel form-panel">
      <h3>เลื่อนนัด · {appointment.patient_name}</h3>
      <p>นัดเดิมยังอยู่จนกว่าจะบันทึกเวลาใหม่สำเร็จ</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const start = new Date(`${when}:00+07:00`);
          onSave({
            starts_at: start.toISOString(),
            ends_at: new Date(
              start.getTime() + Number(minutes) * 60000,
            ).toISOString(),
            resource_id: resource || null,
            expected_version: appointment.version,
          });
        }}
      >
        <div className="field-row">
          <label className="field">
            วันและเวลาใหม่ (ค.ศ. / เวลาไทย)
            <input
              required
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
            />
          </label>
          <label className="field">
            ระยะเวลาใหม่ (นาที)
            <input
              required
              type="number"
              min="1"
              max="480"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
            />
          </label>
          <label className="field">
            ห้อง / เตียงสำหรับนัดใหม่
            <select
              value={resource}
              onChange={(e) => setResource(e.target.value)}
            >
              <option value="">ไม่ใช้ห้อง/เตียงร่วม</option>
              {resources.map((r) => (
                <option key={r.id} value={r.id} disabled={!r.active}>
                  {r.name}
                  {r.active ? "" : " (ปิดรับนัดใหม่)"}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="form-actions">
          <button className="primary" disabled={busy}>
            ยืนยันเวลาใหม่
          </button>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={onCancel}
          >
            คงนัดเดิม
          </button>
        </div>
      </form>
    </section>
  );
}
