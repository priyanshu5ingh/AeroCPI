/**
 * AeroCPI Cinematic Pitch — Master Application Controller
 * Handles scene lifecycle, Canvas particle background, keyboard shortcuts, and HUD telemetry.
 */

class CinematicPitchApp {
  constructor() {
    this.scenes = window.SCENES_DATA || [];
    this.currentIndex = 0;
    this.isPlaying = true;
    this.isMuted = false;
    this.timer = null;
    this.sceneStartTime = 0;
    this.sceneDuration = 0;
    this.rafId = null;

    // DOM Elements
    this.viewport = document.getElementById('app-viewport');
    this.scenesContainer = document.getElementById('scenes-container');
    this.canvas = document.getElementById('fx-canvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.hudSceneCounter = document.getElementById('hud-scene-counter');
    this.hudSceneTitle = document.getElementById('hud-scene-title');
    this.progressBar = document.getElementById('timeline-progress-bar');
    this.timerSubbar = document.getElementById('scene-timer-subbar');
    this.btnPlayPause = document.getElementById('btn-play-pause');
    this.btnMute = document.getElementById('btn-mute');
    this.btnFullscreen = document.getElementById('btn-fullscreen');
    this.sceneDrawer = document.getElementById('scene-drawer');
    this.preloader = document.getElementById('preloader');
    this.btnStart = document.getElementById('btn-start-film');

    // Particle Background State
    this.particles = [];
    this.streamlines = [];
    this.gridOffset = 0;

    this.init();
  }

  init() {
    this.buildSceneContainers();
    this.buildDrawerItems();
    this.initCanvas();
    this.initEventListeners();
    this.startParticleLoop();
  }

  buildSceneContainers() {
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

  buildDrawerItems() {
    if (!this.sceneDrawer) return;
    this.sceneDrawer.innerHTML = '';

    this.scenes.forEach((scene, idx) => {
      const item = document.createElement('div');
      item.className = `drawer-scene-item ${idx === 0 ? 'active' : ''}`;
      item.textContent = (idx + 1 < 10 ? '0' : '') + (idx + 1);
      item.title = `Scene ${idx + 1}: ${scene.title}`;
      item.addEventListener('click', () => {
        this.goToScene(idx);
      });
      this.sceneDrawer.appendChild(item);
    });
  }

  initCanvas() {
    if (!this.canvas) return;
    const resize = () => {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);
    resize();

    // Create background floating stars / telemetry data points
    const count = 120;
    this.particles = [];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: Math.random() * 2 + 0.5,
        speedX: (Math.random() - 0.5) * 0.2,
        speedY: (Math.random() - 0.5) * 0.2,
        alpha: Math.random() * 0.5 + 0.1
      });
    }

    // Aerodynamic streamlines
    this.streamlines = [];
    for (let i = 0; i < 6; i++) {
      this.streamlines.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        len: Math.random() * 300 + 150,
        speed: Math.random() * 2 + 1.5,
        alpha: Math.random() * 0.25 + 0.05
      });
    }
  }

  startParticleLoop() {
    const render = () => {
      if (this.ctx && this.canvas) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 1. Draw subtle 3D coordinate grid lines
        this.gridOffset = (this.gridOffset + 0.2) % 60;
        this.ctx.strokeStyle = 'rgba(6, 182, 212, 0.035)';
        this.ctx.lineWidth = 1;
        
        for (let x = -this.gridOffset; x < this.canvas.width; x += 60) {
          this.ctx.beginPath();
          this.ctx.moveTo(x, 0);
          this.ctx.lineTo(x, this.canvas.height);
          this.ctx.stroke();
        }

        // 2. Draw Floating Telemetry Particles
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

        // 3. Draw Aerodynamic Streamlines
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
    const prevIndex = this.currentIndex;
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
    if (this.hudSceneTitle) this.hudSceneTitle.textContent = this.scenes[this.currentIndex].title;

    // Update Global Progress Bar
    const globalPct = ((this.currentIndex + 1) / this.scenes.length) * 100;
    if (this.progressBar) this.progressBar.style.width = `${globalPct}%`;

    // Reset Scene Timer
    this.sceneStartTime = performance.now();
    this.sceneDuration = this.scenes[this.currentIndex].duration || 12000;
    if (this.timerSubbar) this.timerSubbar.style.width = '0%';

    // Trigger Scene onEnter Lifecycle with Audio
    if (this.scenes[this.currentIndex].onEnter && window.cinematicAudio) {
      this.scenes[this.currentIndex].onEnter(window.cinematicAudio);
    }
  }

  nextScene() {
    if (this.currentIndex < this.scenes.length - 1) {
      this.goToScene(this.currentIndex + 1);
    } else {
      // Loop or stop
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

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Space: Play/Pause
      if (e.code === 'Space') {
        e.preventDefault();
        this.togglePlayPause();
      }
      // Right Arrow / Page Down / Key L
      else if (e.code === 'ArrowRight' || e.code === 'PageDown' || e.code === 'KeyL') {
        e.preventDefault();
        this.nextScene();
      }
      // Left Arrow / Page Up / Key H
      else if (e.code === 'ArrowLeft' || e.code === 'PageUp' || e.code === 'KeyH') {
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
      // Tab: Toggle Drawer
      else if (e.code === 'Tab') {
        e.preventDefault();
        if (this.sceneDrawer) this.sceneDrawer.classList.toggle('visible');
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
