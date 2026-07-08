import { useEffect, useState } from "react";
import api from "../api.js";
import BarChart from "../components/BarChart.jsx";

export default function SuperDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/dashboard/superuser/").then((r) => setData(r.data));
  }, []);

  if (!data) return <div className="container">Cargando…</div>;

  const tiles = [
    ["Usuarios", data.users_count],
    ["Controladores", data.controllers_count],
    ["Casilleros", data.lockers_count],
    ["Modelos activos", data.active_models],
    ["Controladores en línea", data.controllers_online],
    ["Controladores offline", data.controllers_offline],
    ["Intentos rechazados", data.total_denied_attempts],
    ["Controlador más activo", data.busiest_controller || "—"],
  ];

  return (
    <div className="container">
      <h2>Dashboard general (superusuario)</h2>
      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Aperturas de casilleros — últimos 7 días</h3>
        <BarChart data={data.openings_last_7_days} />
      </div>
      <div className="grid">
        {tiles.map(([label, value]) => (
          <div className="card" key={label}>
            <h3>{label}</h3>
            <div className="stat">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
