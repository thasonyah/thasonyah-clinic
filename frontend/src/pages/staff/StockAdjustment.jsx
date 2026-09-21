import { useState } from "react";
export default function StockAdjustment({
  lot,
  history,
  busy,
  onDirty,
  onSave,
  onClose,
}) {
  const [quantity, setQuantity] = useState(String(lot.quantity)),
    [reason, setReason] = useState(""),
    [kind, setKind] = useState("count"),
    [request] = useState(() => crypto.randomUUID());
  return (
    <section className="panel form-panel">
      <h3>ตรวจนับและปรับล็อต {lot.lot_number}</h3>
      <p>
        ยอดในระบบขณะเปิด: {lot.quantity} หน่วย · ระบุยอดหลังปรับ
        ไม่ใช่จำนวนเพิ่มหรือลด
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSave({
            request_id: request,
            expected_quantity: lot.quantity,
            quantity: Number(quantity),
            kind,
            reason,
          });
        }}
      >
        <div className="field-row">
          <label className="field">
            ประเภทการปรับ
            <select
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                onDirty(true);
              }}
            >
              <option value="count">ตรวจนับ</option>
              <option value="return">รับคืนเข้าคลัง</option>
              <option value="damage">ตัดชำรุด / หมดอายุ</option>
              <option value="correction">แก้ยอดที่บันทึกผิด</option>
            </select>
          </label>
          <label className="field">
            ยอดคงเหลือหลังปรับ
            <input
              type="number"
              required
              min="0"
              max="1000000"
              value={quantity}
              onChange={(e) => {
                setQuantity(e.target.value);
                onDirty(true);
              }}
            />
          </label>
        </div>
        <label className="field">
          เหตุผลและเอกสารอ้างอิง
          <textarea
            required
            maxLength="900"
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              onDirty(true);
            }}
          />
        </label>
        <div className="form-actions">
          <button className="primary" disabled={busy}>
            ยืนยันปรับยอดล็อต
          </button>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={onClose}
          >
            ปิดโดยไม่ปรับยอด
          </button>
        </div>
      </form>
      <details className="opd-section">
        <summary>ประวัติการเคลื่อนไหวล็อต</summary>
        <p className="subtle">แสดง 1,000 รายการล่าสุด</p>
        <ul className="service-list">
          {history.map((m) => (
            <li key={m.id}>
              <div>
                <strong>
                  {m.quantity > 0 ? "+" : ""}
                  {m.quantity} หน่วย · {m.reason}
                </strong>
                <p>
                  {new Date(m.created_at).toLocaleString("th-TH", {
                    timeZone: "Asia/Bangkok",
                  })}
                </p>
                <p>ผู้ทำรายการ {m.actor_id}</p>
              </div>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
