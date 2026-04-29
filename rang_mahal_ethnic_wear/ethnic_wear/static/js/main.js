/* ═══════════════════════════════════════════════
   Rang Mahal — Main JavaScript
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll effect ──
  const navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 20);
    });
  }

  // ── Mobile nav toggle ──
  const navToggle = document.getElementById('navToggle');
  const navLinks  = document.getElementById('navLinks');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      // Animate hamburger lines
      const spans = navToggle.querySelectorAll('span');
      if (navLinks.classList.contains('open')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity   = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity   = '';
        spans[2].style.transform = '';
      }
    });
    // Close nav when clicking outside
    document.addEventListener('click', (e) => {
      if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });
  }

  // ── Search dropdown toggle ──
  const searchToggle   = document.getElementById('searchToggle');
  const searchDropdown = document.getElementById('searchDropdown');
  if (searchToggle && searchDropdown) {
    searchToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      searchDropdown.classList.toggle('open');
      if (searchDropdown.classList.contains('open')) {
        setTimeout(() => searchDropdown.querySelector('input')?.focus(), 50);
      }
    });
    document.addEventListener('click', (e) => {
      if (!searchDropdown.contains(e.target) && e.target !== searchToggle) {
        searchDropdown.classList.remove('open');
      }
    });
  }

  // ── Auto-dismiss flash messages ──
  const flashContainer = document.getElementById('flashContainer');
  if (flashContainer) {
    setTimeout(() => {
      flashContainer.querySelectorAll('.flash').forEach(f => {
        f.style.animation = 'slideOut .3s ease forwards';
        setTimeout(() => f.remove(), 300);
      });
    }, 4000);
  }

  // ── Product card image hover swap (if data-hover attr set) ──
  document.querySelectorAll('.product-card').forEach(card => {
    const img = card.querySelector('.product-img');
    const secondaryImg = img?.dataset.hover;
    if (img && secondaryImg) {
      const original = img.src;
      card.addEventListener('mouseenter', () => img.src = secondaryImg);
      card.addEventListener('mouseleave', () => img.src = original);
    }
  });

  // ── Scroll-triggered animations ──
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'fadeInUp .5s ease both';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.product-card, .trust-item, .cat-card').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });

  // ── Add to cart feedback ──
  document.querySelectorAll('.quick-add-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.disabled) {
        btn.innerHTML = '<i class="fas fa-check"></i> Added!';
        btn.style.background = 'var(--rose)';
        btn.style.color = 'white';
      }
    });
  });

  // ── Lazy load images ──
  if ('IntersectionObserver' in window) {
    const imgObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            imgObserver.unobserve(img);
          }
        }
      });
    });
    document.querySelectorAll('img[data-src]').forEach(img => imgObserver.observe(img));
  }

  // ── Smooth scroll for anchor links ──
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Star hover effect in product detail reviews ──
  const starSelect = document.getElementById('starSelect');
  if (starSelect) {
    const stars = starSelect.querySelectorAll('.star-pick');
    stars.forEach((star, index) => {
      star.addEventListener('mouseover', () => {
        stars.forEach((s, i) => s.style.color = i <= index ? '#f59e0b' : '#d1d5db');
      });
      star.addEventListener('mouseleave', () => {
        const rating = parseInt(document.getElementById('ratingInput')?.value || 5);
        stars.forEach((s, i) => s.style.color = i < rating ? '#f59e0b' : '#d1d5db');
      });
    });
  }

});

// ── CSS animation for flash removal ──
const style = document.createElement('style');
style.textContent = `@keyframes slideOut { to { transform: translateX(110%); opacity: 0; } }`;
document.head.appendChild(style);
