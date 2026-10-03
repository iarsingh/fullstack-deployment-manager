import React, { useEffect, useState } from "react";

type Deployment = { id: string; name: string; environment: string };

export function App() {
  const [rows, setRows] = useState<Deployment[]>([]);
  useEffect(() => {
    fetch("/deployments")
      .then((response) => response.json())
      .then((body) => setRows(body.deployments));
  }, []);
  return (
    <main>
      <h1>Deployments</h1>
      <ul>
        {rows.map((row) => (
          <li key={row.id}>{row.name} {row.environment}</li>
        ))}
      </ul>
    </main>
  );
}
