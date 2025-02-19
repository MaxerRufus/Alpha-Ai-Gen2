// spotify-player.js
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
        document.querySelector('.loading').style.display = 'block';
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
        
        // Store duration for seek functionality
        document.getElementById('total-time').setAttribute('data-duration', duration);
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

// Initialize Spotify Player when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.spotifyPlayer = new SpotifyPlayer();
});