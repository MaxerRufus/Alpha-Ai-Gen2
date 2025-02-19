// Theme switching functionality
let currentTheme = 0; // 0: default, 1: dark, 2: light
const themeFiles = ['/static/styles.css', '/static/styles1.css', '/static/styles2.css'];

function toggleTheme() {
    currentTheme = (currentTheme + 1) % 3;
    const styleSheet = document.getElementById('theme-style');
    styleSheet.href = themeFiles[currentTheme];
    
    // Update moon icon
    const themeIcon = document.querySelector('#theme-toggle i');
    switch(currentTheme) {
        case 0:
            themeIcon.className = 'fas fa-moon';
            break;
        case 1:
            themeIcon.className = 'fas fa-moon';
            break;
        case 2:
            themeIcon.className = 'fas fa-sun';
            break;
    }
}

$(document).ready(function() {
    // Theme toggle initialization
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Text-to-speech setup
    const synth = window.speechSynthesis;
    let voiceEnabled = true;

    // Get username from server
    $.get('/get_username', function(data) {
        $('#username, #welcome-text').text(data.username);
    });

    // Sidebar toggle functionality
    let sidebarVisible = true;
    
    function toggleSidebar() {
        sidebarVisible = !sidebarVisible;
        $('#sidebar').toggleClass('sidebar-hidden');
        $('#main-content').toggleClass('ml-64 ml-0');
        $('#toggle-sidebar i').toggleClass('fa-bars fa-chevron-right');
    }

    $('#toggle-sidebar').click(toggleSidebar);

    // New chat functionality
    $('#new-chat').click(function() {
        $('#chat-messages').empty();
        appendMessage('ai', 'Hello! How can I help you today?');
        // Add the new chat to history
        const chatEntry = $(`
            <div class="sidebar-item p-2 hover:bg-black-800 rounded cursor-pointer">
                <i class="fas fa-comment mr-2"></i>
                New Chat ${new Date().toLocaleTimeString()}
            </div>
        `);
        $('#chat-history').prepend(chatEntry);
    });

    // Voice toggle functionality
    $('#voice-toggle').click(function() {
        voiceEnabled = !voiceEnabled;
        $(this).find('i').toggleClass('text-blue-400');
        const status = voiceEnabled ? 'enabled' : 'disabled';
        showToast(`Text-to-speech ${status}`);
    });

    // Frontend JavaScript code
    $('#exit-app').click(function() {
        window.close();
        // Fallback if window.close() doesn't work
        window.location.href = 'https://www.google.com';
    });

    // Toast notification system
    function showToast(message) {
        const toast = $(`
            <div class="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg">
                ${message}
            </div>
        `).appendTo('body');

        setTimeout(() => toast.fadeOut(300, function() { $(this).remove(); }), 3000);
    }

    // Text-to-speech function
    function speakText(text) {
        if (!voiceEnabled) return;
        
        synth.cancel(); // Stop any current speech
        const utterance = new SpeechSynthesisUtterance(text);
        synth.speak(utterance);
    }

    // Message sending functionality
    function sendMessage() {
        const message = $('#user-input').val().trim();
        if (!message) return;

        appendMessage('user', message);
        $('#user-input').val('').focus();

        $.post('/get_response', {user_input: message}, function(data) {
            if (data.response) {
                appendMessage('ai', data.response);
                speakText(data.response);
            }
        });
    }

    function appendMessage(sender, content) {
        // Process the content to preserve whitespace and line breaks
        const formattedContent = content
            .split('\n')
            .map(line => {
                // Preserve leading spaces by replacing them with non-breaking spaces
                const indentMatch = line.match(/^(\s+)/);
                if (indentMatch) {
                    const indent = indentMatch[0];
                    const indentLength = indent.length;
                    const nbspIndent = '&nbsp;'.repeat(indentLength);
                    return nbspIndent + line.slice(indentLength);
                }
                return line;
            })
            .join('<br>');

        const messageHtml = `
            <div class="message-container flex space-x-4 message-enter">
                <img src="/static/${sender === 'user' ? 'user-icon.jpg' : 'bot-icon.jpg'}" 
                     class="w-12 h-12 rounded-full flex-shrink-0">
                <div class="flex-1 glass-effect rounded-lg p-4 relative group">
                    <p style="white-space: pre-wrap; font-family: monospace;">${formattedContent}</p>
                    <div class="absolute right-2 bottom-2 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button class="action-btn relative text-gray-400 hover:text-white" onclick="copyMessage(this)">
                            <i class="fas fa-copy"></i>
                            <span class="tooltip">Copy message</span>
                        </button>
                        ${sender === 'ai' ? `
                            <button class="action-btn relative text-gray-400 hover:text-white" onclick="speakMessage('${content.replace(/'/g, "\\'")}')">
                                <i class="fas fa-volume-up"></i>
                                <span class="tooltip">Speak message</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        $('#chat-messages').append(messageHtml);
        $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
    }

    // Event listeners
    $('#send-message').click(sendMessage);
    $('#user-input').keypress(function(e) {
        if (e.which == 13 && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Initial message
    appendMessage('ai', 'Hello! How can I help you today?');
});

// Update copyMessage function to preserve formatting when copying
window.copyMessage = async function(button) {
    try {
        const messageElement = $(button).closest('.message-container').find('p');
        if (!messageElement.length) {
            throw new Error('Message text not found');
        }
        
        // Get the original text with preserved formatting
        const text = messageElement.html()
            .replace(/<br>/g, '\n')  // Convert <br> back to newlines
            .replace(/&nbsp;/g, ' '); // Convert &nbsp; back to spaces
        
        // Decode HTML entities
        const decodedText = $('<textarea>').html(text).text();
        
        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(decodedText);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = decodedText;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                textArea.remove();
            } catch (err) {
                console.error('Fallback: Copy to clipboard failed', err);
                textArea.remove();
                throw new Error('Unable to copy text to clipboard');
            }
        }
        
        // Show green tick
        const icon = $(button).find('i');
        const originalClass = icon.attr('class');
        
        // Change to green tick
        icon.removeClass().addClass('fas fa-check text-success');
        
        // Reset icon after 2 seconds
        setTimeout(() => {
            icon.removeClass().addClass(originalClass);
        }, 2000);
        
        showToast('Message copied to clipboard');
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('Failed to copy message to clipboard');
    }
};

