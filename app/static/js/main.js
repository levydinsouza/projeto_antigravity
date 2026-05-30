/**
 * GDev Tutorial - Main Javascript Application
 * Handles layout interactions, responsiveness, and premium micro-animations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ──────────────────────────────────────────────
    //  Mobile Navigation Toggle
    // ──────────────────────────────────────────────
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    const navbar = document.getElementById('navbar');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            // Toggle classes for hamburger animation and menu slide
            navToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });

        // Close menu when a link is clicked (useful for anchors)
        const links = navLinks.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                navLinks.classList.remove('active');
                document.body.classList.remove('menu-open');
            });
        });
    }

    // ──────────────────────────────────────────────
    //  Navbar Glassmorphism & Sticky Scroll Effect
    // ──────────────────────────────────────────────
    const handleScroll = () => {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };

    if (navbar) {
        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Check on init in case page was refreshed scrolled
    }

    // ──────────────────────────────────────────────
    //  Automatic Smooth Fade for Flash Messages
    // ──────────────────────────────────────────────
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(flash => {
        // Set a timer to start fading out after 4 seconds
        setTimeout(() => {
            flash.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            
            // Remove from DOM entirely after the animation finishes
            setTimeout(() => {
                flash.remove();
            }, 600);
        }, 4000);
    });

    // ──────────────────────────────────────────────
    //  Micro-animations & Reveal on Scroll
    // ──────────────────────────────────────────────
    const revealElements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window && revealElements.length > 0) {
        const observerOptions = {
            root: null,
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target); // Reveal only once
                }
            });
        }, observerOptions);

        revealElements.forEach(element => {
            observer.observe(element);
        });
    } else {
        // Fallback for browsers without Intersection Observer
        revealElements.forEach(element => {
            element.classList.add('visible');
        });
    }
});
