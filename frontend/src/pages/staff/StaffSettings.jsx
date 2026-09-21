import { useEffect, useState } from "react";
import { api } from "../../api/client";

export const roles = {
  admin: "ผู้ดูแลระบบ",
  manager: "ผู้จัดการ",
  practitioner: "ผู้รักษา",
  reception: "ต้อนรับ",
  finance: "การเงิน",
  pharmacy: "เภสัชกรรม",
};
export default function StaffSettings({
  token,
  user,
  onError,
  onDirty,
  onBusy,
  onPasswordChanged,
}) {
  const [users, setUsers] = useState([]),
    [audit, setAudit] = useState([]);
  const [draft, setDraft] = useState({
    email: "",
    password: "",
    role: "practitioner",
  });
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm: "",
  });
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const config = { headers: { Authorization: `Bearer ${token}` } };
  const dirty = Boolean(
    draft.email || draft.password || Object.values(passwords).some(Boolean),
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
  const load = async () => {
    if (user.role !== "admin") return;
    const [u, a] = await Promise.all([
      api.get("/users?limit=100", config),
      api.get("/audit", config),
    ]);
    setUsers(u.data);
    setAudit(a.data);
  };
  const run = async (action) => {
    setBusy(true);
    onBusy(true);
    setMessage("");
    try {
      await action();
    } catch (e) {
      setMessage(
        e.response?.status === 409
          ? "มีอีเมลนี้แล้ว หรือไม่สามารถปิดบัญชีตัวเอง/ผู้ดูแลคนสุดท้ายได้"
          : e.response?.status === 422
            ? "ตรวจอีเมลและรหัสผ่าน: อย่างน้อย 12 ตัวอักษร ไม่เกิน 72 ไบต์"
            : onError(e),
      );
    } finally {
      setBusy(false);
      onBusy(false);
    }
  };
  useEffect(() => {
    run(load);
  }, [token]);
  return (
    <section aria-busy={busy}>
      <fieldset className="module-fields" disabled={busy}>
        <h2>บัญชีและความปลอดภัย</h2>
        <p className="subtle">
          {user.email} · {roles[user.role]}
        </p>
        {message && (
          <p className="notice" role="status">
            {message}
          </p>
        )}
        {dirty && (
          <button
            className="secondary"
            disabled={busy}
            onClick={() => {
              setDraft({ email: "", password: "", role: "practitioner" });
              setPasswords({
                current_password: "",
                new_password: "",
                confirm: "",
              });
            }}
          >
            ล้างข้อมูลที่ยังไม่บันทึก
          </button>
        )}
        <details className="opd-section">
          <summary>เปลี่ยนรหัสผ่านของฉัน</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (passwords.new_password !== passwords.confirm) {
                setMessage("รหัสผ่านใหม่ทั้งสองช่องไม่ตรงกัน");
                return;
              }
              run(async () => {
                await api.post(
                  "/auth/change-password",
                  {
                    current_password: passwords.current_password,
                    new_password: passwords.new_password,
                  },
                  config,
                );
                setPasswords({
                  current_password: "",
                  new_password: "",
                  confirm: "",
                });
                onDirty(false);
                onPasswordChanged();
              });
            }}
          >
            <p>
              รหัสผ่านใหม่อย่างน้อย 12 ตัวอักษร ไม่เกิน 72 ไบต์
              เมื่อบันทึกต้องเข้าสู่ระบบใหม่ทุกอุปกรณ์
            </p>
            <div className="field-row">
              {[
                ["current_password", "รหัสผ่านปัจจุบัน"],
                ["new_password", "รหัสผ่านใหม่"],
                ["confirm", "ยืนยันรหัสผ่านใหม่"],
              ].map(([key, label]) => (
                <label className="field" key={key}>
                  {label}
                  <input
                    type="password"
                    required
                    autoComplete={
                      key === "current_password"
                        ? "current-password"
                        : "new-password"
                    }
                    minLength={key === "current_password" ? 1 : 12}
                    value={passwords[key]}
                    onChange={(e) =>
                      setPasswords({ ...passwords, [key]: e.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            <div className="form-actions">
              <button className="primary" disabled={busy}>
                บันทึกรหัสผ่านใหม่
              </button>
            </div>
          </form>
        </details>
        {user.role === "admin" && (
          <>
            <details className="opd-section">
              <summary>เพิ่มบัญชีเจ้าหน้าที่</summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  run(async () => {
                    await api.post("/users", draft, config);
                    setDraft({ email: "", password: "", role: "practitioner" });
                    await load();
                    setMessage(
                      "สร้างบัญชีแล้ว กรุณาส่งมอบรหัสให้เจ้าหน้าที่เป็นการส่วนตัว",
                    );
                  });
                }}
              >
                <div className="field-row">
                  <label className="field">
                    อีเมลเจ้าหน้าที่
                    <input
                      required
                      type="email"
                      autoComplete="off"
                      value={draft.email}
                      onChange={(e) =>
                        setDraft({ ...draft, email: e.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    รหัสผ่านเริ่มต้น
                    <input
                      required
                      type="password"
                      autoComplete="new-password"
                      minLength="12"
                      value={draft.password}
                      onChange={(e) =>
                        setDraft({ ...draft, password: e.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    บทบาท
                    <select
                      value={draft.role}
                      onChange={(e) =>
                        setDraft({ ...draft, role: e.target.value })
                      }
                    >
                      {Object.entries(roles).map(([k, v]) => (
                        <option key={k} value={k}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-actions">
                  <button className="primary" disabled={busy}>
                    สร้างบัญชี
                  </button>
                </div>
              </form>
            </details>
            <h3>เจ้าหน้าที่</h3>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => run(load)}
            >
              โหลดบัญชีและประวัติล่าสุด
            </button>
            <ul className="service-list">
              {users.map((u) => (
                <li key={u.id}>
                  <div>
                    <strong>{u.email}</strong>
                    <p>
                      {roles[u.role]} · {u.active ? "ใช้งานอยู่" : "ปิดใช้งาน"}
                    </p>
                  </div>
                  <button
                    className="secondary"
                    disabled={busy || u.id === user.id}
                    onClick={() =>
                      run(async () => {
                        await api.patch(
                          `/users/${u.id}/status`,
                          { active: !u.active },
                          config,
                        );
                        await load();
                        setMessage("อัปเดตสถานะบัญชีแล้ว");
                      })
                    }
                  >
                    {u.active ? "ปิดบัญชี" : "เปิดบัญชี"}
                  </button>
                </li>
              ))}
            </ul>
            <p className="subtle">แสดง 100 บัญชีแรก</p>
            <details className="opd-section">
              <summary>ประวัติการทำรายการล่าสุด</summary>
              <p className="subtle">
                แสดง 100 เหตุการณ์ล่าสุด ไม่แสดงเนื้อหาเวชระเบียนหรือรหัสผ่าน
              </p>
              <ul className="service-list">
                {audit.map((a) => (
                  <li key={a.id}>
                    <div>
                      <strong>{a.action}</strong>
                      <p>
                        {new Date(a.created_at).toLocaleString("th-TH")} · ผู้ทำ{" "}
                        {users.find((u) => u.id === a.actor_id)?.email ||
                          a.actor_id}
                      </p>
                      <p>รายการ {a.target_id}</p>
                    </div>
                  </li>
                ))}
              </ul>
              {!audit.length && <p>ยังไม่มีเหตุการณ์ในรายการ</p>}
            </details>
          </>
        )}
      </fieldset>
    </section>
  );
}