// Speak message function remains the same
window.speakMessage = function(text) {
    try {
        let messageText;
        
        if (typeof text === 'string') {
            messageText = text;
        } else {
            const messageElement = $(text).closest('.message-container').find('p');
            if (!messageElement.length) {
                throw new Error('Message text not found');
            }
            messageText = messageElement.text();
        }

        speakText(messageText);
    } catch (error) {
        console.error('Speech failed:', error);
        showToast('Failed to speak message');
    }
};

// Helper function for text-to-speech
function speakText(text) {
    if (!('speechSynthesis' in window)) {
        showToast('Text-to-speech is not supported in your browser');
        return;
    }
    
    // Check text length
    if (text.length > 500) {
        showToast('Message is too long for text-to-speech. Maximum length is 500 characters.');
        return;
    }
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Optional: Configure speech settings
    utterance.rate = 1.0;  // Speed: 0.1 to 10
    utterance.pitch = 1.0; // Pitch: 0 to 2
    utterance.volume = 1.0; // Volume: 0 to 1
    
    // Use default system voice
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
        utterance.voice = voices[0];
    }
    
    utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        showToast('Failed to speak message');
    };
    
    window.speechSynthesis.speak(utterance);
}

// Helper function for showing toast messages
function showToast(message) {
    if (typeof window.showToast === 'function') {
        window.showToast(message);
    } else {
        console.log(message);
    }
}


function startDictation() {
    if (window.hasOwnProperty('webkitSpeechRecognition') || window.hasOwnProperty('SpeechRecognition')) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        // Create and preload audio elements for sound effects
        const startSound = new Audio('/static/start-listening.mp3');
        const endSound = new Audio('/static/end-listening.mp3');
        startSound.load();
        endSound.load();
        endSound.onerror = () => console.error('Failed to load end-listening.mp3');
        startSound.onerror = () => console.error('Failed to load start-listening.mp3');
        
        // Play start sound before recognition starts
        startSound.play().then(() => {
            recognition.start();
        }).catch(error => {
            console.error('Failed to play start sound:', error);
            recognition.start();
        });
        
        let lastSpeechTime = Date.now();
        let timeoutId = null;
        
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onstart = function() {
            console.log('Voice recognition activated. Speak now.');
            $('#mic-button').addClass('recording');
            startSound.play(); // Play start sound
        };

        recognition.onresult = function(event) {
            clearTimeout(timeoutId);
            lastSpeechTime = Date.now();
            let transcript = '';
            
            // Get the latest result only
            const lastResult = event.results[event.results.length - 1];
            if (lastResult.isFinal) {
                transcript = lastResult[0].transcript;
                $('#user-input').val(transcript);
                
                if (transcript.trim()) {
                    recognition.stop();
                    $('#send-message').click();
                }
            } else {
                // Show interim results
                transcript = lastResult[0].transcript;
                $('#user-input').val(transcript);
            }
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            $('#mic-button').removeClass('recording');
            endSound.play(); // Play end sound on error
        };

        recognition.onend = function() {
            $('#mic-button').removeClass('recording');
            endSound.play(); // Play end sound
        };

        recognition.start();
    } else {
        alert('Speech recognition is not supported in this browser.');
    }
}


// Add event listener to mic button
$(document).ready(function() {
    $('#mic-button').click(startDictation);
});

// Spotify Player Class
class SpotifyPlayer {
    constructor() {
        this.currentTrackId = null;
        this.isPlaying = false;
        this.updateInterval = null;
        this.isActive = false;
        this.initialize();
    }

    initialize() {
        this.attachEventListeners();
        this.checkAuthenticationStatus();
    }

