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

    // ──────────────────────────────────────────────
    //  GDev Helper Chatbot Logic
    // ──────────────────────────────────────────────
    const chatTrigger = document.getElementById('chat-trigger');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    if (chatTrigger && chatWindow && chatClose && chatMessages && chatInput && chatSend) {
        // Toggle Chat Window
        chatTrigger.addEventListener('click', () => {
            chatWindow.classList.toggle('active');
            if (chatWindow.classList.contains('active')) {
                chatInput.focus();
                // Scroll to bottom when opening
                scrollToBottom();
            }
        });

        // Close Chat Window
        chatClose.addEventListener('click', () => {
            chatWindow.classList.remove('active');
        });

        // Send Message on click
        chatSend.addEventListener('click', () => {
            handleUserMessage();
        });

        // Send Message on Enter key
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Prevent default new line
                handleUserMessage();
            }
        });

        // Auto-expand textarea on typing
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = (chatInput.scrollHeight) + 'px';
            if (chatInput.scrollHeight > 80) {
                chatInput.style.overflowY = 'auto';
            } else {
                chatInput.style.overflowY = 'hidden';
            }
        });

        function handleUserMessage() {
            const messageText = chatInput.value.trim();
            if (!messageText) return;

            // Append User Message to Screen
            appendMessage('user', messageText);
            
            // Clear and reset Input
            chatInput.value = '';
            chatInput.style.height = 'auto';

            // Show Typing Indicator
            showTypingIndicator();

            // Send to Flask Backend API
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro de conexão com o servidor');
                }
                return response.json();
            })
            .then(data => {
                removeTypingIndicator();
                const botResponse = data.response || "Olá! Desculpe, não consegui processar sua mensagem agora. Pode tentar de novo?";
                appendMessage('bot', botResponse);
            })
            .catch(error => {
                removeTypingIndicator();
                console.error('Chatbot error:', error);
                appendMessage('bot', "Ops! Tive um pequeno problema de rede para me conectar à inteligência artificial. Por favor, tente novamente.");
            });
        }

        function appendMessage(sender, text) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `message-${sender}`, 'animate-fade-in');

            const contentDiv = document.createElement('div');
            contentDiv.classList.add('message-content');

            if (sender === 'bot') {
                // Basic markdown parsing for Bot responses (bold, linebreaks, codeblocks)
                contentDiv.innerHTML = formatMarkdown(text);
            } else {
                contentDiv.textContent = text;
            }

            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        function showTypingIndicator() {
            // Check if typing indicator already exists
            if (document.getElementById('typing-indicator')) return;

            const indicatorDiv = document.createElement('div');
            indicatorDiv.id = 'typing-indicator';
            indicatorDiv.classList.add('message', 'message-bot', 'animate-fade-in');

            const contentDiv = document.createElement('div');
            contentDiv.classList.add('message-content');
            
            const typingIndicator = document.createElement('div');
            typingIndicator.classList.add('typing-indicator');
            typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

            contentDiv.appendChild(typingIndicator);
            indicatorDiv.appendChild(contentDiv);
            chatMessages.appendChild(indicatorDiv);
            scrollToBottom();
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function formatMarkdown(text) {
            // Replace linebreaks with <br>
            let formatted = text.replace(/\n/g, '<br>');

            // Replace Bold (**text**) with <strong>text</strong>
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

            // Replace Code block (```code```) with <pre><code>code</code></pre>
            formatted = formatted.replace(/```(.*?)```/gs, '<pre style="background: rgba(0,0,0,0.4); padding: 0.5rem 0.75rem; border-radius: 6px; font-family: monospace; font-size: 0.85rem; border: 1px solid var(--border-glass); margin: 0.5rem 0; overflow-x: auto; color: var(--primary);"><code style="font-family: inherit;">$1</code></pre>');

            // Replace Inline Code (`code`) with <code style="font-family: monospace; background: rgba(255,255,255,0.1); padding: 0.1rem 0.3rem; border-radius: 4px; color: var(--accent);">$1</code>
            formatted = formatted.replace(/`(.*?)`/g, '<code style="font-family: monospace; background: rgba(255,255,255,0.1); padding: 0.1rem 0.3rem; border-radius: 4px; color: var(--accent); font-size: 0.85rem;">$1</code>');

            return formatted;
        }
    }
});
