// ============================================
// main.js - SkyBook Global JavaScript
// ============================================
// Concept: JavaScript browser mein chalta hai
// Flask/Python server pe chalta hai, JS client pe
// Yahan hum:
// 1. Navbar toggle (mobile)
// 2. User dropdown menu
// 3. Flash messages auto-close
// 4. Smooth animations
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // ============================================
    // NAVBAR MOBILE TOGGLE
    // ============================================
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('open');
            // Hamburger animation
            const spans = this.querySelectorAll('span');
            this.classList.toggle('active');
            if (this.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });
    }

    // Close nav when clicking outside
    document.addEventListener('click', function (e) {
        if (navLinks && !navLinks.contains(e.target) && !navToggle.contains(e.target)) {
            navLinks.classList.remove('open');
        }
    });

    // ============================================
    // USER DROPDOWN MENU
    // ============================================
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        document.addEventListener('click', function () {
            userDropdown.classList.remove('active');
        });

        userDropdown.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    // ============================================
    // FLASH MESSAGES AUTO-CLOSE
    // ============================================
    const flashMessages = document.querySelectorAll('.flash[data-auto-close]');
    flashMessages.forEach(function (flash) {
        const timeout = parseInt(flash.getAttribute('data-auto-close')) || 5000;
        setTimeout(function () {
            flash.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => flash.remove(), 300);
        }, timeout);
    });

    // Add slideOut animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOutRight {
            from { opacity:1; transform:translateX(0); }
            to { opacity:0; transform:translateX(110%); }
        }
    `;
    document.head.appendChild(style);

    // ============================================
    // NAVBAR SCROLL EFFECT
    // ============================================
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 20) {
                navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,.12)';
            } else {
                navbar.style.boxShadow = '0 1px 8px rgba(0,0,0,.06)';
            }
        });
    }

    // ============================================
    // SCROLL REVEAL ANIMATIONS
    // ============================================
    // IntersectionObserver: element visible hone pe animation chalao
    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Cards ko animate karo
    document.querySelectorAll('.airline-card, .route-card, .step-card, .stat-card, .flight-card-result, .flight-card-mini').forEach(function (el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });

    // ============================================
    // FORM VALIDATION HELPERS
    // ============================================
    // Date inputs mein past date select na ho
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function (input) {
        if (!input.min && !input.hasAttribute('data-allow-past')) {
            input.min = new Date().toISOString().split('T')[0];
        }
    });

    // ============================================
    // AIRLINE CODE COLORS (dynamic)
    // ============================================
    // Agar koi naya airline code hai jo CSS mein nahi
    // toh default color lagao
    document.querySelectorAll('.airline-badge-small, .fcm-airline, .br-code, .uc-airline, .sum-airline-code, .et-code, .table-airline-badge').forEach(function(el) {
        const colors = { PK: '#006633', EK: '#cc0001', QR: '#5c0632', G9: '#e31837', ER: '#002b5c' };
        const code = el.textContent.trim();
        if (colors[code] && !el.style.background) {
            el.style.background = colors[code];
        }
    });

    // ============================================
    // NUMBER COUNTER ANIMATION (Stats)
    // ============================================
    function animateCounter(el, target) {
        let current = 0;
        const increment = target / 30;
        const timer = setInterval(function () {
            current += increment;
            if (current >= target) {
                el.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(current).toLocaleString();
            }
        }, 50);
    }

    // Stat numbers animate karo
    const statObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                const el = entry.target;
                const text = el.textContent.replace(/,/g, '');
                const num = parseFloat(text);
                if (!isNaN(num) && num > 0) {
                    animateCounter(el, num);
                }
                statObserver.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.sc-num').forEach(function (el) {
        statObserver.observe(el);
    });

    console.log('🛫 SkyBook JS Loaded Successfully!');
});
