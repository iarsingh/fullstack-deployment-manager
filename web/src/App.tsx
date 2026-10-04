import React, { FormEvent, useEffect, useState } from "react";

type Deployment = {
  id: string;
  name: string;
  environment: string;
  image: string;
  status: string;
  rollback_of: string | null;
};

const NEXT: Record<string, string[]> = {
  pending: ["running", "cancelled"],
  running: ["succeeded", "failed"],
};

export function App() {
  const [rows, setRows] = useState<Deployment[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "billing", environment: "dev", image: "billing:1.4.2" });

  const load = () =>
    fetch("/deployments")
      .then((response) => response.json())
      .then((body) => setRows(body.deployments));

  useEffect(() => {
    load();
  }, []);

  const send = async (url: string, body?: object) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      setError((await response.json()).detail);
      return;
    }
    setError("");
    load();
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    send("/deployments", form);
  };

  return (
    <main>
      <h1>Deployments</h1>
      <form onSubmit={submit}>
        <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        <select value={form.environment} onChange={(event) => setForm({ ...form, environment: event.target.value })}>
          <option value="dev">dev</option>
          <option value="staging">staging</option>
        </select>
        <input value={form.image} onChange={(event) => setForm({ ...form, image: event.target.value })} />
        <button type="submit">Record</button>
      </form>
      {error && <p role="alert">{error}</p>}
      <table>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{row.name}</td>
              <td>{row.environment}</td>
              <td>{row.image}</td>
              <td>{row.status}</td>
              <td>
                {(NEXT[row.status] || []).map((status) => (
                  <button key={status} onClick={() => send(`/deployments/${row.id}/status`, { status })}>
                    {status}
                  </button>
                ))}
                {row.status === "failed" && <button onClick={() => send(`/deployments/${row.id}/rollback`)}>roll back</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
