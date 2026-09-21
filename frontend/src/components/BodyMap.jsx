import { useState } from "react";

export function readMarks(value) {
  try {
    return JSON.parse(value || "[]")
      .filter(
        (p) =>
          ["หน้า", "หลัง", "ซ้าย", "ขวา"].includes(p.view) &&
          Number.isFinite(p.x) &&
          Number.isFinite(p.y) &&
          p.x >= 0 &&
          p.x <= 100 &&
          p.y >= 0 &&
          p.y <= 100,
      )
      .slice(0, 20);
  } catch {
    return [];
  }
}
export default function BodyMap({ value = "", onChange, readOnly = false, disabled = false }) {
  const [view, setView] = useState("หน้า"),
    [region, setRegion] = useState("คอ");
  const marks = readMarks(value);
  const positions = {
    ศีรษะ: [50, 10],
    คอ: [50, 22],
    ไหล่: [30, 28],
    แขน: [22, 43],
    หลัง: [50, 42],
    เอว: [50, 53],
    เข่า: [39, 73],
    เท้า: [38, 94],
  };
  const add = (x, y) => {
    if (!readOnly && !disabled && marks.length < 20)
      onChange(
        JSON.stringify([
          ...marks,
          { view, x: Math.round(x), y: Math.round(y) },
        ]),
      );
  };
  return (
    <div className="body-map">
      <p>
        ผังตำแหน่งที่ผู้รักษาบันทึก{" "}
        {readOnly
          ? ""
          : "· แตะจุดบนภาพ หรือเลือกบริเวณด้านล่าง (สูงสุด 20 จุด)"}
      </p>
      <div className="clinical-tabs no-print" aria-label="มุมมองร่างกาย">
        {["หน้า", "หลัง", "ซ้าย", "ขวา"].map((v) => (
          <button
            type="button"
            key={v}
            aria-pressed={view === v}
            onClick={() => setView(v)}
          >
            ด้าน{v}
          </button>
        ))}
      </div>
      <div className="body-map-content">
        <svg
          viewBox="0 0 120 260"
          role="img"
          aria-label={`ผังร่างกายด้าน${view}`}
          onClick={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            add(
              ((e.clientX - r.left) / r.width) * 100,
              ((e.clientY - r.top) / r.height) * 100,
            );
          }}
        >
          <g fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="60" cy="26" r="17" />
            <path d="M50 43v14L32 65 13 129 25 133 42 86 42 137 35 233 49 239 60 161 71 239 85 233 78 137 78 86 95 133 107 129 88 65 70 57v-14" />
          </g>
          {marks.map(
            (p, i) =>
              p.view === view && (
                <g key={i}>
                  <circle cx={p.x * 1.2} cy={p.y * 2.6} r="7" fill="#A14238" />
                  <text
                    x={p.x * 1.2}
                    y={p.y * 2.6 + 3}
                    textAnchor="middle"
                    fill="white"
                    fontSize="8"
                  >
                    {i + 1}
                  </text>
                </g>
              ),
          )}
        </svg>
        <div>
          {!readOnly && (
            <>
              <label className="field">
                เลือกบริเวณเพื่อเพิ่มจุด
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  {Object.keys(positions).map((k) => (
                    <option key={k}>{k}</option>
                  ))}
                </select>
              </label>
              <button
                className="secondary"
                type="button"
                disabled={marks.length >= 20}
                onClick={() => add(...positions[region])}
              >
                เพิ่มจุดบริเวณ{region}
              </button>
            </>
          )}
          <ol>
            {marks.map((p, i) => (
              <li key={i}>
                จุด {i + 1} · ด้าน{p.view} ({p.x}%, {p.y}%)
                {!readOnly && (
                  <button
                    className="secondary"
                    type="button"
                    onClick={() =>
                      onChange(JSON.stringify(marks.filter((_, j) => j !== i)))
                    }
                  >
                    ลบจุด {i + 1}
                  </button>
                )}
              </li>
            ))}
          </ol>
          {!marks.length && <p>ยังไม่ได้ระบุตำแหน่ง</p>}
        </div>
      </div>
    </div>
  );
}
