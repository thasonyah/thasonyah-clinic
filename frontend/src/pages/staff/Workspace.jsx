import { useState } from "react";
import PasswordRecovery from "./PasswordRecovery";
import Pharmacy from "./Pharmacy";
import Billing from "./Billing";
import Scheduling from "./Scheduling";
import Records from "./Records";
import StaffSettings, { roles } from "./StaffSettings";
import { api } from "../../api/client";
import ServiceCatalog from "../design/ServiceCatalog";
import "../design/design.css";

export default function Workspace() {
  const [recovery, setRecovery] = useState(() =>
    window.location.hash.startsWith("#reset="),
  );
  const [recordsDirty, setRecordsDirty] = useState(false);
  const [recordsBusy, setRecordsBusy] = useState(false);
  const [section, setSection] = useState("services");
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [expired, setExpired] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [services, setServices] = useState([]);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const auth = (value) => ({
    headers: { Authorization: `Bearer ${value || token}` },
  });
  const load = async (value) => {
    const response = await api.get("/services", auth(value));
    setServices(response.data.map((s) => ({ ...s, price: Number(s.price) })));
  };
  const explain = (error) => {
    if (error.response?.status === 401) {
      if (user) {
        setExpired(true);
        return "session หมดอายุ ร่างยังอยู่ในหน่วยความจำ กรุณาเข้าสู่ระบบด้วยบัญชีเดิมเพื่อทำต่อ";
      }
      return "เข้าสู่ระบบไม่สำเร็จ กรุณาตรวจอีเมลและรหัสผ่าน";
    }
    if (error.response?.status === 409)
      return "รายการถูกแก้ไขแล้วหรือมีชื่อซ้ำ กรุณาโหลดข้อมูลล่าสุดก่อนแก้ไขอีกครั้ง";
    if (error.response?.status === 403)
      return "บัญชีนี้ไม่มีสิทธิ์ทำรายการในส่วนนี้";
    if (error.response?.status === 429)
      return "ลองเข้าสู่ระบบถี่เกินไป กรุณารอหนึ่งนาที";
    if (error.response?.status === 422)
      return "ตรวจชื่อ ราคา และระยะเวลาอีกครั้ง";
    return "เชื่อมต่อระบบไม่สำเร็จ กรุณาลองใหม่";
  };
  const login = async (e) => {
    e.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const response = await api.post("/auth/login", { email, password });
      const nextToken = response.data.access_token;
      const me = await api.get("/auth/me", auth(nextToken));
      if (expired && me.data.id !== user.id) {
        setNotice("ต้องใช้บัญชีเดิมเพื่อกลับไปยังร่างที่ค้างอยู่");
        return;
      }
      await load(nextToken);
      if (!expired)
        setSection(
          {
            admin: "settings",
            reception: "records",
            practitioner: "records",
            pharmacy: "pharmacy",
            finance: "billing",
            manager: "billing",
          }[me.data.role] || "services",
        );
      setExpired(false);
      setUser(me.data);
      setToken(nextToken);
      setPassword("");
    } catch (error) {
      setNotice(explain(error));
    } finally {
      setBusy(false);
    }
  };
  const saveService = async (id, values, expectedVersion) => {
    try {
      const old = services.find((s) => s.id === id);
      const response = id
        ? await api.patch(
            `/services/${id}`,
            {
              ...values,
              active: old.active,
              expected_version: expectedVersion,
            },
            auth(),
          )
        : await api.post("/services", values, auth());
      const saved = { ...response.data, price: Number(response.data.price) };
      setServices((list) =>
        id ? list.map((s) => (s.id === id ? saved : s)) : [...list, saved],
      );
      setNotice("บันทึกหัตถการลงฐานข้อมูลแล้ว");
    } catch (error) {
      throw new Error(explain(error));
    }
  };
  const toggleService = async (item) => {
    try {
      const response = await api.patch(
        `/services/${item.id}`,
        {
          name: item.name,
          price: item.price.toFixed(2),
          minutes: item.minutes,
          active: !item.active,
          expected_version: item.version,
        },
        auth(),
      );
      setServices((list) =>
        list.map((s) =>
          s.id === item.id
            ? { ...response.data, price: Number(response.data.price) }
            : s,
        ),
      );
      setNotice("อัปเดตสถานะในฐานข้อมูลแล้ว");
    } catch (error) {
      throw new Error(explain(error));
    }
  };
  return (
    <div className="clinic-preview">
      <main className="live-workspace">
        <header className="live-header">
          <img
            src="/brand/thasonyah-logo.jpg"
            alt="ธสัญญา คลินิก"
            width="64"
            height="64"
          />
          <h1>ธสัญญา คลินิกการแพทย์แผนไทย</h1>
          {user && (
            <button
              className="secondary"
              disabled={busy || recordsDirty || recordsBusy}
              onClick={async () => {
                setBusy(true);
                try {
                  await api.post("/auth/logout", {}, auth());
                  setToken("");
                  setUser(null);
                  setServices([]);
                  setRecordsDirty(false);
                  setNotice("");
                } catch (error) {
                  setNotice(explain(error));
                } finally {
                  setBusy(false);
                }
              }}
            >
              ออกจากระบบ
            </button>
          )}
        </header>
        {user && (
          <p className="live-user no-print">
            {user.email} · {roles[user.role]}
          </p>
        )}
        {import.meta.env.VITE_DEMO_MODE === "true" && (
          <p className="notice" role="status">
            ระบบสาธิต · บัญชีทดลองเปิดเผยโดยเจตนา ไม่มีข้อมูลจริง
            ห้ามกรอกข้อมูลคนไข้จริง
          </p>
        )}
        {notice && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}
        {!user && recovery ? (
          <PasswordRecovery onBack={() => setRecovery(false)} />
        ) : !user ? (
          <section className="panel form-panel live-login">
            <h2>เข้าสู่ระบบเจ้าหน้าที่</h2>
            <p className="subtle">ใช้บัญชีที่ผู้ดูแลคลินิกสร้างให้</p>
            <form onSubmit={login}>
              <label className="field">
                อีเมล
                <input
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <label className="field">
                รหัสผ่าน
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <div className="form-actions">
                <button className="primary" disabled={busy}>
                  {busy ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบ"}
                </button>
              </div>
            </form>
            <div className="form-actions">
              <button
                className="secondary"
                disabled={busy}
                onClick={() => {
                  setPassword("");
                  setNotice("");
                  setRecovery(true);
                }}
              >
                ลืมรหัสผ่าน
              </button>
            </div>
          </section>
        ) : (
          <>
            {expired && (
              <section className="panel form-panel live-login">
                <h2>เข้าสู่ระบบเพื่อทำงานต่อ</h2>
                <p>
                  ร่างยังไม่ถูกส่งและเก็บอยู่เฉพาะในหน่วยความจำ
                  อย่ารีโหลดหน้านี้
                </p>
                <form onSubmit={login}>
                  <label className="field">
                    บัญชีเดิม
                    <input type="email" value={user.email} readOnly />
                  </label>
                  <label className="field">
                    รหัสผ่านเพื่อทำงานต่อ
                    <input
                      type="password"
                      required
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </label>
                  <div className="form-actions">
                    <button className="primary" disabled={busy}>
                      เข้าสู่ระบบและกลับไปยังร่าง
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={busy}
                      onClick={() => {
                        setUser(null);
                        setToken("");
                        setExpired(false);
                        setRecordsDirty(false);
                        setPassword("");
                        setNotice("ละทิ้งร่างและออกจากระบบแล้ว");
                      }}
                    >
                      ละทิ้งร่างและออกจากระบบ
                    </button>
                  </div>
                </form>
              </section>
            )}
            <div hidden={expired}>
              <nav className="clinical-tabs" aria-label="เมนูเจ้าหน้าที่">
                <button
                  disabled={recordsDirty || recordsBusy}
                  aria-pressed={section === "services"}
                  onClick={() => setSection("services")}
                >
                  หัตถการ
                </button>
                {["reception", "practitioner"].includes(user.role) && (
                  <button
                    disabled={recordsDirty || recordsBusy}
                    aria-pressed={section === "records"}
                    onClick={() => setSection("records")}
                  >
                    ทะเบียนและการตรวจ
                  </button>
                )}
                <button
                  disabled={recordsDirty || recordsBusy}
                  aria-pressed={section === "settings"}
                  onClick={() => setSection("settings")}
                >
                  บัญชีและความปลอดภัย
                </button>
                {["admin", "reception", "practitioner"].includes(user.role) && (
                  <button
                    disabled={recordsDirty || recordsBusy}
                    aria-pressed={section === "schedule"}
                    onClick={() => setSection("schedule")}
                  >
                    {user.role === "admin" ? "ห้องและเตียง" : "นัดหมายและคิว"}
                  </button>
                )}
                {["practitioner", "finance", "manager"].includes(user.role) && (
                  <button
                    disabled={recordsDirty || recordsBusy}
                    aria-pressed={section === "billing"}
                    onClick={() => setSection("billing")}
                  >
                    {user.role === "manager"
                      ? "รายงาน"
                      : "ค่ารักษาและใบรับเงิน"}
                  </button>
                )}
                {["practitioner", "pharmacy"].includes(user.role) && (
                  <button
                    disabled={recordsDirty || recordsBusy}
                    aria-pressed={section === "pharmacy"}
                    onClick={() => setSection("pharmacy")}
                  >
                    ใบสั่งยาและคลังยา
                  </button>
                )}
              </nav>
              {section === "pharmacy" ? (
                <Pharmacy
                  token={token}
                  user={user}
                  onError={explain}
                  onDirty={setRecordsDirty}
                  onBusy={setRecordsBusy}
                />
              ) : section === "billing" ? (
                <Billing
                  services={services}
                  token={token}
                  user={user}
                  onError={explain}
                  onDirty={setRecordsDirty}
                  onBusy={setRecordsBusy}
                />
              ) : section === "schedule" ? (
                <Scheduling
                  token={token}
                  user={user}
                  onError={explain}
                  onDirty={setRecordsDirty}
                  onBusy={setRecordsBusy}
                />
              ) : section === "settings" ? (
                <StaffSettings
                  token={token}
                  user={user}
                  onError={explain}
                  onDirty={setRecordsDirty}
                  onBusy={setRecordsBusy}
                  onPasswordChanged={() => {
                    setToken("");
                    setUser(null);
                    setNotice(
                      "เปลี่ยนรหัสผ่านแล้ว กรุณาเข้าสู่ระบบด้วยรหัสใหม่",
                    );
                  }}
                />
              ) : section === "records" &&
                ["reception", "practitioner"].includes(user.role) ? (
                <Records
                  token={token}
                  user={user}
                  onError={explain}
                  onDirty={setRecordsDirty}
                  onBusy={setRecordsBusy}
                />
              ) : (
                <>
                  <h2>จัดการหัตถการ</h2>
                  <p className="subtle">
                    บัญชี {user.email} · {user.role}
                  </p>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={async () => {
                      setBusy(true);
                      try {
                        await load();
                        setNotice("โหลดข้อมูลล่าสุดแล้ว");
                      } catch (error) {
                        setNotice(explain(error));
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    โหลดข้อมูลล่าสุด
                  </button>
                  <ServiceCatalog
                    services={services}
                    setServices={setServices}
                    flash={setNotice}
                    live
                    onSave={saveService}
                    onToggle={toggleService}
                    canManage={user.permissions.includes("clinic.manage")}
                  />
                </>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
