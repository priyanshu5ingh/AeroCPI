/**
 * AeroCPI + AeroGuide — Cinematic Pitch Film Application Controller
 * Team: BuzzCodeX | Problem Statement: SIH26056 | Theme: Smart Automation
 */

class CinematicPitchApp {
  constructor() {
    this.scenes = window.SCENES_DATA || [];
    this.currentIndex = 0;
    this.isPlaying = true;
    this.isMuted = false;
    this.sceneStartTime = performance.now();
    this.sceneDuration = 12000;
    this.rafId = null;

    // DOM Elements
    this.viewport = document.getElementById('app-viewport');
    this.scenesContainer = document.getElementById('scenes-container');
    this.hudSceneCounter = document.getElementById('hud-scene-counter');
    this.hudSceneTitle = document.getElementById('hud-scene-title');
    this.progressBar = document.getElementById('timeline-progress-bar');
    this.timerSubbar = document.getElementById('scene-timer-subbar');
    this.btnPlayPause = document.getElementById('btn-play-pause');
    this.btnMute = document.getElementById('btn-mute');
    this.btnFullscreen = document.getElementById('btn-fullscreen');
    this.btnDownloadPptx = document.getElementById('btn-download-pptx');
    this.btnPrev = document.getElementById('btn-prev');
    this.btnNext = document.getElementById('btn-next');
    this.sceneDrawer = document.getElementById('scene-drawer');
    this.preloader = document.getElementById('preloader');
    this.btnStart = document.getElementById('btn-start-film');

    // Canvas FX
    this.canvas = document.getElementById('fx-canvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.particles = [];
    this.streamlines = [];
    this.gridOffset = 0;

    this.init();
  }

  init() {
    this.setupCanvas();
    this.buildScenes();
    this.buildDrawer();
    this.initParticles();
    this.startParticleLoop();
    this.initEventListeners();
  }

  setupCanvas() {
    if (!this.canvas) return;
    const resize = () => {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);
  }

  buildScenes() {
    if (!this.scenesContainer) return;
    this.scenesContainer.innerHTML = '';

    this.scenes.forEach((scene, idx) => {
      const sceneEl = document.createElement('div');
      sceneEl.className = `scene ${idx === 0 ? 'active' : ''}`;
      sceneEl.id = `scene-${idx + 1}`;
      sceneEl.innerHTML = scene.render();
      this.scenesContainer.appendChild(sceneEl);
    });
  }

  buildDrawer() {
    if (!this.sceneDrawer) return;
    this.sceneDrawer.innerHTML = '';

    this.scenes.forEach((scene, idx) => {
      const item = document.createElement('div');
      item.className = `drawer-scene-item ${idx === 0 ? 'active' : ''}`;
      item.textContent = idx + 1;
      item.title = `Scene ${idx + 1}: ${scene.title}`;
      item.addEventListener('click', () => this.goToScene(idx));
      this.sceneDrawer.appendChild(item);
    });
  }


  initParticles() {
    this.particles = [];
    for (let i = 0; i < 45; i++) {
      this.particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: Math.random() * 2 + 0.5,
        speedX: (Math.random() - 0.5) * 0.25,
        speedY: (Math.random() - 0.5) * 0.25,
        alpha: Math.random() * 0.5 + 0.15
      });
    }

