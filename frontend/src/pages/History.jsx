import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar.jsx";
import { API_BASE_URL, getHistory } from "../services/api.js";

export default function History() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    getHistory().then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div className="workspace-shell">
      <Sidebar />
      <section className="workspace-main">
        <p className="section-kicker">History</p>
        <h1 className="page-title">Processed document history</h1>
        <div className="mt-8 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-5 py-4">Command</th>
                <th className="px-5 py-4">Task</th>
                <th className="px-5 py-4">Status</th>
                <th className="px-5 py-4">Output</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="px-5 py-4 font-medium text-slate-950">{item.command}</td>
                  <td className="px-5 py-4 text-slate-600">{item.detected_task}</td>
                  <td className="px-5 py-4 text-slate-600">{item.status}</td>
                  <td className="px-5 py-4">
                    {item.output_filename ? (
                      <a className="font-bold text-brand" href={`${API_BASE_URL}/api/documents/download/${item.output_filename}`}>
                        Download
                      </a>
                    ) : (
                      <span className="text-slate-400">None</span>
                    )}
                  </td>
                </tr>
              ))}
              {!items.length && (
                <tr>
                  <td className="px-5 py-10 text-center text-slate-500" colSpan="4">No processed documents yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
