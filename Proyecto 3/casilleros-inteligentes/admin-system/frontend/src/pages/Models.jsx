import { useEffect, useState } from "react";
import api from "../api.js";

// CRUD de modelos de gestos — solo superusuario.
export default function Models() {
  const [models, setModels] = useState([]);
  const [form, setForm] = useState({ name: "", version: 1, symbols: "🖐,✊,✌,👍,☝,👌" });

  const load = () => api.get("/models/").then((r) => setModels(r.data));
  useEffect(() => { load(); }, []);

  const create = async () => {
    await api.post("/models/", {
      name: form.name,
      version: Number(form.version),
      symbols: form.symbols.split(",").map((s) => s.trim()),
      active: true,
    });
    setForm({ name: "", version: 1, symbols: "🖐,✊,✌,👍,☝,👌" });
    load();
  };

  const remove = async (id) => {
    await api.delete(`/models/${id}/`);
    load();
  };

  return (
    <div className="container">
      <h2>Modelos de gestos</h2>
      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Crear modelo</h3>
        <label>Nombre</label>
        <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <label>Versión</label>
        <input type="number" value={form.version}
               onChange={(e) => setForm({ ...form, version: e.target.value })} />
        <label>Símbolos (separados por coma, en orden de índice)</label>
        <input value={form.symbols} onChange={(e) => setForm({ ...form, symbols: e.target.value })} />
        <button className="btn" onClick={create}>Crear</button>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Nombre</th><th>Versión</th><th>Símbolos</th><th>Activo</th><th></th></tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.name}</td>
                <td>v{m.version}</td>
                <td className="symbols">{(m.symbols || []).join(" ")}</td>
                <td>{m.active ? "Sí" : "No"}</td>
                <td>
                  <button className="btn danger" onClick={() => remove(m.id)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
