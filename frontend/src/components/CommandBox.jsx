import { WandSparkles } from "lucide-react";

export default function CommandBox({ command, setCommand, onSubmit, loading }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <label htmlFor="command" className="text-sm font-bold text-slate-950">
        Smart Command Box
      </label>
      <textarea
        id="command"
        value={command}
        onChange={(event) => setCommand(event.target.value)}
        rows={5}
        className="mt-4 w-full resize-none rounded-md border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-4 focus:ring-blue-100"
        placeholder="Example: Convert this photo to Word"
      />
      <button className="btn-primary mt-4 w-full justify-center sm:w-auto" type="button" onClick={onSubmit} disabled={loading}>
        <WandSparkles size={17} aria-hidden="true" />
        {loading ? "Processing..." : "Start"}
      </button>
    </section>
  );
}
