"use client";

import { useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080";

export default function HomePage() {
  const [role, setRole] = useState("cashier");
  const [tableNo, setTableNo] = useState("T1");
  const [items, setItems] = useState([{ item_id: "it-1", item_name: "Paneer Tikka", qty: 1, unit_price: 220 }]);
  const [orderId, setOrderId] = useState("");
  const total = useMemo(() => items.reduce((a, b) => a + (b.qty * b.unit_price), 0), [items]);

  async function createOrder() {
    const res = await fetch(`${API}/orders`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Role": role,
        "Idempotency-Key": crypto.randomUUID()
      },
      body: JSON.stringify({ table_no: tableNo, lines: items })
    });
    const data = await res.json();
    if (data.order_id) setOrderId(data.order_id);
  }

  async function finalizeBill() {
    if (!orderId) return;
    await fetch(`${API}/bills`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Role": role,
        "Idempotency-Key": crypto.randomUUID()
      },
      body: JSON.stringify({ order_id: orderId, gstin: "27ABCDE1234F1Z5" })
    });
    alert("Bill finalized");
  }

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif", maxWidth: 720 }}>
      <h1>Restro Medha POS (MVP)</h1>
      <label>Role: </label>
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="manager">manager</option>
        <option value="cashier">cashier</option>
      </select>
      <div style={{ marginTop: 12 }}>
        <label>Table: </label>
        <input value={tableNo} onChange={(e) => setTableNo(e.target.value)} />
      </div>
      <p>Order total: Rs {total.toFixed(2)}</p>
      <button onClick={createOrder}>Create Order</button>
      <button onClick={finalizeBill} style={{ marginLeft: 8 }}>Finalize Bill</button>
      <p>Order ID: {orderId || "-"}</p>
    </main>
  );
}
