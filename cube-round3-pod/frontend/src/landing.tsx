import {
  ArrowUpRight,
  PackageCheck,
  ScanLine,
  ClipboardList,
  ShieldCheck,
  ArrowRight,
  Eye,
  FileCheck2,
} from "lucide-react";
import "./landing.css";

export function Landing() {
  return (
    <div className="landing">
      <a className="lp-skip" href="#product">
        Skip to content
      </a>
      <header className="lp-nav">
        <a className="lp-logo" href="/" aria-label="Pack Manager home">
          <PackageCheck size={28} />
          <span>
            Pack<span>Manager</span>
          </span>
        </a>
        <nav aria-label="Product navigation">
          <a href="#workflow">How it works</a>
          <a href="#evidence">The evidence</a>
          <a className="lp-nav-cta" href="/workspace">
            Open workspace <ArrowUpRight size={16} />
          </a>
        </nav>
      </header>
      <main id="product" className="lp-main">
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <p className="lp-eyebrow">
              <span /> A CLEARER LAST CHECK
            </p>
            <h1>
              The right items.
              <br />
              The right order.
              <br />
              <em>Before you seal.</em>
            </h1>
            <p className="lp-intro">
              A focused inspection workspace for the moment that matters:
              checking what’s in the box against what your customer ordered.
            </p>
            <div className="lp-actions">
              <a className="lp-primary" href="/workspace">
                Enter your workspace <ArrowUpRight size={20} />
              </a>
              <a className="lp-text-link" href="#workflow">
                See the workflow <ArrowRight size={17} />
              </a>
            </div>
            <div className="lp-hero-note">
              <ShieldCheck size={17} /> Evidence attached. Uncertainty visible.
              People in control.
            </div>
          </div>
          <div
            className="lp-visual"
            aria-label="Illustration of an open packing box; not an inspection result"
          >
            <div className="lp-visual-top">
              <span>
                <span className="lp-dot" /> THE PACK STATION
              </span>
              <span>01 / CAPTURE</span>
            </div>
            <svg
              className="lp-box"
              viewBox="0 0 600 480"
              role="img"
              aria-label="Illustrated open box with a notebook and two pens"
            >
              <defs>
                <linearGradient id="box-face" x2="0" y2="1">
                  <stop stopColor="#c3a98a" />
                  <stop offset="1" stopColor="#a78b6c" />
                </linearGradient>
                <pattern
                  id="surface-grid"
                  width="32"
                  height="32"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M32 0H0V32"
                    fill="none"
                    stroke="#d7dfd6"
                    strokeWidth=".5"
                  />
                </pattern>
              </defs>
              <rect width="600" height="480" fill="url(#surface-grid)" />
              <ellipse
                cx="300"
                cy="395"
                rx="190"
                ry="30"
                fill="#152737"
                opacity=".09"
              />
              <path d="M120 216L298 140 479 214 301 302Z" fill="#8d7054" />
              <path
                d="M120 216L301 302 301 419 120 327Z"
                fill="url(#box-face)"
              />
              <path d="M301 302L479 214 479 331 301 419Z" fill="#b49b7c" />
              <path d="M120 216L298 140 225 80 54 151Z" fill="#e1ceb4" />
              <path d="M298 140L479 214 549 150 378 78Z" fill="#d8c1a2" />
              <path d="M120 216L301 302 233 361 48 269Z" fill="#ddc7a8" />
              <path d="M301 302L479 214 553 273 366 366Z" fill="#e9d5b8" />
              <path d="M179 214L276 174 341 202 245 245Z" fill="#f3f2e8" />
              <path d="M176 204L274 163 342 191 244 234Z" fill="#176c68" />
              <path d="M185 202L279 163" stroke="#8cc7b7" strokeWidth="3" />
              <path
                d="M315 244L386 209M336 253L407 218"
                stroke="#172e3a"
                strokeWidth="10"
                strokeLinecap="round"
              />
              <path
                d="M320 241L327 238M341 250L348 247"
                stroke="#b9c6c4"
                strokeWidth="10"
              />
              <path
                d="M98 181V155H124M476 155H502V181M98 328V354H124M476 354H502V328"
                stroke="#247b6e"
                strokeWidth="2"
                fill="none"
              />
            </svg>
            <div className="lp-order-slip">
              <ClipboardList size={18} />
              <div>
                <strong>Start with the expected order</strong>
                <span>Then capture the visible contents.</span>
              </div>
              <ArrowUpRight size={18} />
            </div>
            <p className="lp-illustration-note">
              Product illustration · no AI result shown
            </p>
          </div>
        </section>
        <div className="lp-context">
          <span>BUILT FOR THE PACKING BENCH</span>
          <p>Merchant-fulfilled orders</p>
          <span aria-hidden="true">/</span>
          <p>Small catalogues</p>
          <span aria-hidden="true">/</span>
          <p>3PL pack stations</p>
        </div>
        <section id="workflow" className="lp-section">
          <div className="lp-section-heading">
            <div>
              <p className="lp-eyebrow">FROM ORDER TO EVIDENCE</p>
              <h2>
                A simple workflow.
                <br />A considered decision.
              </h2>
            </div>
            <p>
              Bring the order, the catalogue and a clear photograph together.
              Keep the decision connected to the evidence behind it.
            </p>
          </div>
          <div className="lp-steps">
            {[
              {
                n: "01",
                Icon: ClipboardList,
                title: "Define what belongs",
                text: "Save the expected SKUs, variants and quantities. Add reference photographs to distinguish similar products.",
              },
              {
                n: "02",
                Icon: ScanLine,
                title: "Make it visible",
                text: "Photograph the open box with every item and label exposed. One model request assesses the visible contents.",
              },
              {
                n: "03",
                Icon: FileCheck2,
                title: "Review, then act",
                text: "Compare supported observations with the order. Review mismatches and uncertainty before making the packing decision.",
              },
            ].map(({ n, Icon, title, text }) => (
              <article key={n}>
                <div className="lp-step-top">
                  <Icon size={25} />
                  <span>{n}</span>
                </div>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section id="evidence" className="lp-evidence">
          <div>
            <p className="lp-eyebrow">A RECORD YOU CAN EXAMINE</p>
            <h2>
              The answer matters.
              <br />
              <em>So does the why.</em>
            </h2>
            <p>
              An inspection should leave more than a coloured badge. Keep the
              original photograph, order snapshot, observations and human review
              together.
            </p>
            <a href="/workspace" className="lp-text-link">
              Explore the workspace <ArrowUpRight size={18} />
            </a>
          </div>
          <div className="lp-evidence-list">
            {[
              {
                Icon: Eye,
                title: "Visible evidence",
                text: "Original captures are retained. Hidden contents and unreadable labels are not treated as verified.",
              },
              {
                Icon: ShieldCheck,
                title: "Uncertainty has a place",
                text: "An unclear view can remain uncertain. A failed model request is saved for review, never approved automatically.",
              },
              {
                Icon: FileCheck2,
                title: "Human decisions stay attributed",
                text: "A supervisor can record a reasoned decision while preserving the original automated result.",
              },
            ].map(({ Icon, title, text }) => (
              <article key={title}>
                <Icon size={23} />
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
        <section className="lp-section lp-faq">
          <div>
            <p className="lp-eyebrow">BEFORE YOUR FIRST INSPECTION</p>
            <h2>Know the boundaries.</h2>
          </div>
          <div>
            <details>
              <summary>What do I need to get started?</summary>
              <p>
                A real product catalogue with distinguishing references, an
                order with quantities, and a clear open-box photograph.
                Automated inspection additionally requires a configured vision
                model.
              </p>
            </details>
            <details>
              <summary>Does this inspect hidden items?</summary>
              <p>
                No. The workflow is designed for exposed items in a bounded
                catalogue. Occlusion, unreadable variants and insufficient
                coverage need a new capture or human review.
              </p>
            </details>
            <details>
              <summary>Has accuracy been measured?</summary>
              <p>
                Not yet. Software and container checks have passed, but
                real-provider verification and independently labelled held-out
                evaluation are still pending. We publish no accuracy or savings
                claims.
              </p>
            </details>
          </div>
        </section>
        <section className="lp-final">
          <p className="lp-eyebrow">ONE BOX. A CLEAR RECORD.</p>
          <h2>
            Give the last check
            <br />
            the attention it deserves.
          </h2>
          <a href="/workspace" className="lp-primary">
            Open Pack Manager <ArrowUpRight size={20} />
          </a>
        </section>
      </main>
      <footer className="lp-footer">
        <a className="lp-logo" href="/">
          <PackageCheck size={23} /> PackManager
        </a>
        <p>CUBE Buildathon · PCK track</p>
        <a
          href="https://github.com/ganapathyshree007/cube-03-pack-manager"
          target="_blank"
          rel="noreferrer"
        >
          View source <ArrowUpRight size={15} />
        </a>
      </footer>
    </div>
  );
}
