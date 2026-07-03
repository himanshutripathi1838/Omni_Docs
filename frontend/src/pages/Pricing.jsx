import { Check } from "lucide-react";

const plans = [
  ["Free", "$0", ["10 documents/month", "Local storage", "Basic conversions"]],
  ["Pro", "$12", ["500 documents/month", "Batch processing", "Priority OCR"]],
  ["Business", "$39", ["Team workspace", "Admin analytics", "Shared history"]],
  ["Enterprise", "Custom", ["SLA support", "Custom storage", "Private deployment"]],
];

export default function Pricing() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <p className="section-kicker">Pricing</p>
      <h1 className="page-title">Plans for every document workflow</h1>
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {plans.map(([name, price, features]) => (
          <article key={name} className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-extrabold text-slate-950">{name}</h2>
            <p className="mt-4 text-3xl font-extrabold text-slate-950">{price}</p>
            <ul className="mt-6 space-y-3">
              {features.map((feature) => (
                <li key={feature} className="flex gap-2 text-sm text-slate-600">
                  <Check size={17} className="shrink-0 text-emerald-600" aria-hidden="true" />
                  {feature}
                </li>
              ))}
            </ul>
            <button className="btn-secondary mt-6 w-full justify-center" type="button">Choose plan</button>
          </article>
        ))}
      </div>
    </section>
  );
}
