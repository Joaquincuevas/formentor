import { useEffect, useState } from "react";
import api from "../api.js";
import BarChart from "../components/BarChart.jsx";

export default function UserDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/dashboard/user/").then((r) => setData(r.data));
  }, []);

  if (!data) return <div className="container">Cargando…</div>;

  return (
    <div className="container">
      <h2>Bienvenido</h2>
      <div className="grid">
        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Aperturas de casilleros — últimos 7 días</h3>
          <BarChart data={data.openings_last_7_days} />
        </div>
        <div className="card">
          <h3>Casillero más usado (7 días)</h3>
          <div className="stat">{data.most_used_locker || "—"}</div>
        </div>
        <div className="card">
          <h3>Ratio de intentos rechazados</h3>
          <div className="stat">{data.denied_ratio}</div>
        </div>
        <div className="card">
          <h3>Controladores en línea</h3>
          <div className="stat">
            {data.controllers_online}/{data.controllers_total}
          </div>
        </div>
      </div>
    </div>
  );
}
