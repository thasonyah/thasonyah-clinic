import { useState, useRef } from "react";

export const initialServices = [
  ["S016", "ตอกเส้นผ่อนคลาย", 500, 45],
  ["S002", "ตอกเส้นแก้อาการ", 900, 90],
  ["S003", "ตอกเส้นใบหน้า", 1200, 75],
  ["S006", "พอกโคลน", 500, 60],
  ["S005", "พอกตา", 400, 45],
  ["S007", "กักน้ำมัน", 700, 60],
  ["S011", "สุมยา", 400, 45],
  ["S010", "นั่งถ่าน", 500, 60],
  ["S008", "เผายา", 800, 60],
  ["S013", "นึ่ง/นาบหม้อเกลือ", 800, 75],
  ["S009", "เข้ากระโจมอบยา", 500, 60],
  ["S014", "อยู่ไฟ", 1200, 120],
].map(([id, name, price, minutes]) => ({ id, name, price, minutes, active: true }));
const empty = { name: "", price: "", minutes: "" };

export default function ServiceCatalog({ services, setServices, flash, live = false, onSave, onToggle, canManage = true }) {
  const [saving, setSaving] = useState(false);
  const nameInput = useRef(null);
  const [draft, setDraft] = useState(empty);
  const [editVersion, setEditVersion] = useState(null);
  const [editing, setEditing] = useState(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("active");
  const [error, setError] = useState("");
  const bind = name => ({ value: draft[name], onChange: e => setDraft({ ...draft, [name]: e.target.value }) });
  const save = async e => {
    e.preventDefault();
    const name = draft.name.trim();
    if (!name || !String(draft.price).trim() || !String(draft.minutes).trim() || !Number.isFinite(Number(draft.price)) || Number(draft.price) < 0 || !Number.isInteger(Number(draft.minutes)) || Number(draft.minutes) <= 0) {
      setError("กรอกชื่อ ราคาอย่างน้อย 0 บาท และเวลาจำนวนเต็มมากกว่า 0 นาที"); return;
    }
    if (services.some(s => s.id !== editing && s.name.trim().toLocaleLowerCase() === name.toLocaleLowerCase())) {
      setError("มีชื่อหัตถการนี้แล้ว กรุณาแก้ไขหรือเปิดใช้รายการเดิม"); return;
    }
    const values = { name, price: Number(draft.price), minutes: Number(draft.minutes) };
    if (live) {
      setSaving(true);
      try { await onSave(editing, { ...values, price: values.price.toFixed(2) }, editVersion); setDraft(empty); setEditing(null); setError(""); }
      catch (err) { setError(err.message); }
      finally { setSaving(false); }
      return;
    }
    setServices(list => editing ? list.map(s => s.id === editing ? { ...s, ...values } : s) : [...list, { ...values, id: `LOCAL-${crypto.randomUUID()}`, active: true }]);
    setDraft(empty); setEditing(null); setError(""); setStatus("active"); setQuery("");
    flash("อัปเดตรายการในต้นแบบแล้ว — ยังไม่บันทึกลงฐานข้อมูล");
  };
  const filtered = services.filter(s => (s.name + s.id).toLowerCase().includes(query.toLowerCase()) && (status === "all" || s.active === (status === "active")));
  return <>
    <p className="subtle">{live ? "รายการหัตถการที่บันทึกในระบบคลินิก" : "รายการตั้งต้นจากหน้าบริการคลินิก 11 กันยายน 2569 · หน้านี้จำลองสิทธิ์แอดมิน ข้อมูลที่แก้ไขอยู่เฉพาะรอบการเปิดต้นแบบนี้"}</p>
    <div className="service-layout">
      <section className="panel form-panel">
        <h2>รายการหัตถการ</h2>
        <div className="field-row">
          <label className="field">ค้นหาชื่อหรือรหัส<input value={query} onChange={e => setQuery(e.target.value)} type="search" /></label>
          <label className="field">แสดงรายการ<select value={status} onChange={e => setStatus(e.target.value)}><option value="active">เปิดใช้งาน</option><option value="inactive">ปิดใช้งาน</option><option value="all">ทั้งหมด</option></select></label>
        </div>
        <p className="subtle" role="status">พบ {filtered.length} รายการ</p>
        <ul className="service-list">{filtered.map(s => <li key={s.id}>
          <div><strong>{s.name}</strong><p>{s.price.toLocaleString("th-TH")} บาท · {s.minutes} นาที · {s.active ? "เปิดใช้งาน" : "ปิดใช้งาน"}</p></div>
          <div className="service-actions" hidden={!canManage}>
            <button className="secondary" disabled={saving} aria-label={`แก้ไข ${s.name}`} onClick={() => {setEditing(s.id); setEditVersion(s.version); setDraft({ name: s.name, price: s.price, minutes: s.minutes }); setError(""); nameInput.current?.focus();}}>แก้ไข</button>
            <button className="secondary" aria-label={`${s.active ? "ปิดใช้งาน" : "เปิดใช้งาน"} ${s.name}`} disabled={saving} onClick={async () => {if(live){setSaving(true);try{await onToggle(s);setError("");}catch(err){setError(err.message);}finally{setSaving(false);}return;}setServices(list => list.map(item => item.id === s.id ? { ...item, active: !item.active } : item)); flash(`${s.active ? "ปิด" : "เปิด"}ใช้งาน ${s.name} ในต้นแบบแล้ว`);}}>{s.active ? "ปิดใช้งาน" : "เปิดใช้งานอีกครั้ง"}</button>
          </div>
        </li>)}</ul>
        {!filtered.length && <p>ไม่พบรายการ ลองเปลี่ยนคำค้นหรือสถานะ หรือเพิ่มหัตถการใหม่</p>}
      </section>
      <section className="panel form-panel service-editor" hidden={!canManage}>
        <h2>{editing ? "แก้ไขหัตถการ" : "เพิ่มหัตถการ"}</h2>
        <form onSubmit={save}><fieldset disabled={saving} style={{border:0,padding:0,margin:0,minWidth:0}}>
          <label className="field">ชื่อหัตถการ<input ref={nameInput} {...bind("name")} maxLength="150" required /></label>
          <label className="field">ราคา (บาท)<input {...bind("price")} type="number" min="0" step="0.01" required /></label>
          <label className="field">ระยะเวลา (นาที)<input {...bind("minutes")} type="number" min="1" step="1" required /></label>
          {error && <p role="alert">{error}</p>}
          <div className="form-actions"><button type="submit" className="primary">{editing ? "บันทึกการแก้ไข" : "เพิ่มหัตถการ"}</button>{editing && <button type="button" className="secondary" onClick={() => {setEditing(null); setDraft(empty); setError("");}}>ยกเลิกแก้ไข</button>}</div>
        </fieldset></form>
        <p className="subtle">การลบใช้วิธีปิดใช้งาน เพื่อหยุดเลือกในรายการใหม่และสามารถเปิดคืนได้ ประวัติการรักษาเดิมต้องเก็บชื่อและราคาขณะรับบริการไว้</p>
      </section>
    </div>
  </>;
}
