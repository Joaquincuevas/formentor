import { useEffect, useState } from "react";
import api from "../api.js";

const SYMBOLS = ["🖐", "✊", "✌", "👍", "☝", "👌"];

function keyToSymbols(key) {
  return (key || []).map((i) => SYMBOLS[i] ?? "?").join(" ");
}

export default function Controllers() {
  const [controllers, setControllers] = useState([]);
  const [modal, setModal] = useState(null); // {type, data}

  const load = () =>
    api.get("/controllers/").then((r) => setControllers(r.data));

  useEffect(() => { load(); }, []);

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h2>Controladores</h2>
        <button className="btn" onClick={() => setModal({ type: "controller" })}>
          + Añadir controlador
        </button>
      </div>

      {controllers.map((c) => (
        <div className="card" key={c.id} style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h3 style={{ color: "var(--text)" }}>
              {c.name} <small style={{ color: "var(--muted)" }}>({c.controller_id})</small>
            </h3>
            <span className={`badge ${c.is_online ? "on" : "off"}`}>
              {c.is_online ? "Conectado" : "Desconectado"}
            </span>
          </div>
          <table>
            <thead>
              <tr><th>Casillero</th><th>Dueño</th><th>Clave</th><th></th></tr>
            </thead>
            <tbody>
              {c.lockers.map((lk) => (
                <tr key={lk.id}>
                  <td>{lk.name} (#{lk.number})</td>
                  <td>{lk.owner_email || "—"}</td>
                  <td className="symbols">{keyToSymbols(lk.key)}</td>
                  <td>
                    <button className="btn secondary"
                            onClick={() => setModal({ type: "assign", data: lk })}>
                      Editar clave/dueño
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className="btn secondary" style={{ marginTop: 10 }}
                  onClick={() => setModal({ type: "locker", data: { controller: c.id } })}>
            + Añadir casillero
          </button>
        </div>
      ))}

      {modal?.type === "controller" && (
        <ControllerModal onClose={() => setModal(null)} onSaved={() => { setModal(null); load(); }} />
      )}
      {modal?.type === "locker" && (
        <LockerModal controllerId={modal.data.controller}
                     onClose={() => setModal(null)} onSaved={() => { setModal(null); load(); }} />
      )}
      {modal?.type === "assign" && (
        <AssignModal locker={modal.data}
                     onClose={() => setModal(null)} onSaved={() => { setModal(null); load(); }} />
      )}
    </div>
  );
}

// --- Modal: añadir controlador (define id, nombre y arranca sincronizacion) ---
function ControllerModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ controller_id: "", name: "" });
  const save = async () => {
    await api.post("/controllers/", form);
    onSaved();
  };
  return (
    <Modal title="Añadir controlador" onClose={onClose} onSave={save}>
      <label>ID del controlador (MQTT)</label>
      <input value={form.controller_id}
             onChange={(e) => setForm({ ...form, controller_id: e.target.value })}
             placeholder="ctrl-a1b2c3" />
      <label>Nombre</label>
      <input value={form.name}
             onChange={(e) => setForm({ ...form, name: e.target.value })}
             placeholder="Casilleros Gimnasio" />
      <p style={{ fontSize: 12, color: "var(--muted)" }}>
        Al crearlo se publica su configuración por MQTT. El controlador responde con
        la cantidad de casilleros activos durante la sincronización.
      </p>
    </Modal>
  );
}

// --- Modal: añadir casillero ---
function LockerModal({ controllerId, onClose, onSaved }) {
  const [form, setForm] = useState({ controller: controllerId, number: 1, name: "", owner_email: "" });
  const save = async () => {
    await api.post("/lockers/", form);
    onSaved();
  };
  return (
    <Modal title="Añadir casillero" onClose={onClose} onSave={save}>
      <label>Número (1-4)</label>
      <input type="number" min="1" max="4" value={form.number}
             onChange={(e) => setForm({ ...form, number: Number(e.target.value) })} />
      <label>Nombre</label>
      <input value={form.name}
             onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <label>Correo del dueño</label>
      <input type="email" value={form.owner_email}
             onChange={(e) => setForm({ ...form, owner_email: e.target.value })} />
    </Modal>
  );
}

// --- Modal: asignar clave y dueño (envia email + MQTT) ---
function AssignModal({ locker, onClose, onSaved }) {
  const [ownerEmail, setOwnerEmail] = useState(locker.owner_email || "");
  const [key, setKey] = useState(locker.key?.length === 4 ? locker.key : [0, 0, 0, 0]);
  const save = async () => {
    await api.post(`/lockers/${locker.id}/assign/`, { key, owner_email: ownerEmail });
    onSaved();
  };
  return (
    <Modal title={`Editar ${locker.name}`} onClose={onClose} onSave={save}>
      <label>Correo del dueño</label>
      <input type="email" value={ownerEmail}
             onChange={(e) => setOwnerEmail(e.target.value)} />
      <label>Clave (4 gestos)</label>
      <div style={{ display: "flex", gap: 8 }}>
        {key.map((g, idx) => (
          <select key={idx} value={g}
                  onChange={(e) => {
                    const nk = [...key];
                    nk[idx] = Number(e.target.value);
                    setKey(nk);
                  }}>
            {SYMBOLS.map((s, i) => (
              <option key={i} value={i}>{s}</option>
            ))}
          </select>
        ))}
      </div>
      <p className="symbols">{key.map((i) => SYMBOLS[i]).join(" ")}</p>
      <p style={{ fontSize: 12, color: "var(--muted)" }}>
        Al guardar se envía la clave al controlador por MQTT y un email al dueño con
        las figuras e instrucciones.
      </p>
    </Modal>
  );
}

function Modal({ title, children, onClose, onSave }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ color: "var(--text)" }}>{title}</h3>
        {children}
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
          <button className="btn secondary" onClick={onClose}>Cancelar</button>
          <button className="btn" onClick={onSave}>Guardar</button>
        </div>
      </div>
    </div>
  );
}
