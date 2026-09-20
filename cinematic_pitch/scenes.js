/**
 * AeroCPI + AeroGuide — Cinematic 16:9 Pitch Film Scene Definitions
 * Problem Statement: SIH26056 | Team: BuzzCodeX | Theme: Smart Automation
 */

const SCENES_DATA = [
  // -------------------------------------------------------------
  // SCENE 01: Cold Open & Radar Hologram
  // -------------------------------------------------------------
  {
    id: 1,
    title: "Opening & Radar Hologram",
    duration: 12000,
    render: () => `
      <div class="s01-brand-badge">
        <span class="glass-pill">SMART INDIA HACKATHON 2026</span>
        <span class="glass-pill">PROBLEM STATEMENT SIH26056</span>
        <span class="glass-pill">SMART AUTOMATION</span>
      </div>

      <h1 class="hero-title s01-title-hero metallic-text">
        REAL-TIME AIRFARE PRICE INDEX
      </h1>

      <div class="s01-subtitle-hero">
        AeroCPI &nbsp;+&nbsp; AeroGuide
      </div>

      <div class="s01-tagline">
        MEASURE THE MARKET &nbsp;·&nbsp; EXPLAIN THE MOVEMENT &nbsp;·&nbsp; GUIDE THE DECISION
      </div>

      <div class="s01-meta-bar">
        <span><strong>Team:</strong> BuzzCodeX</span>
        <span>•</span>
        <span><strong>Canonical Observations:</strong> 36K+ Persisted Quotes</span>
        <span>•</span>
        <span><strong>Longitudinal Panel:</strong> 140 Tier-1 Cells</span>
        <span>•</span>
        <span><strong>Multi-Source Coverage:</strong> 100% Dual-Source</span>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.2);
      setTimeout(() => audio.playMetallicImpact(), 500);
      setTimeout(() => audio.playHeroChord(), 900);
    }
  },

  // -------------------------------------------------------------
  // SCENE 02: The Real-World Market Crisis
  // -------------------------------------------------------------
  {
    id: 2,
    title: "The Airfare Volatility Crisis",
    duration: 13000,
    render: () => `
      <div class="s02-grid">
        <div class="glass-panel s02-stat-box">
          <span class="mono-tag neon-rose">THE CONSUMER & POLICY DILEMMA</span>
          <div class="cpi-huge-number">150M+</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff;">
            Annual Domestic Passengers in India Face Unpredictable Dynamic Pricing
          </div>
          <div style="color: var(--text-dim); font-size: 0.95rem; line-height: 1.6;">
            A ticket from Delhi to Bengaluru can swing from <span class="neon-mint">₹4,200</span> to <span class="neon-rose">₹14,500</span> in 48 hours without any structural inflation explanation.
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1.2rem;">
          <div class="glass-panel" style="padding: 1.5rem; border-left: 4px solid var(--crimson);">
            <div class="mono-tag" style="color: var(--crimson);">01. OFFICIAL CPI PUBLICATION LAG</div>
            <div style="color: #ffffff; font-weight: 600; font-size: 1.05rem; margin-top: 0.3rem;">Monthly Physical Shelf Surveys</div>
            <div style="color: var(--text-dim); font-size: 0.88rem; margin-top: 0.2rem;">
              MoSPI CPI tracks static retail baskets with monthly lags. Algorithmic dynamic airfares update every minute.
            </div>
          </div>

          <div class="glass-panel" style="padding: 1.5rem; border-left: 4px solid var(--saffron-gold);">
            <div class="mono-tag" style="color: var(--saffron-gold);">02. CROSS-SOURCE FARE DISPERSION</div>
            <div style="color: #ffffff; font-weight: 600; font-size: 1.05rem; margin-top: 0.3rem;">5.45% Median Platform Spread</div>
            <div style="color: var(--text-dim); font-size: 0.88rem; margin-top: 0.2rem;">
              OTAs and aggregators show diverging fare populations. Single-source scrapers produce biased index numbers.
            </div>
          </div>

          <div class="glass-panel" style="padding: 1.5rem; border-left: 4px solid var(--cyan-bright);">
            <div class="mono-tag" style="color: var(--cyan-bright);">03. ZERO PRICE EXPLAINABILITY</div>
            <div style="color: #ffffff; font-weight: 600; font-size: 1.05rem; margin-top: 0.3rem;">Black-Box Flight Scrapers</div>
            <div style="color: var(--text-dim); font-size: 0.88rem; margin-top: 0.2rem;">
              Scrapers display prices without explaining why fares spiked or whether travellers should book now or wait.
            </div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1400), 400);
      setTimeout(() => audio.playDataTick(1600), 800);
    }
  },

  // -------------------------------------------------------------
  // SCENE 03: Flight Price Ticker Morph
  // -------------------------------------------------------------
  {
    id: 3,
    title: "Flight Price Ticker Morph",
    duration: 12000,
    render: () => `
      <div class="s03-stage">
        <span class="glass-pill" style="margin-bottom: 1.2rem;">DYNAMIC PRICING PHENOMENON</span>
        <h2 class="hero-title metallic-text" style="font-size: 2.8rem; text-align: center;">
          WHAT IS HAPPENING TO THIS FARE?
        </h2>

        <div class="glass-panel s03-ticket-card" style="margin-top: 1.5rem;">
          <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 0.85rem;">
            <span style="color: var(--cyan-bright);">BLR ➔ DEL · NON-STOP</span>
            <span style="color: var(--text-dim);">T+31 DAYS (ECONOMY)</span>
          </div>

          <div class="s03-price-ticker" id="scene3-price-ticker">
            ₹10,495
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 0.85rem;">
            <span class="glass-pill" style="color: var(--saffron-gold); border-color: var(--saffron-gold);">WATCH FARE</span>
            <span style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">Historical Median: ₹10,859</span>
          </div>
        </div>

        <div class="s03-chips-grid">
          <div class="s03-chip">
            <span style="font-size: 1.5rem;">📊</span>
            <div>
              <div style="font-weight: 700; color: #ffffff;">Historical Corridor Baseline</div>
              <div style="font-size: 0.8rem; color: var(--text-dim);">Currently in P50 median percentile zone.</div>
            </div>
          </div>
          <div class="s03-chip">
            <span style="font-size: 1.5rem;">⚡</span>
            <div>
              <div style="font-weight: 700; color: #ffffff;">Cross-Source Agreement</div>
              <div style="font-size: 0.8rem; color: var(--text-dim);">0.98% median spread between Google & Duffel.</div>
            </div>
          </div>
          <div class="s03-chip">
            <span style="font-size: 1.5rem;">📅</span>
            <div>
              <div style="font-weight: 700; color: #ffffff;">Flexible Date Savings</div>
              <div style="font-size: 0.8rem; color: var(--text-dim);">Nearby dates indicate potential ₹1,200 savings.</div>
            </div>
          </div>
          <div class="s03-chip">
            <span style="font-size: 1.5rem;">🔒</span>
            <div>
              <div style="font-weight: 700; color: #ffffff;">11-Node Explainability</div>
              <div style="font-size: 0.8rem; color: var(--text-dim);">Complete mathematical audit trace behind advice.</div>
            </div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      const prices = ["₹4,890", "₹7,250", "₹14,990", "₹10,495"];
      let pIdx = 0;
      const interval = setInterval(() => {
        const el = document.getElementById('scene3-price-ticker');
        if (el && pIdx < prices.length) {
          el.textContent = prices[pIdx];
          audio.playDataTick(900 + pIdx * 200);
          pIdx++;
        } else {
          clearInterval(interval);
        }
      }, 700);
    }
  },

  // -------------------------------------------------------------
  // SCENE 04: Advance Purchase Horizons (T+1 to T+60)
  // -------------------------------------------------------------
  {
    id: 4,
    title: "Advance Purchase Horizons (T+1 to T+60)",
    duration: 12000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 1rem;">TEMPORAL MEASUREMENT AXIS</span>
      <h1 class="hero-title metallic-text" style="font-size: 3rem;">
        ADVANCE PURCHASE HORIZONS
      </h1>
      <p class="hero-sub">
        Standardized statistical sampling across 6 distinct purchasing windows captures airline yield curves.
      </p>

      <div class="s04-timeline-wrapper">
        <div class="s04-spline-line"></div>
        <div class="s04-nodes">
          
          <div class="s04-node-item">
            <div class="s04-node-dot">T+1</div>
            <div class="mono-tag" style="color: var(--crimson);">EMERGENCY</div>
            <div style="font-size: 0.78rem; color: var(--text-dim);">Next-Day Spike</div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+7</div>
            <div class="mono-tag" style="color: var(--saffron-gold);">TACTICAL</div>
            <div style="font-size: 0.78rem; color: var(--text-dim);">Weekly Business</div>
          </div>

          <div class="s04-node-item anchor">
            <div class="s04-node-dot" style="background: #f59e0b; color: #030712;">T+15</div>
            <div class="mono-tag" style="color: var(--saffron-gold); font-weight: 800;">★ HEADLINE ANCHOR</div>
            <div style="font-size: 0.78rem; color: #ffffff;">Primary CPI Baseline</div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+30</div>
            <div class="mono-tag" style="color: var(--cyan-bright);">STANDARD</div>
            <div style="font-size: 0.78rem; color: var(--text-dim);">Monthly Leisure</div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+45</div>
            <div class="mono-tag" style="color: var(--mint-bright);">ADVANCE</div>
            <div style="font-size: 0.78rem; color: var(--text-dim);">Early Vacation</div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+60</div>
            <div class="mono-tag" style="color: var(--indigo-bright);">FAR HORIZON</div>
            <div style="font-size: 0.78rem; color: var(--text-dim);">Deep Booking</div>
          </div>

        </div>
      </div>

      <div class="glass-panel" style="padding: 1.2rem 2.5rem; margin-top: 2rem; display: flex; gap: 3rem; align-items: center;">
        <div>
          <span class="mono-tag neon-gold">ANCHOR STANDARD:</span>
          <span style="color: #ffffff; font-weight: 600; margin-left: 0.5rem;">T+15 is the official Headline Anchor for national inflation reporting.</span>
        </div>
        <div style="border-left: 1px solid var(--glass-border); padding-left: 2rem;">
          <span class="mono-tag neon-cyan">PANEL SCALE:</span>
          <span style="color: #ffffff; font-weight: 600; margin-left: 0.5rem;">140 cells (10 routes × 14 dates) tracked continuously.</span>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playLaserSweep(), 600);
    }
  },

  // -------------------------------------------------------------
  // SCENE 05: The Paradigm Shift (AeroCPI + AeroGuide)
  // -------------------------------------------------------------
  {
    id: 5,
    title: "The Paradigm Shift: AeroCPI + AeroGuide",
    duration: 13000,
    render: () => `
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <span class="glass-pill" style="margin-bottom: 0.5rem;">THE DUAL-LAYER BREAKTHROUGH</span>
        
        <h1 class="s05-huge-title">
          MEASURE &nbsp;·&nbsp; EXPLAIN &nbsp;·&nbsp; GUIDE &nbsp;·&nbsp; VERIFY
        </h1>

        <p class="hero-sub">
          We did not stop at web scraping. We engineered a national airfare measurement system AND an explainable consumer decision cockpit.
        </p>

        <div class="s05-four-pillars">
          <div class="glass-panel s05-pillar-card" style="border-top: 3px solid var(--mint-bright);">
            <div class="mono-tag neon-mint">01. MEASURE</div>
            <div style="font-weight: 700; color: #ffffff; font-size: 1.05rem;">National Airfare Index</div>
            <div style="color: var(--text-dim); font-size: 0.84rem; line-height: 1.45;">
              Jevons geometric aggregation weighted by DGCA annual passenger traffic across 10 trunk routes.
            </div>
          </div>

          <div class="glass-panel s05-pillar-card" style="border-top: 3px solid var(--cyan-bright);">
            <div class="mono-tag neon-cyan">02. EXPLAIN</div>
            <div style="font-weight: 700; color: #ffffff; font-size: 1.05rem;">5A Econometric Model</div>
            <div style="color: var(--text-dim); font-size: 0.84rem; line-height: 1.45;">
              Decomposes price fluctuations into Carrier Strategy, Horizon Urgency, Day of Week, and Corridor.
            </div>
          </div>

          <div class="glass-panel s05-pillar-card" style="border-top: 3px solid var(--saffron-gold);">
            <div class="mono-tag neon-gold">03. GUIDE</div>
            <div style="font-weight: 700; color: #ffffff; font-size: 1.05rem;">AeroGuide Cockpit</div>
            <div style="color: var(--text-dim); font-size: 0.84rem; line-height: 1.45;">
              Advises travellers to BOOK NOW, WATCH FARE, or FLEX DATES with an 11-node explainability trace.
            </div>
          </div>

          <div class="glass-panel s05-pillar-card" style="border-top: 3px solid var(--purple-neon);">
            <div class="mono-tag neon-purple">04. VERIFY</div>
            <div style="font-weight: 700; color: #ffffff; font-size: 1.05rem;">Audit & Provenance</div>
            <div style="color: var(--text-dim); font-size: 0.84rem; line-height: 1.45;">
              Every quote backed by immutable SHA-256 payload fingerprints and reproducible JSON manifests.
            </div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.3);
      setTimeout(() => audio.playMetallicImpact(), 400);
      setTimeout(() => audio.playHeroChord(), 700);
    }
  },

  // -------------------------------------------------------------
  // SCENE 06: Multi-Source Data Ingestion Engine
  // -------------------------------------------------------------
  {
    id: 6,
    title: "Multi-Source Data Ingestion Engine",
    duration: 13000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 1rem;">DATA ACQUISITION ARCHITECTURE</span>
      <h1 class="hero-title metallic-text" style="font-size: 3rem;">
        GENUINE MULTI-SOURCE INGESTION
      </h1>
      <p class="hero-sub">
        100% Dual-Source coverage across all 140 Tier-1 panel cells. No artificial single-source vulnerability.
      </p>

      <div class="s06-sources-grid">
        <div class="glass-panel s06-source-card" style="border-left: 4px solid var(--cyan-bright);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="mono-tag neon-cyan">SOURCE 01</span>
            <span class="glass-pill" style="color: var(--mint-bright); border-color: var(--mint-bright);">● LIVE WEB</span>
          </div>
          <div style="font-size: 1.3rem; font-weight: 800; color: #ffffff;">Google Flights</div>
          <div style="color: var(--text-dim); font-size: 0.88rem; line-height: 1.5;">
            High-frequency public search parser extracting multi-carrier economy flight populations and base fare structures.
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--cyan-bright); margin-top: auto;">
            17,492+ Observations Logged
          </div>
        </div>

        <div class="glass-panel s06-source-card" style="border-left: 4px solid var(--saffron-gold);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="mono-tag neon-gold">SOURCE 02</span>
            <span class="glass-pill" style="color: var(--mint-bright); border-color: var(--mint-bright);">● SCRAPY SPIDER</span>
          </div>
          <div style="font-size: 1.3rem; font-weight: 800; color: #ffffff;">EaseMyTrip Spider</div>
          <div style="color: var(--text-dim); font-size: 0.88rem; line-height: 1.5;">
            Dedicated Scrapy crawler spider capturing unauthenticated OTA flight cards with GZIP raw HTML persistence.
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--saffron-gold); margin-top: auto;">
            18,806+ Observations Logged
          </div>
        </div>

        <div class="glass-panel s06-source-card" style="border-left: 4px solid var(--purple-neon);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="mono-tag neon-purple">SOURCE 03</span>
            <span class="glass-pill" style="color: var(--cyan-bright); border-color: var(--cyan-bright);">● REST API PILOT</span>
          </div>
          <div style="font-size: 1.3rem; font-weight: 800; color: #ffffff;">Duffel REST API</div>
          <div style="color: var(--text-dim); font-size: 0.88rem; line-height: 1.5;">
            Credential-gated GDS aggregator verifying direct carrier wholesale feeds against consumer OTA search results.
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--purple-neon); margin-top: auto;">
            0.98% Median Diff on DEL-BOM
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playDataTick(1200), 400);
      setTimeout(() => audio.playLaserSweep(), 800);
    }
  },

  // -------------------------------------------------------------
  // SCENE 07: 10-Field Canonical Normalization
  // -------------------------------------------------------------
  {
    id: 7,
    title: "10-Field Canonical Normalization",
    duration: 12000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 1rem;">DATA STANDARDIZATION</span>
      <h1 class="hero-title metallic-text" style="font-size: 3rem;">
        CANONICAL OBSERVATION PIPELINE
      </h1>
      <p class="hero-sub">
        Every quote passes through strict typing, arithmetic checks, and SHA-256 fingerprinting before database entry.
      </p>

      <div class="s07-pipeline-flow">
        <div class="glass-panel s07-pipe-card" style="border-left: 3px solid var(--cyan-bright);">
          <span class="mono-tag neon-cyan">STEP 1</span>
          <div style="font-weight: 700; color: #ffffff;">Raw Capture</div>
          <div style="color: var(--text-dim); font-size: 0.82rem;">GZIP payload storage with SHA-256 hash.</div>
        </div>

        <div style="color: var(--text-muted); font-size: 1.2rem;">➔</div>

        <div class="glass-panel s07-pipe-card" style="border-left: 3px solid var(--mint-bright);">
          <span class="mono-tag neon-mint">STEP 2</span>
          <div style="font-weight: 700; color: #ffffff;">10-Field Schema</div>
          <div style="color: var(--text-dim); font-size: 0.82rem;">Route, date, timestamp, airline, fare, APW.</div>
        </div>

        <div style="color: var(--text-muted); font-size: 1.2rem;">➔</div>

        <div class="glass-panel s07-pipe-card" style="border-left: 3px solid var(--saffron-gold);">
          <span class="mono-tag neon-gold">STEP 3</span>
          <div style="font-weight: 700; color: #ffffff;">Validation Rules</div>
          <div style="color: var(--text-dim); font-size: 0.82rem;">Non-stop filter, duplicate removal, price bounds.</div>
        </div>

        <div style="color: var(--text-muted); font-size: 1.2rem;">➔</div>

        <div class="glass-panel s07-pipe-card" style="border-left: 3px solid var(--purple-neon);">
          <span class="mono-tag neon-purple">STEP 4</span>
          <div style="font-weight: 700; color: #ffffff;">Harmonization</div>
          <div style="color: var(--text-dim); font-size: 0.82rem;">Jevons cell grouping & cross-source mapping.</div>
        </div>
      </div>

      <div class="glass-panel" style="padding: 1.2rem 2.5rem; margin-top: 2rem; width: 100%; max-width: 1350px; display: flex; justify-content: space-around; font-family: var(--font-mono); font-size: 0.85rem;">
        <div><strong>Database Quotes:</strong> 36,862 Persisted</div>
        <div>•</div>
        <div><strong>Deduplication Loss:</strong> &lt;0.04%</div>
        <div>•</div>
        <div><strong>Schema Strictness:</strong> 100% Verified</div>
        <div>•</div>
        <div><strong>Pytest Suite:</strong> 301/301 Passed</div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1600), 500);
    }
  },

  // -------------------------------------------------------------
  // SCENE 08: Jevons Geometric Index & DGCA Route Network
  // -------------------------------------------------------------
  {
    id: 8,
    title: "Jevons Geometric Index & DGCA Route Network",
    duration: 13000,
    render: () => `
      <div class="s08-network-grid">
        <!-- India Route Map SVG -->
        <div class="glass-panel" style="padding: 1.5rem; position: relative;">
          <div class="mono-tag neon-cyan" style="margin-bottom: 0.75rem;">TOP 10 DGCA TRUNK CORRIDORS (&gt;45% OF INDIA PASSENGER TRAFFIC)</div>
          
          <svg class="s08-map-svg" viewBox="0 0 500 400" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Map Grid -->
            <path d="M50 50 H450 M50 150 H450 M50 250 H450 M50 350 H450" stroke="rgba(56, 189, 248, 0.08)" stroke-width="1" />
            <path d="M100 20 V380 M200 20 V380 M300 20 V380 M400 20 V380" stroke="rgba(56, 189, 248, 0.08)" stroke-width="1" />

            <!-- Flight Route Arcs -->
            <!-- DEL to BOM -->
            <path d="M220 90 Q 180 180 160 230" stroke="#06b6d4" stroke-width="3" stroke-dasharray="6 3" filter="drop-shadow(0 0 6px #06b6d4)" />
            <!-- DEL to BLR -->
            <path d="M220 90 Q 230 200 230 320" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6 3" filter="drop-shadow(0 0 6px #38bdf8)" />
            <!-- BOM to BLR -->
            <path d="M160 230 Q 190 280 230 320" stroke="#10b981" stroke-width="3" stroke-dasharray="6 3" filter="drop-shadow(0 0 6px #10b981)" />
            <!-- DEL to HYD -->
            <path d="M220 90 Q 230 160 240 240" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4 2" />
            <!-- DEL to CCU -->
            <path d="M220 90 Q 300 130 380 180" stroke="#a855f7" stroke-width="2.5" stroke-dasharray="4 2" />

            <!-- City Nodes -->
            <!-- DEL -->
            <circle cx="220" cy="90" r="7" fill="#f59e0b" filter="drop-shadow(0 0 10px #f59e0b)" />
            <text x="232" y="95" fill="#ffffff" font-family="JetBrains Mono" font-size="12" font-weight="800">DEL (28.4%)</text>

            <!-- BOM -->
            <circle cx="160" cy="230" r="6" fill="#06b6d4" filter="drop-shadow(0 0 8px #06b6d4)" />
            <text x="95" y="235" fill="#ffffff" font-family="JetBrains Mono" font-size="11" font-weight="700">BOM (21.2%)</text>

            <!-- BLR -->
            <circle cx="230" cy="320" r="6" fill="#10b981" filter="drop-shadow(0 0 8px #10b981)" />
            <text x="245" y="325" fill="#ffffff" font-family="JetBrains Mono" font-size="11" font-weight="700">BLR (17.5%)</text>

            <!-- HYD -->
            <circle cx="240" cy="240" r="5" fill="#38bdf8" />
            <text x="252" y="245" fill="#94a3b8" font-family="JetBrains Mono" font-size="10">HYD</text>

            <!-- CCU -->
            <circle cx="380" cy="180" r="5" fill="#a855f7" />
            <text x="392" y="185" fill="#94a3b8" font-family="JetBrains Mono" font-size="10">CCU</text>
          </svg>
        </div>

        <!-- Formula and Route List -->
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div class="mono-tag neon-gold" style="margin-bottom: 0.5rem;">JEVONS GEOMETRIC FORMULA</div>
            <div style="font-family: var(--font-mono); font-size: 1.15rem; font-weight: 800; color: #ffffff; background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--glass-border);">
              I<sub>h</sub> = 100 · exp( &Sigma; w<sub>r</sub> · ln( J<sub>r,h</sub> / 100 ) )
            </div>
            <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 0.5rem;">
              Satisfies Transitivity, Homogeneity, and Time Reversal axioms without substitution bias.
            </div>
          </div>

          <div class="s08-corridor-list">
            <div class="s08-corridor-row"><span>DEL ↔ BOM (Mumbai Trunk)</span><strong class="neon-cyan">Weight: 0.284</strong></div>
            <div class="s08-corridor-row"><span>BLR ↔ DEL (Tech Corridor)</span><strong class="neon-mint">Weight: 0.175</strong></div>
            <div class="s08-corridor-row"><span>BOM ↔ BLR (South Trunk)</span><strong class="neon-gold">Weight: 0.142</strong></div>
            <div class="s08-corridor-row"><span>DEL ↔ HYD (Capital Run)</span><strong class="neon-purple">Weight: 0.098</strong></div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.2);
      setTimeout(() => audio.playDataTick(1100), 400);
      setTimeout(() => audio.playDataTick(1400), 700);
    }
  },

  // -------------------------------------------------------------
  // SCENE 09: 5A Econometric Price Driver Attribution
  // -------------------------------------------------------------
  {
    id: 9,
    title: "5A Econometric Attribution Model",
    duration: 13000,
    render: () => `
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <span class="glass-pill" style="margin-bottom: 0.5rem;">PRICE DRIVER DECOMPOSITION</span>
        <h1 class="hero-title metallic-text" style="font-size: 2.8rem;">
          WHY DID THE AIRFARE CHANGE?
        </h1>
        <p class="hero-sub">
          The 5A Log-Linear Econometric Model isolates exact market forces driving price index movement.
        </p>

        <div class="glass-panel s09-contrib-chart">
          <div class="s09-bar-row">
            <div style="font-weight: 700; color: #ffffff;">Carrier Pricing</div>
            <div class="s09-bar-left"></div>
            <div class="s09-bar-right"><div class="s09-bar-fill pos" style="width: 65%;"></div></div>
            <div style="color: var(--mint-bright); font-weight: 800;">+2.85 pts</div>
          </div>

          <div class="s09-bar-row">
            <div style="font-weight: 700; color: #ffffff;">Horizon Urgency</div>
            <div class="s09-bar-left"><div class="s09-bar-fill neg" style="width: 45%;"></div></div>
            <div class="s09-bar-right"></div>
            <div style="color: var(--crimson); font-weight: 800;">-1.45 pts</div>
          </div>

          <div class="s09-bar-row">
            <div style="font-weight: 700; color: #ffffff;">Day of Week (Sun)</div>
            <div class="s09-bar-left"></div>
            <div class="s09-bar-right"><div class="s09-bar-fill pos" style="width: 35%;"></div></div>
            <div style="color: var(--mint-bright); font-weight: 800;">+0.92 pts</div>
          </div>

          <div class="s09-bar-row">
            <div style="font-weight: 700; color: #ffffff;">Corridor Specific</div>
            <div class="s09-bar-left"><div class="s09-bar-fill neg" style="width: 25%;"></div></div>
            <div class="s09-bar-right"></div>
            <div style="color: var(--crimson); font-weight: 800;">-0.65 pts</div>
          </div>

          <div class="s09-bar-row" style="border-top: 1px dashed var(--glass-border); padding-top: 0.6rem;">
            <div style="font-weight: 800; color: var(--cyan-bright);">Net Index Shift</div>
            <div class="s09-bar-left"></div>
            <div class="s09-bar-right"><div class="s09-bar-fill pos" style="width: 40%; background: var(--cyan-bright);"></div></div>
            <div style="color: var(--cyan-bright); font-weight: 800;">+1.67 pts</div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1200), 300);
      setTimeout(() => audio.playDataTick(1500), 600);
      setTimeout(() => audio.playDataTick(1800), 900);
    }
  },

  // -------------------------------------------------------------
  // SCENE 10: AeroGuide Live Consumer Experience
  // -------------------------------------------------------------
  {
    id: 10,
    title: "AeroGuide Live Consumer Experience",
    duration: 14000,
    render: () => `
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center; width: 100%;">
        <div style="display: flex; gap: 1rem; align-items: center;">
          <span class="glass-pill" style="color: var(--mint-bright); border-color: var(--mint-bright);">● LIVE CONSUMER PROTOTYPE</span>
          <span class="glass-pill">BLR ➔ DEL · ₹10,495 · WATCH FARE</span>
        </div>

        <h2 class="hero-title metallic-text" style="font-size: 2.5rem; margin-top: 0.4rem;">
          AEROGUIDE DECISION COCKPIT
        </h2>

        <div class="s10-screenshot-frame">
          <img src="./assets/01_GUIDE.png" alt="AeroGuide Live Hero Screenshot" class="s10-screenshot-img">
        </div>

        <div style="display: flex; gap: 1.5rem; justify-content: center; margin-top: 1rem; font-family: var(--font-mono); font-size: 0.84rem;">
          <span class="glass-pill" style="color: var(--cyan-bright);">36K+ Canonical Observations</span>
          <span class="glass-pill" style="color: var(--saffron-gold);">0.98% Median Diff</span>
          <span class="glass-pill" style="color: var(--mint-bright);">±2 Days Smart Search Matrix</span>
          <span class="glass-pill" style="color: var(--purple-neon);">11-Node Explainability</span>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.2);
      setTimeout(() => audio.playMetallicImpact(), 400);
    }
  },

  // -------------------------------------------------------------
  // SCENE 11: 11-Node Explainable Decision Trace
  // -------------------------------------------------------------
  {
    id: 11,
    title: "11-Node Explainable Decision Trace",
    duration: 14000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 0.6rem;">FULL MATHEMATICAL EXPLAINABILITY</span>
      <h1 class="hero-title metallic-text" style="font-size: 2.8rem;">
        11-NODE DECISION AUDIT TRACE
      </h1>
      <p class="hero-sub">
        Every traveller recommendation is derived through an auditable, deterministic inference chain.
      </p>

      <div class="s11-trace-pipeline">
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-cyan">01. QUERY</div>
          <div style="color: #ffffff; font-weight: 700;">BLR-DEL</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-cyan">02. APW</div>
          <div style="color: #ffffff; font-weight: 700;">T+31 Days</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-cyan">03. FARE</div>
          <div style="color: #ffffff; font-weight: 700;">₹10,495</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-gold">04. MEDIAN</div>
          <div style="color: #ffffff; font-weight: 700;">₹10,859</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-gold">05. P-RANK</div>
          <div style="color: #ffffff; font-weight: 700;">P50 Zone</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag neon-mint">06. SPREAD</div>
          <div style="color: #ffffff; font-weight: 700;">0.98% Diff</div>
        </div>
        <div style="color: var(--text-muted);">➔</div>
        <div class="glass-panel s11-trace-node" style="border-color: var(--saffron-gold);">
          <div class="mono-tag neon-gold">07. ACTION</div>
          <div style="color: var(--saffron-gold); font-weight: 800;">WATCH FARE</div>
        </div>
      </div>

      <div class="s10-screenshot-frame" style="height: 280px; margin-top: 1.5rem;">
        <img src="./assets/02_WHY_TRACE.png" alt="11-Node Trace Drawer Screenshot" class="s10-screenshot-img">
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playLaserSweep(), 500);
      setTimeout(() => audio.playDataTick(1400), 900);
    }
  },

  // -------------------------------------------------------------
  // SCENE 12: Cross-Source Agreement Lab & Empirical Dispersion
  // -------------------------------------------------------------
  {
    id: 12,
    title: "Cross-Source Agreement Lab & Dispersion",
    duration: 13000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 0.6rem;">CROSS-SOURCE TRUTH</span>
      <h1 class="hero-title metallic-text" style="font-size: 2.8rem;">
        SOURCE AGREEMENT LAB
      </h1>
      <p class="hero-sub">
        Empirical measurement of cross-platform airfare dispersion across Google Flights, EaseMyTrip, and Duffel API.
      </p>

      <div class="s12-dispersion-grid">
        <div class="glass-panel" style="padding: 1.8rem; border-left: 4px solid var(--mint-bright);">
          <div class="mono-tag neon-mint">HIGH AGREEMENT (&le; 5% SPREAD)</div>
          <div style="font-size: 2.5rem; font-weight: 900; color: #ffffff; margin: 0.4rem 0;">0.98%</div>
          <div style="font-weight: 700; color: #ffffff;">DEL-BOM Duffel Pilot vs Google Flights</div>
          <div style="color: var(--text-dim); font-size: 0.85rem; margin-top: 0.4rem;">
            Direct API quotes closely track aggregator medians with just ₹65 absolute median difference.
          </div>
        </div>

        <div class="glass-panel" style="padding: 1.8rem; border-left: 4px solid var(--saffron-gold);">
          <div class="mono-tag neon-gold">MODERATE SPREAD (5 - 15% SPREAD)</div>
          <div style="font-size: 2.5rem; font-weight: 900; color: #ffffff; margin: 0.4rem 0;">5.45%</div>
          <div style="font-weight: 700; color: #ffffff;">Google Flights vs EaseMyTrip Spiders</div>
          <div style="color: var(--text-dim); font-size: 0.85rem; margin-top: 0.4rem;">
            Reflects OTA convenience fee inclusions and airline promotional coupon differences.
          </div>
        </div>
      </div>

      <div class="s10-screenshot-frame" style="height: 250px; margin-top: 1.2rem;">
        <img src="./assets/05_SOURCE_AGREEMENT.png" alt="Source Agreement Lab Screenshot" class="s10-screenshot-img">
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1300), 400);
    }
  },

  // -------------------------------------------------------------
  // SCENE 13: Scientific Safeguards & Evidence-Gated ML
  // -------------------------------------------------------------
  {
    id: 13,
    title: "Scientific Safeguards & Evidence Gates",
    duration: 13000,
    render: () => `
      <span class="glass-pill" style="margin-bottom: 0.6rem;">INTEGRITY & TRUST GATES</span>
      <h1 class="hero-title metallic-text" style="font-size: 2.8rem;">
        EVIDENCE-GATED SCIENTIFIC RIGOR
      </h1>
      <p class="hero-sub">
        We refuse to fabricate artificial predictions. Predictive AI is strictly locked until longitudinal depth accumulates.
      </p>

      <div class="s13-safeguards-grid">
        <div class="glass-panel" style="padding: 1.8rem; border: 1.5px solid var(--crimson);">
          <div class="mono-tag" style="color: var(--crimson);">🔒 ML FORECAST GATE: LOCKED</div>
          <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem;">0 / 7 Target Pairs</div>
          <div style="color: var(--text-dim); font-size: 0.85rem; line-height: 1.5; margin-top: 0.4rem;">
            Predictive AI model is hard-gated with <code>INSUFFICIENT_DATA</code> status. Zero fabricated forward curves.
          </div>
        </div>

        <div class="glass-panel" style="padding: 1.8rem; border: 1.5px solid var(--cyan-bright);">
          <div class="mono-tag neon-cyan">SHA-256 RAW PROVENANCE</div>
          <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem;">Immutable Cryptographic Ledger</div>
          <div style="color: var(--text-dim); font-size: 0.85rem; line-height: 1.5; margin-top: 0.4rem;">
            Every raw web capture and API response is stored in GZIP with an immutable SHA-256 digest on disk.
          </div>
        </div>

        <div class="glass-panel" style="padding: 1.8rem; border: 1.5px solid var(--mint-bright);">
          <div class="mono-tag neon-mint">DETERMINISTIC AUDIT CLI</div>
          <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem;">301/301 Pytest Verified</div>
          <div style="color: var(--text-dim); font-size: 0.85rem; line-height: 1.5; margin-top: 0.4rem;">
            100% reproducible calculation manifests generated via <code>python -m app.cli audit</code>.
          </div>
        </div>
      </div>

      <div class="glass-panel" style="padding: 1rem 2.5rem; margin-top: 1.8rem; width: 100%; max-width: 1300px; text-align: center;">
        <span class="mono-tag" style="color: var(--saffron-gold);">STATUTORY BOUNDARY:</span>
        <span style="color: #ffffff; font-size: 0.88rem; margin-left: 0.5rem;">AeroCPI is an independent experimental airfare measurement system for SIH 2026. It is not official MoSPI CPI.</span>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playMetallicImpact(), 400);
    }
  },

  // -------------------------------------------------------------
  // SCENE 14: Grand Finale & Sovereign Vision
  // -------------------------------------------------------------
  {
    id: 14,
    title: "Grand Finale: Sovereign Airfare Intelligence",
    duration: 25000,
    render: () => `
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <div class="s14-emblem">✈</div>
        
        <div class="glass-pill" style="margin-bottom: 0.6rem;">FROZEN PRODUCTION RESULT · T+15 HEADLINE</div>
        
        <div class="s14-headline-result">96.21</div>
        
        <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 0.4rem;">
          AeroCPI &nbsp;+&nbsp; AeroGuide
        </div>

        <div style="display: flex; gap: 1.5rem; justify-content: center; margin-top: 1.2rem;">
          <div class="glass-pill">36K+ OBSERVATIONS</div>
          <div class="glass-pill">140 TIER-1 CELLS</div>
          <div class="glass-pill">100% DUAL-SOURCE</div>
          <div class="glass-pill">301/301 TESTS PASSED</div>
        </div>

        <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 2rem; font-family: var(--font-mono); font-size: 1.3rem; font-weight: 800;">
          <span class="neon-cyan">MEASURE.</span>
          <span style="color: #ffffff;">EXPLAIN.</span>
          <span class="neon-gold">GUIDE.</span>
          <span class="neon-mint">VERIFY.</span>
        </div>

        <div style="font-family: var(--font-mono); font-size: 0.95rem; color: var(--text-dim); margin-top: 1.5rem;">
          Smart India Hackathon 2026 · Team BuzzCodeX · Problem Statement SIH26056
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.5);
      setTimeout(() => audio.playMetallicImpact(), 500);
      setTimeout(() => audio.playHeroChord(), 900);
    }
  }
];

if (typeof window !== 'undefined') {
  window.SCENES_DATA = SCENES_DATA;
}
