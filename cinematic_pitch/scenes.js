/**
 * AeroCPI Cinematic Pitch — 14 Scene Definitions & Dynamic Animations
 * Crafted for SIH 2026 (Team BUZZCODEX · SIH26056)
 */

const SCENES_DATA = [
  // -------------------------------------------------------------
  // SCENE 01: Grand Opening
  // -------------------------------------------------------------
  {
    id: 1,
    title: "Opening & Title",
    duration: 11000,
    render: () => `
      <div class="s01-brand-line"></div>
      <div class="s01-team-name">TEAM BUZZCODEX</div>
      <h1 class="s01-sih-title metallic-text">SMART INDIA HACKATHON 2026</h1>
      <div class="s01-problem-badge glass-pill">
        <span style="color: var(--saffron-gold);">PROBLEM CODE:</span> SIH26056
      </div>
      <div class="s01-problem-title">
        "REAL-TIME AIRFARE PRICE INDEX FOR INDIA"
      </div>
      <div style="margin-top: 3rem; display: flex; align-items: center; gap: 1rem; opacity: 0.8;">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--cyan-glow)" stroke-width="1.5">
          <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
        </svg>
        <span class="mono-tag" style="letter-spacing: 0.2em;">AEROCPI CINEMATIC OBSERVATORY</span>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.2);
      setTimeout(() => audio.playMetallicImpact(), 600);
      setTimeout(() => audio.playDataTick(1600), 1200);
    }
  },

  // -------------------------------------------------------------
  // SCENE 02: Why Does India Need This?
  // -------------------------------------------------------------
  {
    id: 2,
    title: "Why Does India Need This?",
    duration: 12000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1.5rem;">MACROECONOMIC CONTEXT</div>
      <h1 class="hero-title metallic-text">WHY DOES INDIA NEED THIS?</h1>
      
      <div class="s02-grid" style="margin-top: 2.5rem;">
        <div class="glass-panel s02-stat-box">
          <div class="mono-tag" style="color: var(--saffron-gold);">INDIAN DOMESTIC AVIATION</div>
          <div class="cpi-huge-number">150M+</div>
          <div style="color: var(--text-dim); font-size: 1.1rem; line-height: 1.6;">
            Passengers travel across India's domestic skies annually, making airfare a critical component of modern consumer mobility.
          </div>
          <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
            <div class="glass-pill" style="font-size: 0.75rem;">10 DGCA TRUNK CORRIDORS</div>
            <div class="glass-pill" style="font-size: 0.75rem;">HIGH-FREQUENCY MARKET</div>
          </div>
        </div>

        <div class="glass-panel s02-stat-box" style="border-color: rgba(56, 189, 248, 0.4);">
          <div class="mono-tag" style="color: var(--cyan-glow);">THE MEASUREMENT CHALLENGE</div>
          <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #ffffff; line-height: 1.3;">
            "CPI measures changes in the cost of living."
          </div>
          <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--coral-red); line-height: 1.3;">
            "But airfare does not have ONE fixed price."
          </div>
          <div style="color: var(--text-dim); font-size: 1rem; margin-top: 0.5rem; line-height: 1.6;">
            Unlike standard consumer goods with fixed shelf prices, airline tariffs change by the minute, by advance horizon, and by carrier algorithm.
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(900), 400);
      setTimeout(() => audio.playDataTick(1400), 800);
    }
  },

  // -------------------------------------------------------------
  // SCENE 03: Airfare is a Moving Market (Dynamic Ticket Morph)
  // -------------------------------------------------------------
  {
    id: 3,
    title: "Airfare is a Moving Market",
    duration: 13000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem; color: var(--coral-red); border-color: rgba(244,63,94,0.4);">
        THE VOLATILITY PROBLEM
      </div>
      <h1 class="hero-title metallic-text">AIRFARE IS NOT A FIXED PRICE.</h1>
      <p class="hero-sub">The same seat on the same route shifts continuously based on time and capacity.</p>

      <div style="display: flex; gap: 3rem; align-items: center; margin-top: 2.5rem; width: 100%; max-width: 1200px; justify-content: center;">
        
        <!-- Ticket Visual -->
        <div class="glass-panel s03-ticket-card" style="border-color: rgba(56,189,248,0.5);">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 1rem;">
            <div>
              <div class="mono-tag" style="color: var(--cyan-glow);">FLIGHT CORRIDOR</div>
              <div style="font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: #ffffff;">DEL ➔ BOM</div>
            </div>
            <div style="text-align: right;">
              <div class="mono-tag">CABIN</div>
              <div style="font-weight: 700; color: var(--text-dim);">ECONOMY (Y)</div>
            </div>
          </div>

          <div>
            <div class="mono-tag" style="margin-bottom: 0.25rem;">OBSERVED FARE QUOTE</div>
            <div id="s03-ticket-price" class="s03-price-ticker cyan-metallic">₹6,314</div>
            <div id="s03-ticker-status" style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--mint-glow);">
              ● BASELINE QUOTE RECORDED
            </div>
          </div>
        </div>

        <!-- 4 Contributing Factors -->
        <div class="s03-chips-grid">
          <div class="s03-chip glass-panel">
            <div style="font-size: 1.5rem; color: var(--cyan-glow);">01</div>
            <div>
              <div style="font-weight: 700; color: #ffffff;">ROUTE & NETWORK</div>
              <div style="font-size: 0.85rem; color: var(--text-dim);">Distance, airport charges, corridor density</div>
            </div>
          </div>
          <div class="s03-chip glass-panel">
            <div style="font-size: 1.5rem; color: var(--saffron-gold);">02</div>
            <div>
              <div style="font-weight: 700; color: #ffffff;">TRAVEL CALENDAR</div>
              <div style="font-size: 0.85rem; color: var(--text-dim);">Day of week, seasonal festival spikes</div>
            </div>
          </div>
          <div class="s03-chip glass-panel">
            <div style="font-size: 1.5rem; color: var(--coral-red);">03</div>
            <div>
              <div style="font-weight: 700; color: #ffffff;">BOOKING HORIZON</div>
              <div style="font-size: 0.85rem; color: var(--text-dim);">Lead time: T+1 close-in vs T+45 advance</div>
            </div>
          </div>
          <div class="s03-chip glass-panel">
            <div style="font-size: 1.5rem; color: var(--mint-glow);">04</div>
            <div>
              <div style="font-weight: 700; color: #ffffff;">DYNAMIC INVENTORY</div>
              <div style="font-size: 0.85rem; color: var(--text-dim);">Revenue management seat allocation</div>
            </div>
          </div>
        </div>

      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(0.9);
      // Dynamic price ticker morph animation
      const priceElem = document.getElementById('s03-ticket-price');
      const statusElem = document.getElementById('s03-ticker-status');
      if (priceElem && statusElem) {
        const sequence = [
          { p: "₹6,314", s: "● BASELINE QUOTE RECORDED", c: "var(--mint-glow)", delay: 0 },
          { p: "₹6,880", s: "▲ CLOSE-IN SURGE (+8.9%)", c: "var(--coral-red)", delay: 2000 },
          { p: "₹7,126", s: "▲ SEAT BUCKET EXHAUSTED (+12.8%)", c: "var(--coral-red)", delay: 4500 },
          { p: "₹8,025", s: "▲ PEAK DEMAND ALGORITHM (+27.1%)", c: "var(--coral-red)", delay: 7000 }
        ];

        sequence.forEach(item => {
          setTimeout(() => {
            if (!document.getElementById('s03-ticket-price')) return;
            priceElem.textContent = item.p;
            statusElem.textContent = item.s;
            statusElem.style.color = item.c;
            audio.playDataTick(item.delay === 0 ? 1200 : 1800);
          }, item.delay);
        });
      }
    }
  },

  // -------------------------------------------------------------
  // SCENE 04: Booking Horizon Term Structure
  // -------------------------------------------------------------
  {
    id: 4,
    title: "Booking Horizon Term Structure",
    duration: 13000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">ADVANCE PURCHASE HORIZONS</div>
      <h1 class="hero-title metallic-text">TIMING CHANGES THE PRICE.</h1>
      <p class="hero-sub">Airfares follow a deterministic lead-time curve across purchase windows.</p>

      <div class="s04-timeline-wrapper">
        <div class="s04-spline-line"></div>
        <div class="s04-nodes">
          
          <div class="s04-node-item">
            <div class="s04-node-dot">T+1</div>
            <div style="text-align: center;">
              <div style="font-weight: 700; color: #ffffff;">Next-Day</div>
              <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--coral-red); font-weight: 700;">63.50</div>
              <div class="mono-tag" style="font-size: 0.7rem; color: var(--text-muted);">-36.50 pts</div>
            </div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+7</div>
            <div style="text-align: center;">
              <div style="font-weight: 700; color: #ffffff;">1-Week</div>
              <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--cyan-glow); font-weight: 700;">99.86</div>
              <div class="mono-tag" style="font-size: 0.7rem; color: var(--text-muted);">-0.14 pts</div>
            </div>
          </div>

          <div class="s04-node-item anchor">
            <div class="s04-node-dot" style="background: var(--saffron-gold); color: #030712;">T+15</div>
            <div style="text-align: center;">
              <div style="font-weight: 800; color: var(--saffron-gold);">HEADLINE ANCHOR</div>
              <div style="font-family: var(--font-display); font-size: 1.5rem; color: #ffffff; font-weight: 800;">96.21</div>
              <div class="mono-tag" style="font-size: 0.75rem; color: var(--saffron-gold); font-weight: 700;">-3.79 pts</div>
            </div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+30</div>
            <div style="text-align: center;">
              <div style="font-weight: 700; color: #ffffff;">1-Month</div>
              <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--cyan-glow); font-weight: 700;">90.60</div>
              <div class="mono-tag" style="font-size: 0.7rem; color: var(--text-muted);">-9.40 pts</div>
            </div>
          </div>

          <div class="s04-node-item">
            <div class="s04-node-dot">T+45</div>
            <div style="text-align: center;">
              <div style="font-weight: 700; color: #ffffff;">45-Day Advance</div>
              <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--cyan-glow); font-weight: 700;">88.95</div>
              <div class="mono-tag" style="font-size: 0.7rem; color: var(--text-muted);">-11.05 pts</div>
            </div>
          </div>

        </div>
      </div>

      <div class="glass-panel" style="padding: 1.25rem 2.5rem; border-color: rgba(245,158,11,0.5); margin-top: 1.5rem;">
        <span style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; color: #ffffff;">
          "So which price do we measure?"
        </span>
        <span style="color: var(--text-dim); margin-left: 1rem;">
          A single quote cannot represent air travel inflation. We must measure the full term structure.
        </span>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playDataTick(1200), 500);
      setTimeout(() => audio.playDataTick(1500), 1000);
      setTimeout(() => audio.playMetallicImpact(), 2000);
    }
  },

  // -------------------------------------------------------------
  // SCENE 05: The Data is Fragmented
  // -------------------------------------------------------------
  {
    id: 5,
    title: "Data Fragmentation to Canonical Observation",
    duration: 13000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">MULTI-CHANNEL INGESTION</div>
      <h1 class="hero-title metallic-text">THE DATA IS FRAGMENTED.</h1>
      <p class="hero-sub">Airfares are scattered across proprietary airline channels, OTAs, and aggregators.</p>

      <div class="s05-channels-stage" style="margin-top: 2.5rem;">
        
        <!-- Fragmented Raw Feeds -->
        <div style="display: flex; flex-direction: column; gap: 1rem; flex: 1;">
          <div class="glass-panel s05-stream-card" style="border-left: 4px solid var(--blue-electric);">
            <div style="color: var(--cyan-glow); font-weight: 700;">CHANNEL A: AIRLINE DIRECT API</div>
            <div style="color: var(--text-muted);">{"flight": "6E-204", "fare": 6880, "tax": 1120, "baggage": "15kg"}</div>
          </div>
          <div class="glass-panel s05-stream-card" style="border-left: 4px solid var(--saffron-gold);">
            <div style="color: var(--saffron-gold); font-weight: 700;">CHANNEL B: OTA AGGREGATOR FEED</div>
            <div style="color: var(--text-muted);">{"carrier": "AI-805", "total_inr": "7126.00", "seat_left": 3}</div>
          </div>
          <div class="glass-panel s05-stream-card" style="border-left: 4px solid var(--coral-red);">
            <div style="color: var(--coral-red); font-weight: 700;">CHANNEL C: COMMERCIAL GDS ADAPTER</div>
            <div style="color: var(--text-muted);">{"itin": "DEL-BOM", "tariff": 8025, "class": "Y", "stops": 0}</div>
          </div>
        </div>

        <!-- Convergence Arrow -->
        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
          <div class="mono-tag" style="color: var(--cyan-bright); font-weight: 700;">CANONICALIZATION</div>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--cyan-bright)" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </div>

        <!-- Structured Observation -->
        <div class="glass-panel s05-canonical-box">
          <div class="mono-tag" style="color: var(--mint-glow); margin-bottom: 0.75rem;">
            ✓ CANONICAL STRUCTURED OBSERVATION (N=5,332)
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.85rem; color: #ffffff; line-height: 1.8;">
            <div>• <strong>CORRIDOR:</strong> DEL ↔ BOM (DGCA Top 10)</div>
            <div>• <strong>TRAVEL DATE:</strong> 2026-09-27 (Horizon T+15)</div>
            <div>• <strong>WINDOW:</strong> 10:00 - 18:00 IST (Locked Non-stop)</div>
            <div>• <strong>CURRENCY:</strong> INR Normalized (Base + Taxes)</div>
            <div>• <strong>PROVENANCE:</strong> Google Flights Ingestion Adapter</div>
            <div>• <strong>INTEGRITY:</strong> Schema Sealed & Timestamped</div>
          </div>
        </div>

      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1200), 300);
      setTimeout(() => audio.playDataTick(1400), 600);
      setTimeout(() => audio.playLaserSweep(), 1200);
    }
  },

  // -------------------------------------------------------------
  // SCENE 06: Hero Pivot (AeroCPI Reveal)
  // -------------------------------------------------------------
  {
    id: 6,
    title: "From Observation to Measurement (AeroCPI Reveal)",
    duration: 13000,
    render: () => `
      <div style="text-align: center; max-width: 1000px;">
        <div style="font-family: var(--font-display); font-size: clamp(2rem, 3.5vw, 3.2rem); font-weight: 700; color: var(--text-dim); margin-bottom: 1rem;">
          "THE PROBLEM IS NOT FINDING A PRICE."
        </div>
        <div style="font-family: var(--font-display); font-size: clamp(2.5rem, 4.5vw, 4.2rem); font-weight: 800; color: #ffffff; margin-bottom: 2.5rem;">
          "IT IS MEASURING THE MARKET."
        </div>

        <div class="s06-huge-aerocpi">AeroCPI</div>

        <div class="s06-motto" style="justify-content: center; margin-top: 1.5rem;">
          <span style="color: var(--cyan-glow);">MEASURE.</span>
          <span style="color: #ffffff;">EXPLAIN.</span>
          <span style="color: var(--mint-glow);">VERIFY.</span>
        </div>

        <p style="color: var(--text-dim); font-size: 1.25rem; margin-top: 2rem;">
          India's sovereign, high-frequency, scientifically rigorous airfare measurement observatory.
        </p>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.5);
      setTimeout(() => audio.playMetallicImpact(), 500);
      setTimeout(() => audio.playHeroChord(), 800);
    }
  },

  // -------------------------------------------------------------
  // SCENE 07: AeroCPI 4-Stage Architecture
  // -------------------------------------------------------------
  {
    id: 7,
    title: "4-Stage Architecture Journey",
    duration: 14000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">END-TO-END METHODOLOGY PIPELINE</div>
      <h1 class="hero-title metallic-text">THE MEASUREMENT ENGINE</h1>
      <p class="hero-sub">A continuous, four-stage transformation from raw web quotes into sovereign measurement.</p>

      <div class="s07-arch-track" style="margin-top: 3rem;">
        
        <div class="glass-panel s07-node active-stage">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="mono-tag" style="color: var(--cyan-glow);">STAGE 01</div>
            <div style="font-size: 1.2rem;">📡</div>
          </div>
          <div style="font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: #ffffff;">OBSERVE</div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); line-height: 1.6;">
            • 5,332 Raw Quotes<br>
            • 10 DGCA Corridors<br>
            • 5 Horizons (T+1..T+45)<br>
            • Multi-source Adapters
          </div>
        </div>

        <div class="glass-panel s07-node active-stage">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="mono-tag" style="color: var(--saffron-gold);">STAGE 02</div>
            <div style="font-size: 1.2rem;">🛡️</div>
          </div>
          <div style="font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: #ffffff;">VALIDATE</div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); line-height: 1.6;">
            • Tukey 1.5× IQR Outliers<br>
            • Currency Normalization<br>
            • 10:00-18:00 IST Window<br>
            • Total-Only Policy
          </div>
        </div>

        <div class="glass-panel s07-node active-stage">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="mono-tag" style="color: var(--mint-glow);">STAGE 03</div>
            <div style="font-size: 1.2rem;">📐</div>
          </div>
          <div style="font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: #ffffff;">MEASURE</div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); line-height: 1.6;">
            • Jevons Elementary Geometric<br>
            • DGCA Passenger Weights<br>
            • Active Weight Norm (w*)<br>
            • Geometric Aggregation
          </div>
        </div>

        <div class="glass-panel s07-node active-stage">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="mono-tag" style="color: var(--blue-electric);">STAGE 04</div>
            <div style="font-size: 1.2rem;">🔍</div>
          </div>
          <div style="font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: #ffffff;">EXPLAIN</div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim); line-height: 1.6;">
            • 5A Log-Linear Attribution<br>
            • Zero Residual Error<br>
            • 9-Stage Trace Tree<br>
            • SHA-256 Manifest
          </div>
        </div>

      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playDataTick(1000), 400);
      setTimeout(() => audio.playDataTick(1400), 800);
      setTimeout(() => audio.playDataTick(1800), 1200);
      setTimeout(() => audio.playLaserSweep(), 1600);
    }
  },

  // -------------------------------------------------------------
  // SCENE 08: DGCA India Route Network
  // -------------------------------------------------------------
  {
    id: 8,
    title: "DGCA-Informed Route Basket",
    duration: 13000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">SPATIAL COVERAGE & BASKET WEIGHTS</div>
      <h1 class="hero-title metallic-text">DGCA-TRAFFIC-INFORMED BASKET</h1>
      <p class="hero-sub">The top 10 domestic corridors represent over 91.5% of high-density domestic passenger flow.</p>

      <div class="s08-network-grid" style="margin-top: 2rem;">
        
        <!-- Stylized India Route Map SVG -->
        <div class="glass-panel" style="padding: 1.5rem; display: flex; justify-content: center; align-items: center;">
          <svg class="s08-map-svg" viewBox="0 0 500 450">
            <!-- Background Map Grid -->
            <defs>
              <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#38bdf8" />
                <stop offset="100%" stop-color="#10b981" />
              </linearGradient>
            </defs>

            <!-- Airport Nodes -->
            <!-- DEL (220, 120) -->
            <!-- BOM (150, 260) -->
            <!-- BLR (210, 360) -->
            <!-- HYD (225, 280) -->
            <!-- CCU (380, 210) -->
            <!-- MAA (240, 375) -->
            <!-- GOI (160, 310) -->
            <!-- PAT (340, 160) -->

            <!-- Animated Route Arcs -->
            <path d="M 220 120 Q 170 190 150 260" fill="none" stroke="url(#routeGrad)" stroke-width="3" stroke-dasharray="6,6"/>
            <path d="M 210 360 Q 200 240 220 120" fill="none" stroke="url(#routeGrad)" stroke-width="2.5"/>
            <path d="M 210 360 Q 170 310 150 260" fill="none" stroke="url(#routeGrad)" stroke-width="2.5"/>
            <path d="M 220 120 Q 230 200 225 280" fill="none" stroke="url(#routeGrad)" stroke-width="2.5"/>
            <path d="M 220 120 Q 300 160 380 210" fill="none" stroke="url(#routeGrad)" stroke-width="2.5"/>
            <path d="M 240 375 Q 230 250 220 120" fill="none" stroke="url(#routeGrad)" stroke-width="2"/>
            <path d="M 160 310 Q 150 280 150 260" fill="none" stroke="url(#routeGrad)" stroke-width="2"/>
            <path d="M 210 360 Q 220 320 225 280" fill="none" stroke="url(#routeGrad)" stroke-width="2"/>
            <path d="M 220 120 Q 280 140 340 160" fill="none" stroke="url(#routeGrad)" stroke-width="2"/>
            <path d="M 210 360 Q 300 290 380 210" fill="none" stroke="url(#routeGrad)" stroke-width="2"/>

            <!-- Airport Markers -->
            <g transform="translate(220, 120)"><circle r="7" fill="#06b6d4"/><text x="12" y="5" fill="#ffffff" font-family="monospace" font-size="12" font-weight="bold">DEL</text></g>
            <g transform="translate(150, 260)"><circle r="7" fill="#06b6d4"/><text x="-35" y="5" fill="#ffffff" font-family="monospace" font-size="12" font-weight="bold">BOM</text></g>
            <g transform="translate(210, 360)"><circle r="7" fill="#06b6d4"/><text x="-35" y="5" fill="#ffffff" font-family="monospace" font-size="12" font-weight="bold">BLR</text></g>
            <g transform="translate(225, 280)"><circle r="6" fill="#38bdf8"/><text x="10" y="5" fill="#ffffff" font-family="monospace" font-size="11">HYD</text></g>
            <g transform="translate(380, 210)"><circle r="6" fill="#38bdf8"/><text x="10" y="5" fill="#ffffff" font-family="monospace" font-size="11">CCU</text></g>
            <g transform="translate(240, 375)"><circle r="5" fill="#38bdf8"/><text x="10" y="5" fill="#ffffff" font-family="monospace" font-size="11">MAA</text></g>
            <g transform="translate(160, 310)"><circle r="5" fill="#38bdf8"/><text x="-32" y="5" fill="#ffffff" font-family="monospace" font-size="11">GOI</text></g>
            <g transform="translate(340, 160)"><circle r="5" fill="#38bdf8"/><text x="10" y="5" fill="#ffffff" font-family="monospace" font-size="11">PAT</text></g>
          </svg>
        </div>

        <!-- Corridors Ranking Strip -->
        <div class="s08-corridor-list">
          <div class="s08-corridor-row" style="border-left: 3px solid var(--cyan-bright);">
            <span>DEL ↔ BOM</span>
            <span style="color: var(--cyan-glow); font-weight: 700;">17.8% Weight</span>
          </div>
          <div class="s08-corridor-row">
            <span>BLR ↔ DEL</span>
            <span style="color: var(--text-dim);">14.1% Weight</span>
          </div>
          <div class="s08-corridor-row">
            <span>BLR ↔ BOM</span>
            <span style="color: var(--text-dim);">11.6% Weight</span>
          </div>
          <div class="s08-corridor-row">
            <span>DEL ↔ HYD</span>
            <span style="color: var(--mint-glow); font-weight: 700;">10.3% (+1.07 pts)</span>
          </div>
          <div class="s08-corridor-row">
            <span>DEL ↔ CCU</span>
            <span style="color: var(--text-dim);">9.9% Weight</span>
          </div>
          <div class="s08-corridor-row">
            <span>MAA ↔ DEL</span>
            <span style="color: var(--text-dim);">8.2% Weight</span>
          </div>
          <div class="s08-corridor-row">
            <span>GOI ↔ BOM</span>
            <span style="color: var(--coral-red); font-weight: 700;">8.0% (-4.74 pts)</span>
          </div>
          <div class="s08-corridor-row">
            <span>BLR ↔ HYD / PAT / CCU</span>
            <span style="color: var(--text-dim);">20.1% Combined</span>
          </div>
        </div>

      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1100), 400);
      setTimeout(() => audio.playDataTick(1500), 800);
    }
  },

  // -------------------------------------------------------------
  // SCENE 09: Real AeroCPI Product Observatory
  // -------------------------------------------------------------
  {
    id: 9,
    title: "The Real Measurement Observatory",
    duration: 14000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">VERIFIED PRODUCTION RUN</div>
      <h1 class="hero-title metallic-text">THE MEASUREMENT OBSERVATORY</h1>
      <p class="hero-sub">High-density visual interface backed by certified FastAPI endpoints and immutable data runs.</p>

      <div class="s09-screenshot-frame" style="margin-top: 2rem;">
        <img class="s09-screenshot-img" src="./assets/01_overview_main_desktop.png" alt="AeroCPI Overview">
        
        <!-- Live Callout Badges over the UI -->
        <div style="position: absolute; top: 1.5rem; left: 2rem;" class="glass-panel">
          <div style="padding: 0.8rem 1.4rem;">
            <div class="mono-tag" style="color: var(--saffron-gold);">HEADLINE INDEX (T+15)</div>
            <div style="font-family: var(--font-display); font-size: 2.4rem; font-weight: 800; color: #ffffff;">96.21</div>
            <div style="color: var(--coral-red); font-family: var(--font-mono); font-size: 0.85rem; font-weight: 700;">-3.791 pts vs Baseline 100.00</div>
          </div>
        </div>

        <div style="position: absolute; bottom: 1.5rem; right: 2rem;" class="glass-panel">
          <div style="padding: 0.8rem 1.4rem; font-family: var(--font-mono); font-size: 0.85rem;">
            <div style="color: var(--cyan-glow);">RUN ID: e1c05338-bc7a-4e2f</div>
            <div style="color: var(--text-dim);">POPULATION: N = 5,332 Obs</div>
            <div style="color: var(--mint-glow);">COVERAGE: 100% (10/10 Routes)</div>
          </div>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.2);
      setTimeout(() => audio.playMetallicImpact(), 600);
      setTimeout(() => audio.playDataTick(1600), 1200);
    }
  },

  // -------------------------------------------------------------
  // SCENE 10: Explainability / Route Contributions
  // -------------------------------------------------------------
  {
    id: 10,
    title: "Route Attribution & Explainability",
    duration: 14000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">EXACT LOG-LINEAR ATTRIBUTION</div>
      <h1 class="hero-title metallic-text">WHERE DID THE MOVEMENT COME FROM?</h1>
      <p class="hero-sub">AeroCPI provides mathematically exact decomposition of index movement into route contributions.</p>

      <div class="s10-contrib-chart" style="margin-top: 2.5rem;">
        
        <!-- Row 1: DEL-HYD (+1.0675) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">DEL ↔ HYD</div>
          <div class="s10-bar-left"></div>
          <div class="s10-bar-right">
            <div class="s10-bar-fill pos" style="width: 140px;"></div>
          </div>
          <div style="color: var(--mint-glow); font-weight: 700; text-align: right;">+1.0675</div>
        </div>

        <!-- Row 2: BLR-CCU (+0.3269) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">BLR ↔ CCU</div>
          <div class="s10-bar-left"></div>
          <div class="s10-bar-right">
            <div class="s10-bar-fill pos" style="width: 45px;"></div>
          </div>
          <div style="color: var(--mint-glow); font-weight: 700; text-align: right;">+0.3269</div>
        </div>

        <!-- Row 3: BLR-HYD (+0.2805) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">BLR ↔ HYD</div>
          <div class="s10-bar-left"></div>
          <div class="s10-bar-right">
            <div class="s10-bar-fill pos" style="width: 38px;"></div>
          </div>
          <div style="color: var(--mint-glow); font-weight: 700; text-align: right;">+0.2805</div>
        </div>

        <!-- Row 4: MAA-DEL (-0.2993) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">MAA ↔ DEL</div>
          <div class="s10-bar-left">
            <div class="s10-bar-fill neg" style="width: 40px;"></div>
          </div>
          <div class="s10-bar-right"></div>
          <div style="color: var(--coral-red); font-weight: 700; text-align: right;">-0.2993</div>
        </div>

        <!-- Row 5: BLR-DEL (-0.7875) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">BLR ↔ DEL</div>
          <div class="s10-bar-left">
            <div class="s10-bar-fill neg" style="width: 105px;"></div>
          </div>
          <div class="s10-bar-right"></div>
          <div style="color: var(--coral-red); font-weight: 700; text-align: right;">-0.7875</div>
        </div>

        <!-- Row 6: GOI-BOM (-4.7391) -->
        <div class="s10-bar-row">
          <div style="font-weight: 700; color: #ffffff;">GOI ↔ BOM</div>
          <div class="s10-bar-left">
            <div class="s10-bar-fill neg" style="width: 260px;"></div>
          </div>
          <div class="s10-bar-right"></div>
          <div style="color: var(--coral-red); font-weight: 700; text-align: right;">-4.7391</div>
        </div>

      </div>

      <div class="glass-pill" style="margin-top: 2rem; border-color: rgba(56,189,248,0.5);">
        Σ ROUTE CONTRIBUTIONS = -3.791 pts = HEADLINE INDEX CHANGE (96.209 - 100.000) · ZERO RESIDUAL
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1200), 300);
      setTimeout(() => audio.playDataTick(1600), 700);
    }
  },

  // -------------------------------------------------------------
  // SCENE 11: Trust, Audit & Trace Lineage
  // -------------------------------------------------------------
  {
    id: 11,
    title: "Trust, Audit & Trace Lineage",
    duration: 13000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">CRYPTOGRAPHIC LINEAGE & AUDITABILITY</div>
      <h1 class="hero-title metallic-text">MEASUREMENT ASSURANCE</h1>
      <p class="hero-sub">"Trust does not change the index. Trust explains the health of the measurement."</p>

      <div class="s11-trace-pipeline" style="margin-top: 3rem;">
        
        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">RUN</div>
          <div style="font-weight: 700; color: #ffffff;">e1c05338</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">CONFIG</div>
          <div style="font-weight: 700; color: #ffffff;">2026.1.0</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">HORIZONS</div>
          <div style="font-weight: 700; color: #ffffff;">5 Windows</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">CORRIDORS</div>
          <div style="font-weight: 700; color: #ffffff;">10 DGCA</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">FARES</div>
          <div style="font-weight: 700; color: #ffffff;">Representative</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node">
          <div class="mono-tag" style="color: var(--cyan-glow);">EVIDENCE</div>
          <div style="font-weight: 700; color: #ffffff;">5,332 Obs</div>
        </div>

        <div style="display: flex; align-items: center; color: var(--text-muted);">➔</div>

        <div class="glass-panel s11-trace-node" style="border-color: var(--mint-glow);">
          <div class="mono-tag" style="color: var(--mint-glow);">SHA-256 HASH</div>
          <div style="font-weight: 700; color: var(--mint-glow);">cacd4054...</div>
        </div>

      </div>

      <div class="glass-panel" style="padding: 1.5rem 3rem; margin-top: 2.5rem; text-align: center;">
        <div class="mono-tag" style="color: var(--mint-glow); margin-bottom: 0.5rem;">STATUTORY PROVENANCE SEAL</div>
        <div style="font-family: var(--font-mono); font-size: 0.95rem; color: #ffffff;">
          Immutable Calculation Hash: <code>cacd4054e1c05338bc7a4e2f8b81f855ca54c3be928a6f4e22301f7823901b0</code>
        </div>
      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.1);
      setTimeout(() => audio.playDataTick(1200), 400);
      setTimeout(() => audio.playLaserSweep(), 900);
    }
  },

  // -------------------------------------------------------------
  // SCENE 12: Final Result & Seal
  // -------------------------------------------------------------
  {
    id: 12,
    title: "Final Headline Result (96.21)",
    duration: 13000,
    render: () => `
      <div style="text-align: center;">
        <div class="glass-pill" style="margin-bottom: 1.5rem;">FROZEN PRODUCTION RESULT</div>
        
        <div class="s12-headline-result">96.21</div>
        
        <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem;">
          AeroCPI Headline · Horizon T+15
        </div>

        <div style="display: flex; gap: 1.5rem; justify-content: center; margin-top: 2rem;">
          <div class="glass-pill">10 / 10 ACTIVE ROUTES</div>
          <div class="glass-pill">ACTIVE WEIGHT 1.000</div>
          <div class="glass-pill">MATCHED COVERAGE 100%</div>
        </div>

        <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 2.5rem; font-family: var(--font-mono); font-size: 1.5rem; font-weight: 800;">
          <span style="color: var(--cyan-glow);">MEASURE.</span>
          <span style="color: #ffffff;">EXPLAIN.</span>
          <span style="color: var(--mint-glow);">VERIFY.</span>
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
  // SCENE 13: Research Literature & Validation
  // -------------------------------------------------------------
  {
    id: 13,
    title: "Scientific Literature & Governance",
    duration: 12000,
    render: () => `
      <div class="glass-pill" style="margin-bottom: 1rem;">SCIENTIFIC FOUNDATIONS</div>
      <h1 class="hero-title metallic-text">METHODOLOGICAL RIGOR</h1>
      <p class="hero-sub">Grounded in established international price index literature and empirical aviation economics.</p>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; width: 100%; max-width: 1200px; margin-top: 2.5rem;">
        
        <div class="glass-panel" style="padding: 2rem; display: flex; flex-direction: column; gap: 1rem;">
          <div class="mono-tag" style="color: var(--saffron-gold);">01. MoSPI CPI CONTEXT & LIMITS</div>
          <div style="font-weight: 700; font-size: 1.2rem; color: #ffffff;">Augmentation, Not Replacement</div>
          <div style="color: var(--text-dim); font-size: 0.95rem; line-height: 1.6;">
            AeroCPI is an independent high-frequency airfare observatory. It clarifies statutory boundaries and does not claim official MoSPI statistical equivalence.
          </div>
        </div>

        <div class="glass-panel" style="padding: 2rem; display: flex; flex-direction: column; gap: 1rem;">
          <div class="mono-tag" style="color: var(--cyan-glow);">02. JEVONS GEOMETRIC FORMULATION</div>
          <div style="font-weight: 700; font-size: 1.2rem; color: #ffffff;">Axiomatic Elementary Indices</div>
          <div style="color: var(--text-dim); font-size: 0.95rem; line-height: 1.6;">
            Satisfies Time Reversal, Proportionality, Commensurability, and Monotonicity invariants across all 50 corridor-horizon cells.
          </div>
        </div>

      </div>
    `,
    onEnter: (audio) => {
      audio.playWhoosh(1.0);
      setTimeout(() => audio.playDataTick(1200), 400);
    }
  },

  // -------------------------------------------------------------
  // SCENE 14: Thank You & Grand Curtain
  // -------------------------------------------------------------
  {
    id: 14,
    title: "Thank You & Pitch Closing",
    duration: 20000,
    render: () => `
      <div style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <div class="s14-emblem">✈</div>
        
        <h1 class="hero-title metallic-text" style="font-size: clamp(3.5rem, 8vw, 7rem);">THANK YOU</h1>
        
        <div style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--cyan-glow); margin-top: 1rem;">
          TEAM BUZZCODEX
        </div>

        <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--saffron-gold); margin-top: 0.5rem; letter-spacing: 0.1em;">
          SMART INDIA HACKATHON 2026 · PROBLEM SIH26056
        </div>

        <div style="margin-top: 2rem; padding: 0.6rem 1.8rem; border-radius: 9999px; background: rgba(15,23,42,0.8); border: 1px solid rgba(56,189,248,0.4); font-family: var(--font-mono); font-size: 0.9rem; letter-spacing: 0.25em; color: #ffffff;">
          MEASURE · EXPLAIN · VERIFY
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

window.SCENES_DATA = SCENES_DATA;