    this.streamlines = [];
    for (let i = 0; i < 6; i++) {
      this.streamlines.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        len: Math.random() * 300 + 150,
        speed: Math.random() * 2.5 + 1.5,
        alpha: Math.random() * 0.25 + 0.08
      });
    }
  }

  startParticleLoop() {
    const render = () => {
      if (this.ctx && this.canvas) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 1. Coordinate grid lines
        this.gridOffset = (this.gridOffset + 0.2) % 60;
        this.ctx.strokeStyle = 'rgba(6, 182, 212, 0.04)';
        this.ctx.lineWidth = 1;
        
        for (let x = -this.gridOffset; x < this.canvas.width; x += 60) {
          this.ctx.beginPath();
          this.ctx.moveTo(x, 0);
          this.ctx.lineTo(x, this.canvas.height);
          this.ctx.stroke();
        }

        // 2. Telemetry Particles
        this.particles.forEach(p => {
          p.x += p.speedX;
          p.y += p.speedY;
          if (p.x < 0) p.x = this.canvas.width;
          if (p.x > this.canvas.width) p.x = 0;
          if (p.y < 0) p.y = this.canvas.height;
          if (p.y > this.canvas.height) p.y = 0;

          this.ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha})`;
          this.ctx.beginPath();
          this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          this.ctx.fill();
        });

        // 3. Aerodynamic Streamlines
        this.streamlines.forEach(s => {
          s.x += s.speed;
          if (s.x > this.canvas.width + s.len) {
            s.x = -s.len;
            s.y = Math.random() * this.canvas.height;
          }

          const grad = this.ctx.createLinearGradient(s.x, s.y, s.x + s.len, s.y);
          grad.addColorStop(0, 'transparent');
          grad.addColorStop(0.5, `rgba(6, 182, 212, ${s.alpha})`);
          grad.addColorStop(1, 'transparent');

          this.ctx.strokeStyle = grad;
          this.ctx.lineWidth = 1.5;
          this.ctx.beginPath();
          this.ctx.moveTo(s.x, s.y);
          this.ctx.lineTo(s.x + s.len, s.y);
          this.ctx.stroke();
        });
      }

      // Update timer progress bar if playing
      if (this.isPlaying && this.sceneDuration > 0) {
        const elapsed = performance.now() - this.sceneStartTime;
        const pct = Math.min(100, (elapsed / this.sceneDuration) * 100);
        if (this.timerSubbar) {
          this.timerSubbar.style.width = `${pct}%`;
        }

        if (elapsed >= this.sceneDuration) {
          this.nextScene();
        }
      }

      this.rafId = requestAnimationFrame(render);
    };

    render();
  }

  goToScene(index) {
    if (index < 0 || index >= this.scenes.length) return;

    const allSceneEls = document.querySelectorAll('.scene');
    this.currentIndex = index;

    allSceneEls.forEach((el, idx) => {
      el.classList.remove('active', 'prev');
      if (idx === this.currentIndex) {
        el.classList.add('active');
      } else if (idx < this.currentIndex) {
        el.classList.add('prev');
      }
    });

    // Update Drawer Active Item
    const drawerItems = document.querySelectorAll('.drawer-scene-item');
    drawerItems.forEach((item, idx) => {
      item.classList.toggle('active', idx === this.currentIndex);
    });

    // Update Top HUD
    const curNum = (this.currentIndex + 1 < 10 ? '0' : '') + (this.currentIndex + 1);
    const totalNum = (this.scenes.length < 10 ? '0' : '') + this.scenes.length;
    if (this.hudSceneCounter) this.hudSceneCounter.textContent = `${curNum} / ${totalNum}`;
    if (this.hudSceneTitle && this.scenes[this.currentIndex]) {
      this.hudSceneTitle.textContent = this.scenes[this.currentIndex].title;
    }

    // Update Global Progress Bar
    const globalPct = ((this.currentIndex + 1) / this.scenes.length) * 100;
    if (this.progressBar) this.progressBar.style.width = `${globalPct}%`;

    // Reset Scene Timer
    this.sceneStartTime = performance.now();
    this.sceneDuration = this.scenes[this.currentIndex].duration || 12000;
    if (this.timerSubbar) this.timerSubbar.style.width = '0%';

    // Trigger Scene onEnter Lifecycle with Audio
    if (this.scenes[this.currentIndex] && this.scenes[this.currentIndex].onEnter && window.cinematicAudio) {
      this.scenes[this.currentIndex].onEnter(window.cinematicAudio);
    }
  }

  nextScene() {
    if (this.currentIndex < this.scenes.length - 1) {
      this.goToScene(this.currentIndex + 1);
    } else {
      this.goToScene(0);
    }
  }

  prevScene() {
    if (this.currentIndex > 0) {
      this.goToScene(this.currentIndex - 1);
    }
  }

  togglePlayPause() {
    this.isPlaying = !this.isPlaying;
    if (this.btnPlayPause) {
      this.btnPlayPause.textContent = this.isPlaying ? '❚❚ Pause' : '▶ Play';
    }
    if (this.isPlaying) {
      this.sceneStartTime = performance.now();
    }
  }

  toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => {
        console.warn("Fullscreen request error:", err);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  toggleMute() {
    if (window.cinematicAudio) {
      this.isMuted = window.cinematicAudio.toggleMute();
      if (this.btnMute) {
        this.btnMute.textContent = this.isMuted ? '🔇 Unmute' : '🔊 Sound ON';
      }
    }
  }

  initEventListeners() {
    // Start presentation button on preloader
    if (this.btnStart) {
      this.btnStart.addEventListener('click', () => {
        if (window.cinematicAudio) {
          window.cinematicAudio.init();
          window.cinematicAudio.resume();
        }
        if (this.preloader) {
          this.preloader.classList.add('hidden');
        }
        this.goToScene(0);
      });
    }

    // Top HUD controls
    if (this.btnPlayPause) {
      this.btnPlayPause.addEventListener('click', () => this.togglePlayPause());
    }
    if (this.btnMute) {
      this.btnMute.addEventListener('click', () => this.toggleMute());
    }
    if (this.btnFullscreen) {
      this.btnFullscreen.addEventListener('click', () => this.toggleFullscreen());
    }
    if (this.btnDownloadPptx) {
      this.btnDownloadPptx.addEventListener('click', () => {
        window.open('/AeroCPI_SIH2026_Pitch_Deck.pptx', '_blank');
      });
    }

    // Footer buttons
    if (this.btnPrev) {
      this.btnPrev.addEventListener('click', () => this.prevScene());
    }
    if (this.btnNext) {
      this.btnNext.addEventListener('click', () => this.nextScene());
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Space: Play/Pause
      if (e.code === 'Space') {
        e.preventDefault();
        this.togglePlayPause();
      }
      // Right Arrow / Page Down
      else if (e.code === 'ArrowRight' || e.code === 'PageDown') {
        e.preventDefault();
        this.nextScene();
      }
      // Left Arrow / Page Up
      else if (e.code === 'ArrowLeft' || e.code === 'PageUp') {
        e.preventDefault();
        this.prevScene();
      }
      // R: Restart
      else if (e.code === 'KeyR') {
        e.preventDefault();
        this.goToScene(0);
      }
      // F: Fullscreen
      else if (e.code === 'KeyF') {
        e.preventDefault();
        this.toggleFullscreen();
      }
      // M: Mute
      else if (e.code === 'KeyM') {
        e.preventDefault();
        this.toggleMute();
      }
      // P: Download PPTX
      else if (e.code === 'KeyP') {
        e.preventDefault();
        window.open('/AeroCPI_SIH2026_Pitch_Deck.pptx', '_blank');
      }
      // Number keys 1-9 & 0
      else if (e.key >= '1' && e.key <= '9') {
        const sceneNum = parseInt(e.key, 10);
        if (sceneNum <= this.scenes.length) {
          this.goToScene(sceneNum - 1);
        }
      } else if (e.key === '0') {
        if (this.scenes.length >= 10) {
          this.goToScene(9);
        }
      }
    });
  }
}

// Instantiate on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.pitchApp = new CinematicPitchApp();
});