    attachEventListeners() {
        document.getElementById('toggle-player').addEventListener('click', () => this.togglePlayer());
        document.getElementById('play-pause').addEventListener('click', () => this.togglePlayback());
        document.getElementById('next-track').addEventListener('click', () => this.controlPlayback('next'));
        document.getElementById('prev-track').addEventListener('click', () => this.controlPlayback('previous'));
        document.getElementById('like-button').addEventListener('click', () => this.toggleSaveTrack());
        
        const progressBar = document.querySelector('.progress-bar');
        progressBar.addEventListener('click', (e) => this.handleProgressBarClick(e));
    }

    togglePlayer() {
        this.isActive = !this.isActive;
        document.querySelector('.spotify-player').classList.toggle('active', this.isActive);
        
        if (this.isActive) {
            this.getCurrentTrack();
            this.startPeriodicUpdates();
        } else {
            this.stopPeriodicUpdates();
        }
    }

    async checkAuthenticationStatus() {
        try {
            const response = await fetch('/api/current-track');
            const data = await response.json();
            
            if (data.error === "Authentication required") {
                window.location.href = '/spotify/login';
            }
        } catch (error) {
            this.showError("Failed to check authentication status");
        }
    }

    async getCurrentTrack() {
        try {
            this.showLoading();
            const response = await fetch('/api/current-track');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.status === "success") {
                this.updatePlayerUI(data);
            } else if (data.status === "no_track") {
                this.updatePlayerUINoTrack();
            }
        } catch (error) {
            this.showError("Failed to get current track");
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        document.querySelector('.loading').style.display = 'none';
    }

    hideLoading() {
        document.querySelector('.loading').style.display = 'none';
    }

    updatePlayerUI(data) {
        document.getElementById('track-name').textContent = data.name;
        document.getElementById('artist-name').textContent = data.artist;
        document.getElementById('album-name').textContent = data.album;
        
        const albumArt = document.getElementById('album-art');
        if (data.album_art && albumArt.src !== data.album_art) {
            albumArt.style.opacity = '0';
            setTimeout(() => {
                albumArt.src = data.album_art;
                albumArt.style.opacity = '1';
            }, 300);
        }
        
        this.isPlaying = data.is_playing;
        const playPauseIcon = document.querySelector('#play-pause i');
        playPauseIcon.className = `fas fa-${this.isPlaying ? 'pause' : 'play'}`;
        
        this.updateProgress(data.progress_ms, data.duration_ms);
        
        const likeButton = document.getElementById('like-button');
        likeButton.classList.toggle('active', data.is_saved);
        
        this.currentTrackId = data.track_id;
    }

    updatePlayerUINoTrack() {
        document.getElementById('track-name').textContent = 'No track playing';
        document.getElementById('artist-name').textContent = 'Open Spotify to play music';
        document.getElementById('album-name').textContent = '';
        document.getElementById('album-art').src = '/static/placeholder-album.jpg';
        document.querySelector('.progress-bar-fill').style.width = '0%';
        document.querySelector('#play-pause i').className = 'fas fa-play';
        document.getElementById('current-time').textContent = '0:00';
        document.getElementById('total-time').textContent = '0:00';
        this.currentTrackId = null;
    }

    updateProgress(progress, duration) {
        const progressPercent = (progress / duration) * 100;
        document.querySelector('.progress-bar-fill').style.width = `${progressPercent}%`;
        
        document.getElementById('current-time').textContent = this.formatTime(progress);
        document.getElementById('total-time').textContent = this.formatTime(duration);
    }

    formatTime(ms) {
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    async togglePlayback() {
        const action = this.isPlaying ? 'pause' : 'play';
        await this.controlPlayback(action);
    }

    async controlPlayback(action) {
        try {
            const response = await fetch(`/api/playback/${action}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            setTimeout(() => this.getCurrentTrack(), 200);
        } catch (error) {
            this.showError(`Spotify-Premium Required`);
        }
    }

    async toggleSaveTrack() {
        if (!this.currentTrackId) return;
        
        try {
            const response = await fetch(`/api/toggle-save/${this.currentTrackId}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            document.getElementById('like-button').classList.toggle('active', data.is_saved);
        } catch (error) {
            this.showError("Failed to toggle save status");
        }
    }

    handleProgressBarClick(e) {
        if (!this.currentTrackId) return;
        
        const progressBar = e.currentTarget;
        const rect = progressBar.getBoundingClientRect();
        const clickPosition = (e.clientX - rect.left) / rect.width;
        
        document.querySelector('.progress-bar-fill').style.width = `${clickPosition * 100}%`;
        
        if (this.currentTrackId) {
            const totalDuration = parseInt(document.getElementById('total-time').getAttribute('data-duration'));
            const seekPosition = Math.floor(totalDuration * clickPosition);
            this.seekTrack(seekPosition);
        }
    }

    async seekTrack(position) {
        try {
            const response = await fetch(`/api/seek/${position}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            setTimeout(() => this.getCurrentTrack(), 200);
        } catch (error) {
            this.showError("Spotify-Premium Required");
        }
    }

    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => this.getCurrentTrack(), 1000);
    }

    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 3000);
    }
}

// Initialize Spotify Player when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.spotifyPlayer = new SpotifyPlayer();
});
