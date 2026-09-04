const API = "http://127.0.0.1:8000"; // adjust if backend runs elsewhere

async function refreshSlots() {
  const res = await fetch(`${API}/slots`);
  const data = await res.json();

  document.getElementById("stats").textContent =
    `${data.free} free / ${data.occupied} occupied / ${data.total} total`;

  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  data.slots.forEach((s) => {
    const div = document.createElement("div");
    div.className = `slot ${s.is_occupied ? "occ" : "free"}`;
    div.textContent = s.is_occupied ? `${s.code}\n${s.plate_code ?? ""}` : s.code;
    grid.appendChild(div);
  });
}

document.getElementById("entryForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const out = document.getElementById("entryResult");
  out.textContent = "Detecting…";
  try {
    const res = await fetch(`${API}/entry`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed");
    out.textContent =
      `Plate (raw): ${data.plate_raw}\n` +
      `Plate (canonical): ${data.plate_code}\n` +
      `Assigned slot: ${data.slot_code}\n` +
      `Guidance: ${data.guidance}`;
    refreshSlots();
  } catch (err) {
    out.textContent = `Error: ${err.message}`;
  }
});

document.getElementById("exitForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const out = document.getElementById("exitResult");
  out.textContent = "Detecting…";
  try {
    const res = await fetch(`${API}/exit`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed");
    out.textContent = data.freed
      ? `Plate ${data.plate_code} — slot freed.`
      : `Plate ${data.plate_code} — no matching occupied slot found.`;
    refreshSlots();
  } catch (err) {
    out.textContent = `Error: ${err.message}`;
  }
});

refreshSlots();
setInterval(refreshSlots, 4000);
