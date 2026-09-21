import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { bangkokDate } from "./Scheduling";

const money = (value) =>
  Number(value).toLocaleString("th-TH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
const methods = { cash: "เงินสด", transfer: "โอนเงิน", card: "บัตร" };
const dateTime = (value) =>
  new Date(value).toLocaleString("th-TH", { timeZone: "Asia/Bangkok" });

function ReceiptDocument({ invoice, entry, type }) {
  const isRefund = type === "refund";
  const prefix = isRefund ? "RF" : "RCT";
  const title = isRefund ? "ใบคืนเงิน" : "ใบรับเงิน";
  return (
    <article className="receipt-document">
      <header>
        <div>
          <p className="receipt-kicker">ธสัญญา คลินิกการแพทย์แผนไทย</p>
          <h3>{title}</h3>
          <p>เอกสารรับชำระค่าบริการคลินิก ไม่ใช่ใบกำกับภาษี</p>
        </div>
        <div className="receipt-number">
          <strong>
            {prefix}-{String(entry.number).padStart(6, "0")}
          </strong>
          <span>INV-{String(invoice.number).padStart(6, "0")}</span>
        </div>
      </header>
      <dl className="receipt-meta">
        <div>
          <dt>วันที่ออกเอกสาร</dt>
          <dd>{dateTime(entry.created_at)}</dd>
        </div>
        <div>
          <dt>คนไข้</dt>
          <dd>{invoice.patient_name}</dd>
        </div>
        <div>
          <dt>ช่องทาง</dt>
          <dd>{methods[entry.method]}</dd>
        </div>
      </dl>
      <table>
        <thead>
          <tr>
            <th>รายการอ้างอิง</th>
            <th>จำนวน</th>
            <th>ราคา</th>
            <th>รวม</th>
          </tr>
        </thead>
        <tbody>
          {invoice.items.map((item, index) => (
            <tr key={index}>
              <td>{item.name}</td>
              <td>{item.quantity}</td>
              <td>{money(item.price)}</td>
              <td>{money(item.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="receipt-total">
        <span>{isRefund ? "ยอดคืนเงิน" : "ยอดรับเงิน"}</span>
        <strong>{money(entry.amount)} บาท</strong>
      </div>
      {isRefund && entry.reason && (
        <p className="record-text">เหตุผลคืนเงิน: {entry.reason}</p>
      )}
      <footer>
        <span>ผู้รับเงิน / ผู้คืนเงิน</span>
        <span>ผู้ตรวจสอบ</span>
      </footer>
    </article>
  );
}

export default function Billing({
  token,
  user,
  onError,
  onDirty,
  onBusy,
  services,
}) {
  const [rows, setRows] = useState([]),
    [selected, setSelected] = useState(null),
    [patients, setPatients] = useState([]),
    [visits, setVisits] = useState([]),
    [patient, setPatient] = useState("");
  const [visit, setVisit] = useState(""),
    [items, setItems] = useState([{ service_id: "", quantity: 1 }]),
    [offset, setOffset] = useState(0),
    [query, setQuery] = useState("");
  const [day, setDay] = useState(bangkokDate),
    [report, setReport] = useState(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [payment, setPayment] = useState({
      amount: "",
      method: "cash",
      request_id: crypto.randomUUID(),
    }),
    [reason, setReason] = useState(""),
    [refundKey, setRefundKey] = useState(() => crypto.randomUUID());
  const [refundAmount, setRefundAmount] = useState(""),
    [refundMethod, setRefundMethod] = useState("cash");
  const [cashClose, setCashClose] = useState({ counted_cash: "", note: "" });
  const refundable = selected
    ? Math.max(
        0,
        (selected.payments || [])
          .filter((p) => p.method === refundMethod)
          .reduce((n, p) => n + Number(p.amount), 0) -
          (selected.refunds || [])
            .filter((p) => p.method === refundMethod)
            .reduce((n, p) => n + Number(p.amount), 0),
      )
    : 0;
  const config = { headers: { Authorization: `Bearer ${token}` } },
    dirty = Boolean(
      visit ||
        items.some((i) => i.service_id) ||
        payment.amount ||
        reason ||
        refundAmount ||
        cashClose.counted_cash ||
        cashClose.note,
    );
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
          ? "มีรายการนี้แล้ว สถานะเปลี่ยน หรือยอดเงินไม่ตรง กรุณาโหลดข้อมูลล่าสุดก่อนทำต่อ"
          : e.response?.status === 422
            ? "ตรวจบริการ จำนวน ยอดเงิน และเหตุผลให้ครบ"
            : onError(e),
      );
    } finally {
      setBusy(false);
      onBusy(false);
    }
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
  const load = async () => {
    if (user.role !== "manager") {
      const latest = (
        await api.get("/invoices", {
          ...config,
          params: { limit: 100, offset },
        })
      ).data;
      setRows(latest);
      setSelected((current) =>
        current ? latest.find((row) => row.id === current.id) || null : null,
      );
    }
    if (user.role !== "practitioner")
      setReport(
        (await api.get("/reports/daily", { ...config, params: { day } })).data,
      );
  };
  useEffect(() => {
    run(async () => {
      await load();
      if (user.role === "practitioner") await search();
    });
  }, [token, offset, day]);
  const clear = () => {
    setVisit("");
    setItems([{ service_id: "", quantity: 1 }]);
    setPayment({ amount: "", method: "cash", request_id: crypto.randomUUID() });
    setReason("");
    setRefundAmount("");
    setRefundMethod("cash");
    setRefundKey(crypto.randomUUID());
    setCashClose({ counted_cash: "", note: "" });
  };
  const updateSelected = (data) => {
    setSelected(data);
    setRows((all) => all.map((x) => (x.id === data.id ? data : x)));
    clear();
  };
  return (
    <section aria-busy={busy}>
      <fieldset className="module-fields" disabled={busy}>
        <div className="no-print">
          <h2>
            {user.role === "manager"
              ? "รายงานรับเงินรายวัน"
              : "ค่ารักษาและใบรับเงิน"}
          </h2>
          <p className="subtle">
            บันทึกรับเงินที่เจ้าหน้าที่ตรวจสอบแล้ว ·
            ยังไม่เชื่อมธนาคารหรือเครื่องรับบัตร
          </p>
          {message && (
            <p className="notice" role="status">
              {message}
            </p>
          )}
          {dirty && (
            <button className="secondary" disabled={busy} onClick={clear}>
              ละทิ้งรายการที่ยังไม่บันทึก
            </button>
          )}
          {user.role !== "practitioner" && (
            <>
              <div className="field-row">
                <label className="field">
                  วันที่รายงาน (ค.ศ. / เวลาไทย)
                  <input
                    type="date"
                    required
                    value={day}
                    disabled={busy}
                    onChange={(e) => {
                      if (e.target.value) setDay(e.target.value);
                      setCashClose({ counted_cash: "", note: "" });
                    }}
                  />
                </label>
              </div>
              {report && (
                <p>
                  รับเงิน {money(report.receipts)} บาท · คืนเงิน{" "}
                  {money(report.refunds)} บาท · สุทธิ {money(report.net)} บาท
                </p>
              )}
            </>
          )}
          {report && user.role !== "practitioner" && (
            <section className="panel form-panel">
              <h3>ปิดยอดเงินสดประจำวัน</h3>
              <p>
                เงินสดสุทธิตามระบบ{" "}
                {money(report.channels?.cash?.net || 0)} บาท
              </p>
              {report.cash_close ? (
                <>
                  <p>
                    ปิดยอดแล้ว · นับจริง{" "}
                    {money(report.cash_close.counted_cash)} บาท · ส่วนต่าง{" "}
                    {money(report.cash_close.difference)} บาท
                  </p>
                  {report.cash_close.note && (
                    <p className="record-text">{report.cash_close.note}</p>
                  )}
                </>
              ) : user.role === "finance" ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(async () => {
                      await api.post("/reports/daily/close", cashClose, {
                        ...config,
                        params: { day },
                      });
                      setCashClose({ counted_cash: "", note: "" });
                      await load();
                      setMessage("ปิดยอดเงินสดประจำวันแล้ว");
                    });
                  }}
                >
                  <div className="field-row">
                    <label className="field">
                      เงินสดที่นับจริง (บาท)
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        required
                        value={cashClose.counted_cash}
                        onChange={(e) =>
                          setCashClose({
                            ...cashClose,
                            counted_cash: e.target.value,
                          })
                        }
                      />
                    </label>
                  </div>
                  <label className="field">
                    หมายเหตุการปิดยอด
                    <textarea
                      maxLength="1000"
                      value={cashClose.note}
                      onChange={(e) =>
                        setCashClose({ ...cashClose, note: e.target.value })
                      }
                    />
                  </label>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      ยืนยันปิดยอดเงินสด
                    </button>
                  </div>
                </form>
              ) : (
                <p>ยังไม่ปิดยอดเงินสดของวันนี้</p>
              )}
            </section>
          )}
          {report && (
            <ul className="service-list">
              {Object.entries(report.channels || {}).map(([method, r]) => (
                <li key={method}>
                  <div>
                    <strong>
                      {
                        { cash: "เงินสด", transfer: "โอนเงิน", card: "บัตร" }[
                          method
                        ]
                      }
                    </strong>
                    <p>
                      รับ {money(r.receipts)} · คืน {money(r.refunds)} · สุทธิ{" "}
                      {money(r.net)} บาท
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <button
            className="secondary"
            disabled={busy}
            onClick={() => run(load)}
          >
            โหลดข้อมูลล่าสุด
          </button>
          {user.role === "practitioner" && (
            <details className="opd-section">
              <summary>ส่งรายการค่ารักษาให้การเงิน</summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(search);
                }}
              >
                <label className="field">
                  ค้นหาชื่อคนไข้
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
                      "/invoices",
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
                    setMessage(
                      "สร้างรายการค่ารักษาแล้ว ราคาถูกเก็บตามวันที่ออกเอกสาร",
                    );
                  });
                }}
              >
                <label className="field">
                  คนไข้
                  <select
                    required
                    value={patient}
                    disabled={busy || dirty}
                    onChange={(e) => {
                      setPatient(e.target.value);
                      setVisit("");
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
                <label className="field">
                  ฉบับการตรวจที่ยืนยันแล้ว
                  <select
                    required
                    value={visit}
                    onChange={(e) => setVisit(e.target.value)}
                  >
                    <option value="">เลือกการตรวจ</option>
                    {visits.map((v) => (
                      <option key={v.id} value={v.id}>
                        {new Date(v.created_at).toLocaleString("th-TH")} ·{" "}
                        {v.chief_complaint}
                      </option>
                    ))}
                  </select>
                </label>
                {items.map((item, index) => (
                  <div className="field-row" key={index}>
                    <label className="field">
                      บริการรายการ {index + 1}
                      <select
                        required
                        value={item.service_id}
                        onChange={(e) =>
                          setItems((all) =>
                            all.map((x, i) =>
                              i === index
                                ? { ...x, service_id: e.target.value }
                                : x,
                            ),
                          )
                        }
                      >
                        <option value="">เลือกบริการ</option>
                        {services
                          .filter((s) => s.active)
                          .map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} · {money(s.price)} บาท
                            </option>
                          ))}
                      </select>
                    </label>
                    <label className="field">
                      จำนวน
                      <input
                        type="number"
                        required
                        min="1"
                        max="100"
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
                    <button
                      type="button"
                      className="secondary"
                      disabled={busy || items.length === 1}
                      onClick={() =>
                        setItems((all) => all.filter((_, i) => i !== index))
                      }
                    >
                      นำรายการ {index + 1} ออก
                    </button>
                  </div>
                ))}
                <div className="form-actions">
                  <button
                    type="button"
                    className="secondary"
                    disabled={busy || items.length >= 50}
                    onClick={() =>
                      setItems([...items, { service_id: "", quantity: 1 }])
                    }
                  >
                    เพิ่มบริการ
                  </button>
                  <button className="primary" disabled={busy}>
                    ส่งรายการค่ารักษา
                  </button>
                </div>
              </form>
            </details>
          )}
          {user.role !== "manager" && (
            <>
              <ul className="service-list">
                {rows.map((r) => (
                  <li key={r.id}>
                    <div>
                      <strong>
                        INV-{String(r.number).padStart(6, "0")} ·{" "}
                        {r.patient_name}
                      </strong>
                      <p>
                        {money(r.total)} บาท ·{" "}
                        {
                          {
                            outstanding: "รอชำระ",
                            partial: "ชำระบางส่วน",
                            partially_refunded: "คืนเงินบางส่วน",
                            paid: "รับเงินแล้ว",
                            refunded: "คืนเงินแล้ว",
                          }[r.status]
                        }
                      </p>
                    </div>
                    <button
                      className="secondary"
                      disabled={busy || dirty}
                      onClick={() => {
                        setSelected(r);
                        clear();
                      }}
                    >
                      เปิดรายการ
                    </button>
                  </li>
                ))}
              </ul>
              {!rows.length && <p>ยังไม่มีรายการค่ารักษาในหน้านี้</p>}
              <div className="form-actions">
                <button
                  className="secondary"
                  disabled={busy || dirty || offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - 100))}
                >
                  หน้าก่อน
                </button>
                <span>หน้า {offset / 100 + 1}</span>
                <button
                  className="secondary"
                  disabled={busy || dirty || rows.length < 100}
                  onClick={() => setOffset(offset + 100)}
                >
                  หน้าถัดไป
                </button>
              </div>
            </>
          )}
        </div>
        {selected && (
          <article className="panel form-panel">
            <h2>
              {selected.paid_at ? "สรุปการรับเงิน" : "รายการค่ารักษา"} ·{" "}
              {String(selected.number).padStart(6, "0")}
            </h2>
            <p>คนไข้ {selected.patient_name}</p>
            <p>
              {new Date(selected.paid_at || selected.created_at).toLocaleString(
                "th-TH",
              )}
            </p>
            <ul className="service-list">
              {selected.items.map((i, k) => (
                <li key={k}>
                  <div>
                    <strong>{i.name}</strong>
                    <p>
                      {i.quantity} × {money(i.price)} บาท
                    </p>
                  </div>
                  <strong>{money(i.amount)} บาท</strong>
                </li>
              ))}
            </ul>
            <h3>ค่ารักษารวม {money(selected.total)} บาท</h3>
            <p>
              รับแล้ว {money(selected.paid_total)} บาท · คืนแล้ว{" "}
              {money(selected.refunded_total)} บาท · ค้างชำระ{" "}
              {money(selected.due_total)} บาท
            </p>
            <p className="subtle">
              การคืนเงินไม่ทำให้ยอดที่รับไปแล้วกลับเป็นหนี้ใหม่
            </p>
            {(selected.payments || []).length > 0 && (
              <>
                <h3>ใบรับเงินแต่ละรายการ</h3>
                <ul className="service-list">
                  {selected.payments.map((p) => (
                    <li key={p.id}>
                      <div>
                        <strong>
                          RCT-{String(p.number).padStart(6, "0")} ·{" "}
                          {money(p.amount)} บาท
                        </strong>
                        <p>
                          {new Date(p.created_at).toLocaleString("th-TH", {
                            timeZone: "Asia/Bangkok",
                          })}{" "}
                          ·{" "}
                          {
                            methods[p.method]
                          }
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {(selected.refunds || []).length > 0 && (
              <>
                <h3>รายการคืนเงิน</h3>
                <ul className="service-list">
                  {selected.refunds.map((p) => (
                    <li key={p.id}>
                      <div>
                        <strong>
                          RF-{String(p.number).padStart(6, "0")} ·{" "}
                          {money(p.amount)} บาท
                        </strong>
                        <p>
                          {new Date(p.created_at).toLocaleString("th-TH", {
                            timeZone: "Asia/Bangkok",
                          })}{" "}
                          ·{" "}
                          {
                            methods[p.method]
                          }{" "}
                          · {p.reason}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <p>
              สถานะ:{" "}
              {
                {
                  outstanding: "รอชำระ",
                  partial: "ชำระบางส่วน",
                  partially_refunded: "คืนเงินบางส่วน",
                  paid: "รับเงินแล้ว",
                  refunded: "คืนเงินแล้ว",
                }[selected.status]
              }
            </p>
            {selected.payment_method && (
              <p>
                ชำระโดย{" "}
                {
                  {
                    ...methods,
                    mixed: "หลายช่องทาง",
                  }[selected.payment_method]
                }
              </p>
            )}
            {selected.refunded_at && (
              <p>
                คืนเงิน {new Date(selected.refunded_at).toLocaleString("th-TH")}{" "}
                · {selected.refund_reason}
              </p>
            )}
            {((selected.payments || []).length > 0 ||
              (selected.refunds || []).length > 0) && (
              <section className="official-receipts">
                <h3>เอกสารใบรับเงิน / ใบคืนเงินสำหรับพิมพ์</h3>
                {(selected.payments || []).map((payment) => (
                  <ReceiptDocument
                    key={payment.id}
                    invoice={selected}
                    entry={payment}
                    type="receipt"
                  />
                ))}
                {(selected.refunds || []).map((refund) => (
                  <ReceiptDocument
                    key={refund.id}
                    invoice={selected}
                    entry={refund}
                    type="refund"
                  />
                ))}
              </section>
            )}
            <div className="no-print">
              <button
                className="secondary"
                disabled={busy || dirty}
                onClick={() => window.print()}
              >
                พิมพ์เอกสาร
              </button>
              {user.role === "finance" && Number(selected.due_total) > 0 && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(async () => {
                      updateSelected(
                        (
                          await api.post(
                            `/invoices/${selected.id}/payment`,
                            payment,
                            config,
                          )
                        ).data,
                      );
                      await load();
                      setMessage("บันทึกรับเงินแล้ว");
                    });
                  }}
                >
                  <p>
                    บันทึกได้ทั้งยอดบางส่วนและยอดที่เหลือ
                    แต่ละช่องทางมีเลขใบรับเงินของตัวเอง
                  </p>
                  <div className="field-row">
                    <label className="field">
                      ยอดที่รับ (บาท)
                      <input
                        type="number"
                        required
                        min="0.01"
                        max={selected.due_total}
                        step="0.01"
                        value={payment.amount}
                        onChange={(e) =>
                          setPayment({ ...payment, amount: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      วิธีชำระ
                      <select
                        value={payment.method}
                        onChange={(e) =>
                          setPayment({ ...payment, method: e.target.value })
                        }
                      >
                        <option value="cash">เงินสด</option>
                        <option value="transfer">โอนเงิน</option>
                        <option value="card">บัตร</option>
                      </select>
                    </label>
                  </div>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      ยืนยันบันทึกรับเงิน
                    </button>
                  </div>
                </form>
              )}
              {user.role === "finance" &&
                Number(selected.paid_total) >
                  Number(selected.refunded_total) && (
                  <details className="opd-section">
                    <summary>บันทึกคืนเงิน</summary>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        run(async () => {
                          updateSelected(
                            (
                              await api.post(
                                `/invoices/${selected.id}/refund`,
                                {
                                  request_id: refundKey,
                                  reason,
                                  amount: refundAmount,
                                  method: refundMethod,
                                },
                                config,
                              )
                            ).data,
                          );
                          await load();
                          setMessage("บันทึกคืนเงินแล้ว");
                        });
                      }}
                    >
                      <p>
                        บันทึกหลังคืนเงินจริง ยอดที่คืนได้ในช่องทางนี้{" "}
                        {money(refundable)} บาท เอกสารเดิมจะยังคงอยู่
                      </p>
                      <div className="field-row">
                        <label className="field">
                          ช่องทางที่คืนเงิน
                          <select
                            value={refundMethod}
                            onChange={(e) => setRefundMethod(e.target.value)}
                          >
                            <option value="cash">เงินสด</option>
                            <option value="transfer">โอนเงิน</option>
                            <option value="card">บัตร</option>
                          </select>
                        </label>
                        <label className="field">
                          ยอดคืน (บาท)
                          <input
                            required
                            type="number"
                            min="0.01"
                            max={refundable.toFixed(2)}
                            step="0.01"
                            value={refundAmount}
                            onChange={(e) => setRefundAmount(e.target.value)}
                          />
                        </label>
                      </div>
                      <label className="field">
                        เหตุผลที่คืนเงิน
                        <textarea
                          required
                          maxLength="1000"
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                        />
                      </label>
                      <div className="form-actions">
                        <button className="primary" disabled={busy}>
                          ยืนยันบันทึกคืนเงิน
                        </button>
                      </div>
                    </form>
                  </details>
                )}
            </div>
          </article>
        )}
      </fieldset>
    </section>
  );
}
