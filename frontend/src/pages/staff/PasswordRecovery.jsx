import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function PasswordRecovery({ onBack }) {
  const [token, setToken] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("reset") || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (window.location.hash) window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }, []);
  const submit = async e => {
    e.preventDefault(); setMessage("");
    if (token && (password !== confirm || password.length < 12 || new TextEncoder().encode(password).length > 72)) {
      setMessage("กรอกรหัสผ่านตรงกันทั้งสองช่อง อย่างน้อย 12 ตัวอักษร และไม่เกิน 72 ไบต์"); return;
    }
    setBusy(true);
    try {
      if (token) {
        await api.post("/auth/reset-password", { token, new_password: password });
        setToken(""); setPassword(""); setConfirm(""); setDone(true);
        setMessage("ตั้งรหัสผ่านใหม่แล้ว กรุณาเข้าสู่ระบบอีกครั้ง");
      } else {
        await api.post("/auth/forgot-password", { email });
        setMessage("หากอีเมลนี้ตรงกับบัญชีที่ใช้งานได้ ระบบจะส่งลิงก์รีเซ็ตให้ กรุณาตรวจกล่องจดหมายและจดหมายขยะ");
      }
    } catch (error) {
      const status = error.response?.status;
      setMessage(status === 503 ? "ระบบส่งอีเมลยังไม่พร้อม กรุณาติดต่อผู้ดูแลคลินิก" : status === 400 ? "ลิงก์นี้หมดอายุหรือใช้แล้ว กรุณาขอลิงก์ใหม่" : status === 429 ? "ส่งคำขอถี่เกินไป กรุณารอหนึ่งนาทีแล้วลองใหม่" : status === 422 ? "ตรวจอีเมลและข้อกำหนดรหัสผ่านอีกครั้ง" : "เชื่อมต่อไม่สำเร็จ กรุณาลองใหม่");
    } finally { setBusy(false); }
  };
  return <section className="panel form-panel live-login"><h2>{token ? "ตั้งรหัสผ่านใหม่" : done ? "เปลี่ยนรหัสผ่านสำเร็จ" : "ลืมรหัสผ่าน"}</h2>
    <p className="subtle">ลิงก์มีอายุ 15 นาทีและใช้ได้ครั้งเดียว</p>
    {message && <p role="status" className="notice">{message}</p>}
    {!done && <form onSubmit={submit}>{token ? <>
      <label className="field">รหัสผ่านใหม่<input type="password" autoComplete="new-password" minLength="12" required value={password} onChange={e=>setPassword(e.target.value)} /></label>
      <label className="field">ยืนยันรหัสผ่านใหม่<input type="password" autoComplete="new-password" minLength="12" required value={confirm} onChange={e=>setConfirm(e.target.value)} /></label>
      <p className="subtle">อย่างน้อย 12 ตัวอักษร ไม่เกิน 72 ไบต์ หลังเปลี่ยนรหัสผ่านทุกอุปกรณ์ต้องเข้าสู่ระบบใหม่</p>
    </> : <label className="field">อีเมลที่ใช้เข้าสู่ระบบ<input type="email" autoComplete="username" required value={email} onChange={e=>setEmail(e.target.value)} /></label>}
    <div className="form-actions"><button className="primary" disabled={busy}>{busy ? "กำลังดำเนินการ…" : token ? "บันทึกรหัสผ่านใหม่" : "ส่งลิงก์รีเซ็ตทางอีเมล"}</button></div></form>}
    <div className="form-actions">{token && <button className="secondary" disabled={busy} onClick={()=>{setToken("");setPassword("");setConfirm("");setMessage("");}}>ขอลิงก์ใหม่</button>}<button className="secondary" disabled={busy} onClick={onBack}>กลับไปเข้าสู่ระบบ</button></div>
  </section>;
}
