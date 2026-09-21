import { useEffect, useState } from "react";
import { api } from "../../api/client";
import StockAdjustment from "./StockAdjustment";
import { bangkokDate } from "./Scheduling";

export default function Pharmacy({ token, user, onError, onDirty, onBusy }) {
  const [meds, setMeds] = useState([]),
    [lots, setLots] = useState([]),
    [rows, setRows] = useState([]),
    [selected, setSelected] = useState(null);
  const [medicine, setMedicine] = useState({ name: "", unit: "" }),
    [lot, setLot] = useState({
      medicine_id: "",
      lot_number: "",
      expires_on: "",
      quantity: "",
    });
  const [patients, setPatients] = useState([]),
    [patient, setPatient] = useState(""),
    [query, setQuery] = useState(""),
    [visits, setVisits] = useState([]),
    [visit, setVisit] = useState("");
  const [items, setItems] = useState([
      { medicine_id: "", quantity: 1, instructions: "" },
    ]),
    [offset, setOffset] = useState(0),
    [confirm, setConfirm] = useState(false),
    [request, setRequest] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [dispenseQuantities, setDispenseQuantities] = useState({}),
    [dispenseDirty, setDispenseDirty] = useState(false);
  const invalidDispense = selected
    ? !(selected.remaining || []).some(
        (i) => Number(dispenseQuantities[i.medicine_id] ?? i.quantity) > 0,
      ) ||
      (selected.remaining || []).some((i) => {
        const q = Number(dispenseQuantities[i.medicine_id] ?? i.quantity);
        return !Number.isInteger(q) || q < 0 || q > i.quantity;
      })
    : false;
  const [stockEditing, setStockEditing] = useState(null),
    [stockHistory, setStockHistory] = useState([]),
    [stockDirty, setStockDirty] = useState(false);
  const config = { headers: { Authorization: `Bearer ${token}` } },
    dirty = Boolean(
      medicine.name ||
        medicine.unit ||
        Object.values(lot).some(Boolean) ||
        visit ||
        items.some((x) => x.medicine_id || x.instructions),
    );
  useEffect(() => {
    onDirty(dirty || dispenseDirty || stockDirty);
  }, [dirty, dispenseDirty, stockDirty, onDirty]);
  useEffect(() => {
    if (!dirty && !dispenseDirty && !stockDirty) return;
    const warn = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, dispenseDirty, stockDirty]);
  const run = async (action) => {
    setBusy(true);
    onBusy(true);
    setMessage("");
    try {
      await action();
    } catch (e) {
      setMessage(
        e.response?.status === 409
          ? "รายการซ้ำ สถานะเปลี่ยน หรือสต็อกที่ไม่หมดอายุไม่พอ ระบบไม่ตัดยาไว้บางรายการ กรุณาโหลดล่าสุดและตรวจคลัง"
          : e.response?.status === 422
            ? "ตรวจชื่อยา หน่วย ล็อต วันหมดอายุ จำนวน และวิธีใช้ให้ครบ"
            : onError(e),
      );
    } finally {
      setBusy(false);
      onBusy(false);
    }
  };
  const load = async () => {
    setMeds((await api.get("/medicines", config)).data);
    const latest = (
      await api.get("/prescriptions", {
        ...config,
        params: { limit: 100, offset },
      })
    ).data;
    setRows(latest);
    setSelected((current) =>
      current ? latest.find((row) => row.id === current.id) || null : null,
    );
    setConfirm(false);
    if (user.role === "pharmacy")
      setLots((await api.get("/lots", config)).data);
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
      if (user.role === "practitioner") await search();
    });
  }, [token, offset]);
  const clear = () => {
    setStockEditing(null);
    setStockDirty(false);
    setDispenseDirty(false);
    setDispenseQuantities({});
    setMedicine({ name: "", unit: "" });
    setLot({ medicine_id: "", lot_number: "", expires_on: "", quantity: "" });
    setVisit("");
    setItems([{ medicine_id: "", quantity: 1, instructions: "" }]);
  };
  return (
    <section aria-busy={busy}>
      <fieldset className="module-fields" disabled={busy}>
        <div className="no-print">
          <h2>
            {user.role === "pharmacy" ? "คลังยาและการจ่ายยา" : "ใบสั่งยา"}
          </h2>
          <p className="subtle">
            ผู้รักษาระบุรายการและวิธีใช้ · จ่ายจากล็อตที่ยังไม่หมดอายุ
            เรียงวันหมดอายุก่อน
          </p>
          {message && (
            <p className="notice" role="status">
              {message}
            </p>
          )}
          {(dirty || dispenseDirty || stockDirty) && (
            <button className="secondary" disabled={busy} onClick={clear}>
              ละทิ้งข้อมูลที่ยังไม่บันทึก
            </button>
          )}
          <button
            className="secondary"
            disabled={busy}
            onClick={() => run(load)}
          >
            โหลดใบสั่งยาและคลังล่าสุด
          </button>
          {user.role === "pharmacy" && (
            <>
              <details className="opd-section">
                <summary>เพิ่มชื่อยา / สมุนไพร</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(async () => {
                      await api.post("/medicines", medicine, config);
                      setMedicine({ name: "", unit: "" });
                      await load();
                      setMessage("เพิ่มรายการยาแล้ว");
                    });
                  }}
                >
                  <div className="field-row">
                    <label className="field">
                      ชื่อยา
                      <input
                        required
                        maxLength="200"
                        value={medicine.name}
                        onChange={(e) =>
                          setMedicine({ ...medicine, name: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      หน่วยนับในคลัง (เช่น แคปซูล / ซอง)
                      <input
                        required
                        maxLength="40"
                        value={medicine.unit}
                        onChange={(e) =>
                          setMedicine({ ...medicine, unit: e.target.value })
                        }
                      />
                    </label>
                  </div>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      เพิ่มรายการยา
                    </button>
                  </div>
                </form>
              </details>
              <details className="opd-section">
                <summary>รับยาเข้าคลัง</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(async () => {
                      await api.post(
                        "/lots",
                        { ...lot, quantity: Number(lot.quantity) },
                        config,
                      );
                      setLot({
                        medicine_id: "",
                        lot_number: "",
                        expires_on: "",
                        quantity: "",
                      });
                      await load();
                      setMessage("รับเข้าคลังและเก็บประวัติการเคลื่อนไหวแล้ว");
                    });
                  }}
                >
                  <div className="field-row">
                    <label className="field">
                      ยา
                      <select
                        required
                        value={lot.medicine_id}
                        onChange={(e) =>
                          setLot({ ...lot, medicine_id: e.target.value })
                        }
                      >
                        <option value="">เลือกยา</option>
                        {meds.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name} · {m.unit}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      เลขล็อต
                      <input
                        required
                        maxLength="100"
                        value={lot.lot_number}
                        onChange={(e) =>
                          setLot({ ...lot, lot_number: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      วันหมดอายุ (ค.ศ.)
                      <input
                        required
                        type="date"
                        value={lot.expires_on}
                        onChange={(e) =>
                          setLot({ ...lot, expires_on: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      จำนวนหน่วยที่รับ
                      <input
                        required
                        type="number"
                        min="1"
                        max="1000000"
                        value={lot.quantity}
                        onChange={(e) =>
                          setLot({ ...lot, quantity: e.target.value })
                        }
                      />
                    </label>
                  </div>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      ยืนยันรับเข้าคลัง
                    </button>
                  </div>
                </form>
              </details>
              <details className="opd-section">
                <summary>ยอดคงเหลือแยกล็อต</summary>
                <p className="subtle">
                  แสดง 1,000 ล็อตแรกตามวันหมดอายุ ·
                  ล็อตหมดอายุเก็บยอดเดิมแต่ใช้จ่ายยาไม่ได้
                </p>
                <ul className="service-list">
                  {lots.map((l) => (
                    <li key={l.id}>
                      <div>
                        <strong>
                          {meds.find((m) => m.id === l.medicine_id)?.name ||
                            l.medicine_id}
                        </strong>
                        <p>
                          ล็อต {l.lot_number} · หมดอายุ {l.expires_on}{" "}
                          {l.expires_on < bangkokDate() ? "· หมดอายุแล้ว" : ""}
                        </p>
                      </div>
                      <strong>
                        {l.quantity}{" "}
                        {meds.find((m) => m.id === l.medicine_id)?.unit}
                      </strong>
                      <button
                        className="secondary"
                        disabled={busy || dirty || dispenseDirty || stockDirty}
                        onClick={() =>
                          run(async () => {
                            setStockHistory(
                              (await api.get(`/lots/${l.id}/movements`, config))
                                .data,
                            );
                            setStockEditing(l);
                          })
                        }
                      >
                        ตรวจนับ / ประวัติล็อต
                      </button>
                    </li>
                  ))}
                </ul>
                {!lots.length && <p>ยังไม่มีล็อตยา</p>}
              </details>
            </>
          )}
          {stockEditing && (
            <StockAdjustment
              key={stockEditing.id}
              lot={stockEditing}
              history={stockHistory}
              busy={busy}
              onDirty={setStockDirty}
              onClose={() => {
                setStockEditing(null);
                setStockDirty(false);
              }}
              onSave={(payload) =>
                run(async () => {
                  await api.post(
                    `/lots/${stockEditing.id}/adjust`,
                    payload,
                    config,
                  );
                  setStockEditing(null);
                  setStockDirty(false);
                  await load();
                  setMessage("ปรับยอดและเก็บประวัติล็อตแล้ว");
                })
              }
            />
          )}
          {user.role === "practitioner" && (
            <details className="opd-section">
              <summary>สร้างใบสั่งยาจากฉบับตรวจที่ยืนยันแล้ว</summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(search);
                }}
              >
                <label className="field">
                  ค้นหาคนไข้
                  <input
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
                    const r = await api.post(
                      "/prescriptions",
                      {
                        visit_id: visit,
                        items: items.map((i) => ({
                          ...i,
                          quantity: Number(i.quantity),
                        })),
                      },
                      config,
                    );
                    clear();
                    setSelected(r.data);
                    await load();
                    setMessage("ส่งใบสั่งยาให้เภสัชกรรมแล้ว");
                  });
                }}
              >
                <label className="field">
                  คนไข้
                  <select
                    required
                    disabled={busy || dirty}
                    value={patient}
                    onChange={(e) => {
                      setPatient(e.target.value);
                      setVisits([]);
                      if (e.target.value)
                        run(async () =>
                          setVisits(
                            (
                              await api.get(
                                `/patients/${e.target.value}/visits`,
                                config,
                              )
                            ).data.filter((v) => v.signed_at),
                          ),
                        );
                    }}
                  >
                    <option value="">เลือกคนไข้</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} · {p.birth_date || p.id.slice(0, 8)}
                      </option>
                    ))}
                  </select>
                </label>
                {patient && (
                  <p>
                    แพ้ยา:{" "}
                    {patients.find((p) => p.id === patient)?.allergies ||
                      "ยังไม่บันทึก"}
                  </p>
                )}
                <label className="field">
                  การตรวจ
                  <select
                    required
                    value={visit}
                    onChange={(e) => setVisit(e.target.value)}
                  >
                    <option value="">เลือกการตรวจที่ยืนยันแล้ว</option>
                    {visits.map((v) => (
                      <option key={v.id} value={v.id}>
                        {new Date(v.created_at).toLocaleString("th-TH")} ·{" "}
                        {v.chief_complaint}
                      </option>
                    ))}
                  </select>
                </label>
                {items.map((item, index) => (
                  <fieldset className="opd-element-group" key={index}>
                    <legend>ยารายการ {index + 1}</legend>
                    <div className="field-row">
                      <label className="field">
                        ยา
                        <select
                          required
                          value={item.medicine_id}
                          onChange={(e) =>
                            setItems((all) =>
                              all.map((x, i) =>
                                i === index
                                  ? { ...x, medicine_id: e.target.value }
                                  : x,
                              ),
                            )
                          }
                        >
                          <option value="">เลือกยา</option>
                          {meds
                            .filter((m) => m.active)
                            .map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} · {m.unit}
                              </option>
                            ))}
                        </select>
                      </label>
                      <label className="field">
                        จำนวนหน่วยที่สั่ง
                        <input
                          type="number"
                          min="1"
                          max="1000000"
                          required
                          value={item.quantity}
                          onChange={(e) =>
                            setItems((all) =>
                              all.map((x, i) =>
                                i === index
                                  ? { ...x, quantity: e.target.value }
                                  : x,
                              ),
                            )
                          }
                        />
                      </label>
                    </div>
                    <label className="field">
                      ขนาด วิธีใช้ เวลา และระยะเวลาที่ใช้
                      <textarea
                        required
                        maxLength="2000"
                        value={item.instructions}
                        onChange={(e) =>
                          setItems((all) =>
                            all.map((x, i) =>
                              i === index
                                ? { ...x, instructions: e.target.value }
                                : x,
                            ),
                          )
                        }
                      />
                    </label>
                    <button
                      className="secondary"
                      type="button"
                      disabled={busy || items.length === 1}
                      onClick={() =>
                        setItems((all) => all.filter((_, i) => i !== index))
                      }
                    >
                      นำยารายการ {index + 1} ออก
                    </button>
                  </fieldset>
                ))}
                <div className="form-actions">
                  <button
                    className="secondary"
                    type="button"
                    disabled={busy || items.length >= 50}
                    onClick={() =>
                      setItems([
                        ...items,
                        { medicine_id: "", quantity: 1, instructions: "" },
                      ])
                    }
                  >
                    เพิ่มยา
                  </button>
                  <button className="primary" disabled={busy}>
                    ยืนยันใบสั่งยา
                  </button>
                </div>
              </form>
            </details>
          )}
          <h3>รายการใบสั่งยา</h3>
          <ul className="service-list">
            {rows.map((r) => (
              <li key={r.id}>
                <div>
                  <strong>{r.patient_name}</strong>
                  <p>
                    {new Date(r.created_at).toLocaleString("th-TH")} ·{" "}
                    {
                      {
                        prescribed: "รอจ่ายยา",
                        partial: "จ่ายบางส่วน",
                        dispensed: "จ่ายแล้ว",
                        cancelled: "ยกเลิก",
                      }[r.status]
                    }
                  </p>
                </div>
                <button
                  className="secondary"
                  disabled={busy || dirty || dispenseDirty || stockDirty}
                  onClick={() => {
                    setSelected(r);
                    setDispenseQuantities({});
                    setDispenseDirty(false);
                    setConfirm(false);
                    setRequest(crypto.randomUUID());
                  }}
                >
                  เปิดใบสั่งยา
                </button>
              </li>
            ))}
          </ul>
          {!rows.length && <p>ยังไม่มีใบสั่งยาในหน้านี้</p>}
          <div className="form-actions">
            <button
              className="secondary"
              disabled={
                busy || dirty || dispenseDirty || stockDirty || offset === 0
              }
              onClick={() => setOffset(Math.max(0, offset - 100))}
            >
              หน้าก่อน
            </button>
            <span>หน้า {offset / 100 + 1}</span>
            <button
              className="secondary"
              disabled={
                busy ||
                dirty ||
                dispenseDirty ||
                stockDirty ||
                rows.length < 100
              }
              onClick={() => setOffset(offset + 100)}
            >
              หน้าถัดไป
            </button>
          </div>
        </div>
        {selected && (
          <article className="panel form-panel">
            <h2>ใบสั่งยา · {selected.patient_name}</h2>
            <p>เลขอ้างอิง {selected.id}</p>
            <p>
              ประวัติแพ้ยาล่าสุด: {selected.current_allergies || "ยังไม่บันทึก"}
            </p>
            <p className="subtle">
              ประวัติแพ้ยาที่บันทึกตอนสั่ง:{" "}
              {selected.allergies || "ยังไม่บันทึก"}
            </p>
            <p>
              สถานะ{" "}
              {
                {
                  prescribed: "รอจ่ายยา",
                  partial: "จ่ายบางส่วน",
                  dispensed: "จ่ายแล้ว",
                  cancelled: "ยกเลิก",
                }[selected.status]
              }
            </p>
            <ul className="service-list">
              {selected.items.map((i, k) => (
                <li key={k}>
                  <div>
                    <strong>
                      {i.name} · {i.quantity} {i.unit}
                    </strong>
                    <p className="record-text">{i.instructions}</p>
                  </div>
                </li>
              ))}
            </ul>
            <h3>ยาที่ยังไม่จ่าย</h3>
            <ul className="service-list">
              {(selected.remaining || []).map((i) => (
                <li key={i.medicine_id}>
                  <div>
                    <strong>{i.name}</strong>
                    <p>
                      คงเหลือในใบสั่ง {i.quantity} {i.unit}
                    </p>
                  </div>
                  {user.role === "pharmacy" &&
                    ["prescribed", "partial"].includes(selected.status) && (
                      <label className="field no-print">
                        จำนวนจ่ายครั้งนี้ · {i.name}
                        <input
                          type="number"
                          min="0"
                          max={i.quantity}
                          disabled={busy || confirm}
                          value={
                            dispenseQuantities[i.medicine_id] ?? i.quantity
                          }
                          onChange={(e) => {
                            setDispenseQuantities({
                              ...dispenseQuantities,
                              [i.medicine_id]: e.target.value,
                            });
                            setDispenseDirty(true);
                            setRequest(crypto.randomUUID());
                          }}
                        />
                      </label>
                    )}
                </li>
              ))}
            </ul>
            {user.role === "pharmacy" &&
              invalidDispense &&
              ["prescribed", "partial"].includes(selected.status) && (
                <p className="notice no-print">
                  ระบุจำนวนเต็มตั้งแต่ 0 ถึงยอดคงเหลือ
                  และเลือกจ่ายอย่างน้อยหนึ่งรายการ
                </p>
              )}
            {(selected.allocations || []).length > 0 && (
              <details className="opd-section" open>
                <summary>ประวัติล็อตที่จ่าย</summary>
                <ul className="service-list">
                  {selected.allocations.map((a, i) => (
                    <li key={i}>
                      <div>
                        <strong>
                          {
                            selected.items.find(
                              (m) => m.medicine_id === a.medicine_id,
                            )?.name
                          }{" "}
                          · ล็อต {a.lot_number}
                        </strong>
                        <p>
                          {a.quantity} หน่วย · หมดอายุ {a.expires_on} · จ่าย{" "}
                          {new Date(a.created_at).toLocaleString("th-TH", {
                            timeZone: "Asia/Bangkok",
                          })}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <div className="no-print form-actions">
              <button
                className="secondary"
                disabled={busy || dirty}
                onClick={() => window.print()}
              >
                พิมพ์ใบสั่งยา / วิธีใช้ยา
              </button>
              {["prescribed", "partial"].includes(selected.status) &&
                (confirm ? (
                  <>
                    <p>
                      {user.role === "pharmacy"
                        ? "ตรวจคนไข้ ประวัติแพ้ยา รายการและวิธีใช้แล้ว ยืนยันจ่ายตามจำนวนที่เลือก?"
                        : "ยืนยันยกเลิกส่วนที่ยังไม่จ่าย? ประวัติที่จ่ายแล้วจะคงอยู่"}
                    </p>
                    <button
                      className="primary"
                      disabled={busy || dirty}
                      onClick={() =>
                        run(async () => {
                          const r = await api.post(
                            `/prescriptions/${selected.id}/${user.role === "pharmacy" ? "dispense" : "cancel"}`,
                            user.role === "pharmacy"
                              ? {
                                  request_id: request,
                                  items: (selected.remaining || [])
                                    .map((i) => ({
                                      medicine_id: i.medicine_id,
                                      quantity: Number(
                                        dispenseQuantities[i.medicine_id] ??
                                          i.quantity,
                                      ),
                                    }))
                                    .filter((i) => i.quantity > 0),
                                }
                              : {},
                            config,
                          );
                          setSelected(r.data);
                          setDispenseDirty(false);
                          setDispenseQuantities({});
                          setRequest(crypto.randomUUID());
                          setConfirm(false);
                          await load();
                          setMessage(
                            user.role === "pharmacy"
                              ? "บันทึกการจ่ายยาและตัดสต็อกแล้ว"
                              : "ยกเลิกใบสั่งยาแล้ว",
                          );
                        })
                      }
                    >
                      ยืนยัน
                      {user.role === "pharmacy" ? "จ่ายยา" : "ยกเลิกใบสั่งยา"}
                    </button>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => setConfirm(false)}
                    >
                      กลับไปตรวจทาน
                    </button>
                  </>
                ) : (
                  <button
                    className="primary"
                    disabled={
                      busy ||
                      dirty ||
                      (user.role === "pharmacy" && invalidDispense)
                    }
                    onClick={() => setConfirm(true)}
                  >
                    {user.role === "pharmacy"
                      ? "ตรวจทานก่อนจ่ายยา"
                      : "ยกเลิกใบสั่งยา"}
                  </button>
                ))}
            </div>
          </article>
        )}
      </fieldset>
    </section>
  );
}
