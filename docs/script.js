// Scroll-reveal
const observer = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.16 }
);

document.querySelectorAll('.reveal').forEach(section => observer.observe(section));

// Simple scrollspy for nav
const sections = document.querySelectorAll('main section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

function onScroll() {
  const scrollPos = window.scrollY + 120;
  let currentId = null;

  sections.forEach(sec => {
    if (scrollPos >= sec.offsetTop && scrollPos < sec.offsetTop + sec.offsetHeight) {
      currentId = sec.id;
    }
  });

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && href.startsWith('#')) {
      link.classList.toggle('active', href === `#${currentId}`);
    }
  });
}

window.addEventListener('scroll', onScroll);

// Parallax hero blob
const blob = document.querySelector('.hero-blob');
window.addEventListener('mousemove', e => {
  const x = (e.clientX / window.innerWidth - 0.5) * 20;
  const y = (e.clientY / window.innerHeight - 0.5) * 20;
  blob.style.transform = `translate3d(${x}px, ${y}px, 0)`;
});

// "How it works" interactive steps
const flowSteps = document.querySelectorAll('.flow-step');
const flowPanels = document.querySelectorAll('[data-step-panel]');

flowSteps.forEach(step => {
  step.addEventListener('click', () => {
    const stepId = step.getAttribute('data-step');

    flowSteps.forEach(s => s.classList.toggle('active', s === step));

    flowPanels.forEach(panel => {
      const panelId = panel.getAttribute('data-step-panel');
      panel.classList.toggle('hidden', panelId !== stepId);
    });
  });
});

// Tabbed JSON preview
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('[data-tab-panel]');

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.getAttribute('data-tab');

    tabButtons.forEach(b => b.classList.toggle('active', b === btn));
    tabPanels.forEach(panel => {
      const panelTab = panel.getAttribute('data-tab-panel');
      panel.classList.toggle('hidden', panelTab !== tab);
    });
  });
});
