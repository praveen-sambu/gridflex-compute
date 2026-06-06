import Link from "next/link";

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">GridFlex Compute v2</p>
          <h1>Shift flexible GPU jobs away from stressed grid windows.</h1>
          <p className="lede">
            This Next.js app is the command centre for the hackathon demo. It visualises the mock scheduler response,
            grid stress timeline, workload queue and NIM-style decision explanations.
          </p>
          <div className="button-row">
            <Link className="button primary" href="/dashboard">
              Open dashboard
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}