import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./style.css";
import Workspace from "./pages/staff/Workspace";
import DesignPreview from "./pages/design/DesignPreview";

function App() {
  return (
    <main className="min-h-screen bg-stone-50 px-6 py-20 text-stone-800">
      <div className="mx-auto max-w-2xl">
        <p className="mb-4 text-sm text-teal-700">คลินิกแพทย์แผนไทย</p>
        <h1 className="text-3xl font-semibold">กำลังเตรียมระบบบริการคลินิก</h1>
        <p className="mt-5 leading-8">
          ระบบยังไม่เปิดรับข้อมูลคนไข้
          กรุณาติดต่อเจ้าหน้าที่คลินิกสำหรับการนัดหมาย
        </p>
      </div>
    </main>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/staff/*" element={<Workspace />} />
        <Route path="/design/*" element={<DesignPreview />} />
        <Route path="*" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
