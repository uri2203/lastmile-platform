/**
 * Neural Constellation Background
 * 
 * Particles floating and connecting with lines when close.
 * Reacts to mouse movement. Dark/light theme aware.
 * Zero dependencies — pure vanilla JS Canvas.
 * 
 * Usage:
 *   <script src="js/neural-bg.js"></script>
 *   <canvas id="neural-canvas"></canvas>
 */
(function() {
  'use strict';

  const canvas = document.getElementById('neural-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // ── Config ──────────────────────────────────────────────
  const CONFIG = {
    particleCount: 80,        // number of particles
    maxDistance: 150,          // max distance to draw connections
    particleRadius: 2,        // base radius
    speed: 0.3,               // drift speed
    mouseRadius: 200,         // mouse influence radius
    mouseForce: 0.05,         // how strongly mouse pushes particles
    lineWidth: 0.5,           // connection line width
    colors: {
      dark:  { particle: 'rgba(99, 102, 241, 0.6)', line: 'rgba(99, 102, 241, 0.15)', glow: 'rgba(99, 102, 241, 0.3)' },
      light: { particle: 'rgba(79, 70, 229, 0.5)',  line: 'rgba(79, 70, 229, 0.12)',  glow: 'rgba(79, 70, 229, 0.25)' }
    }
  };

  let particles = [];
  let mouse = { x: -9999, y: -9999 };
  let width, height;
  let animId;
  let currentTheme = 'dark';

  // ── Particle class ──────────────────────────────────────
  class Particle {
    constructor() {
      this.reset();
    }
    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * CONFIG.speed;
      this.vy = (Math.random() - 0.5) * CONFIG.speed;
      this.radius = CONFIG.particleRadius + Math.random() * 1.5;
      this.pulsePhase = Math.random() * Math.PI * 2;
      this.pulseSpeed = 0.01 + Math.random() * 0.02;
    }
    update() {
      // Drift
      this.x += this.vx;
      this.y += this.vy;
      this.pulsePhase += this.pulseSpeed;

      // Mouse repulsion
      const dx = this.x - mouse.x;
      const dy = this.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < CONFIG.mouseRadius && dist > 0) {
        const force = (1 - dist / CONFIG.mouseRadius) * CONFIG.mouseForce;
        this.vx += (dx / dist) * force;
        this.vy += (dy / dist) * force;
      }

      // Damping
      this.vx *= 0.99;
      this.vy *= 0.99;

      // Wrap around edges
      if (this.x < -10) this.x = width + 10;
      if (this.x > width + 10) this.x = -10;
      if (this.y < -10) this.y = height + 10;
      if (this.y > height + 10) this.y = -10;
    }
    draw() {
      const pulse = 1 + Math.sin(this.pulsePhase) * 0.3;
      const r = this.radius * pulse;
      const c = CONFIG.colors[currentTheme];

      // Glow
      ctx.beginPath();
      ctx.arc(this.x, this.y, r * 3, 0, Math.PI * 2);
      ctx.fillStyle = c.glow;
      ctx.fill();

      // Core
      ctx.beginPath();
      ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
      ctx.fillStyle = c.particle;
      ctx.fill();
    }
  }

  // ── Resize ──────────────────────────────────────────────
  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }

  // ── Draw connections ────────────────────────────────────
  function drawConnections() {
    const c = CONFIG.colors[currentTheme];
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONFIG.maxDistance) {
          const alpha = 1 - (dist / CONFIG.maxDistance);
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = c.line.replace(/[\d.]+\)$/, (alpha * 0.3).toFixed(2) + ')');
          ctx.lineWidth = CONFIG.lineWidth;
          ctx.stroke();
        }
      }
    }
  }

  // ── Animation loop ──────────────────────────────────────
  function animate() {
    ctx.clearRect(0, 0, width, height);
    drawConnections();
    for (const p of particles) {
      p.update();
      p.draw();
    }
    animId = requestAnimationFrame(animate);
  }

  // ── Theme detection ─────────────────────────────────────
  function detectTheme() {
    const html = document.documentElement;
    if (html.classList.contains('theme-light')) {
      currentTheme = 'light';
    } else {
      currentTheme = 'dark';
    }
  }

  // ── Init ────────────────────────────────────────────────
  function init() {
    resize();
    detectTheme();
    particles = [];
    for (let i = 0; i < CONFIG.particleCount; i++) {
      particles.push(new Particle());
    }
    animate();
  }

  // ── Events ──────────────────────────────────────────────
  window.addEventListener('resize', () => {
    resize();
  });

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener('mouseleave', () => {
    mouse.x = -9999;
    mouse.y = -9999;
  });

  // Watch for theme changes
  const observer = new MutationObserver(() => {
    detectTheme();
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

  // ── Start ───────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
