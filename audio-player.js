/**
 * CEO Briefing Audio Player
 * Uses Web Speech API for text-to-speech with speed control.
 * Drop-in: include this script and call initAudioPlayer().
 */
(function() {
  'use strict';

  let synth = window.speechSynthesis;
  let utterance = null;
  let isPlaying = false;
  let isPaused = false;
  let currentSpeed = 1.0;
  let sections = [];
  let currentSectionIdx = 0;
  let playerEl = null;

  function getTextContent() {
    // Extract readable text from briefing sections
    const cards = document.querySelectorAll('article.card, .section');
    const parts = [];
    
    // Get section headers and card content
    document.querySelectorAll('.section').forEach(section => {
      const header = section.querySelector('.section-title, h2');
      if (header) {
        parts.push({ type: 'header', text: header.textContent.trim() });
      }
      section.querySelectorAll('article.card').forEach(card => {
        const headline = card.querySelector('.card-headline, h3');
        const summary = card.querySelector('.card-summary, .summary, p');
        let text = '';
        if (headline) text += headline.textContent.trim() + '. ';
        if (summary) text += summary.textContent.trim();
        if (!text && card.textContent) {
          // Fallback: get all text but skip table data
          const clone = card.cloneNode(true);
          clone.querySelectorAll('table, .index-table, .gauge-container').forEach(el => el.remove());
          text = clone.textContent.trim().substring(0, 500);
        }
        if (text) parts.push({ type: 'card', text: text });
      });
    });

    // If no sections found, get all article cards
    if (parts.length === 0) {
      document.querySelectorAll('article.card').forEach(card => {
        const clone = card.cloneNode(true);
        clone.querySelectorAll('table, .index-table, .gauge-container').forEach(el => el.remove());
        const text = clone.textContent.trim();
        if (text) parts.push({ type: 'card', text: text.substring(0, 800) });
      });
    }

    return parts;
  }

  function detectLanguage() {
    const html = document.documentElement;
    const lang = html.getAttribute('lang') || '';
    if (lang.startsWith('ja')) return 'ja-JP';
    // Check filename
    if (window.location.pathname.includes('-ja') || window.location.pathname.includes('/ja')) return 'ja-JP';
    return 'en-US';
  }

  function getVoice(lang) {
    const voices = synth.getVoices();
    if (!voices.length) return null;
    
    // Prefer high-quality voices
    const preferred = lang === 'ja-JP' 
      ? ['Kyoko', 'Otoya', 'O-Ren', 'Siri', 'Google']
      : ['Samantha', 'Alex', 'Daniel', 'Siri', 'Google'];
    
    for (const pref of preferred) {
      const v = voices.find(v => v.name.includes(pref) && v.lang.startsWith(lang.substring(0, 2)));
      if (v) return v;
    }
    // Fallback to any voice in the right language
    return voices.find(v => v.lang.startsWith(lang.substring(0, 2))) || voices[0];
  }

  function speakSection(idx) {
    if (idx >= sections.length) {
      stop();
      return;
    }
    currentSectionIdx = idx;
    updateProgress();

    const lang = detectLanguage();
    utterance = new SpeechSynthesisUtterance(sections[idx].text);
    utterance.lang = lang;
    utterance.rate = currentSpeed;
    utterance.pitch = 1.0;
    
    const voice = getVoice(lang);
    if (voice) utterance.voice = voice;

    utterance.onend = () => {
      if (isPlaying && !isPaused) {
        speakSection(idx + 1);
      }
    };
    utterance.onerror = (e) => {
      if (e.error !== 'canceled') {
        speakSection(idx + 1);
      }
    };

    synth.speak(utterance);
  }

  function play() {
    if (isPaused) {
      synth.resume();
      isPaused = false;
      isPlaying = true;
      updateUI();
      return;
    }

    sections = getTextContent();
    if (!sections.length) return;

    isPlaying = true;
    isPaused = false;
    updateUI();
    speakSection(currentSectionIdx);
  }

  function pause() {
    synth.pause();
    isPaused = true;
    isPlaying = false;
    updateUI();
  }

  function stop() {
    synth.cancel();
    isPlaying = false;
    isPaused = false;
    currentSectionIdx = 0;
    updateUI();
  }

  function skipForward() {
    synth.cancel();
    if (currentSectionIdx < sections.length - 1) {
      currentSectionIdx++;
      if (isPlaying || isPaused) {
        isPaused = false;
        isPlaying = true;
        speakSection(currentSectionIdx);
        updateUI();
      }
    }
  }

  function skipBack() {
    synth.cancel();
    if (currentSectionIdx > 0) {
      currentSectionIdx--;
      if (isPlaying || isPaused) {
        isPaused = false;
        isPlaying = true;
        speakSection(currentSectionIdx);
        updateUI();
      }
    }
  }

  function setSpeed(speed) {
    currentSpeed = speed;
    document.querySelector('.cbap-speed-value').textContent = speed.toFixed(1) + '×';
    // If currently playing, restart current section at new speed
    if (isPlaying) {
      synth.cancel();
      speakSection(currentSectionIdx);
    }
  }

  function updateProgress() {
    const prog = playerEl.querySelector('.cbap-progress-fill');
    if (prog && sections.length) {
      prog.style.width = ((currentSectionIdx + 1) / sections.length * 100) + '%';
    }
    const count = playerEl.querySelector('.cbap-section-count');
    if (count && sections.length) {
      count.textContent = (currentSectionIdx + 1) + ' / ' + sections.length;
    }
  }

  function updateUI() {
    const playBtn = playerEl.querySelector('.cbap-play');
    const pauseBtn = playerEl.querySelector('.cbap-pause');
    if (isPlaying) {
      playBtn.style.display = 'none';
      pauseBtn.style.display = 'inline-flex';
    } else {
      playBtn.style.display = 'inline-flex';
      pauseBtn.style.display = 'none';
    }
    updateProgress();
  }

  function createPlayer() {
    const lang = detectLanguage();
    const isJa = lang === 'ja-JP';

    const el = document.createElement('div');
    el.className = 'cbap-player';
    el.innerHTML = `
      <div class="cbap-progress"><div class="cbap-progress-fill"></div></div>
      <div class="cbap-controls">
        <div class="cbap-left">
          <button class="cbap-btn cbap-skip-back" title="${isJa ? '前へ' : 'Previous'}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="19 20 9 12 19 4"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
          </button>
          <button class="cbap-btn cbap-play" title="${isJa ? '再生' : 'Play'}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21"/></svg>
          </button>
          <button class="cbap-btn cbap-pause" style="display:none" title="${isJa ? '一時停止' : 'Pause'}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          </button>
          <button class="cbap-btn cbap-stop" title="${isJa ? '停止' : 'Stop'}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
          </button>
          <button class="cbap-btn cbap-skip-fwd" title="${isJa ? '次へ' : 'Next'}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
          </button>
        </div>
        <div class="cbap-right">
          <span class="cbap-section-count"></span>
          <div class="cbap-speed-control">
            <button class="cbap-btn cbap-speed-down" title="Slower">−</button>
            <span class="cbap-speed-value">1.0×</span>
            <button class="cbap-btn cbap-speed-up" title="Faster">+</button>
          </div>
        </div>
      </div>
    `;

    // Wire events
    el.querySelector('.cbap-play').addEventListener('click', play);
    el.querySelector('.cbap-pause').addEventListener('click', pause);
    el.querySelector('.cbap-stop').addEventListener('click', stop);
    el.querySelector('.cbap-skip-back').addEventListener('click', skipBack);
    el.querySelector('.cbap-skip-fwd').addEventListener('click', skipForward);
    el.querySelector('.cbap-speed-down').addEventListener('click', () => {
      setSpeed(Math.max(0.5, currentSpeed - 0.25));
    });
    el.querySelector('.cbap-speed-up').addEventListener('click', () => {
      setSpeed(Math.min(3.0, currentSpeed + 0.25));
    });

    return el;
  }

  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .cbap-player {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(30, 30, 30, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        color: #fff;
        z-index: 9999;
        font-family: var(--sans, -apple-system, BlinkMacSystemFont, sans-serif);
        padding-bottom: env(safe-area-inset-bottom, 0);
      }
      .cbap-progress {
        height: 3px;
        background: rgba(255,255,255,0.15);
        cursor: pointer;
      }
      .cbap-progress-fill {
        height: 100%;
        background: var(--bg-accent, #2A8F87);
        width: 0%;
        transition: width 0.3s ease;
      }
      .cbap-controls {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 16px;
        max-width: 900px;
        margin: 0 auto;
      }
      .cbap-left, .cbap-right {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .cbap-btn {
        background: none;
        border: none;
        color: #fff;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: background 0.15s;
        font-size: 14px;
        line-height: 1;
      }
      .cbap-btn:hover {
        background: rgba(255,255,255,0.12);
      }
      .cbap-btn:active {
        background: rgba(255,255,255,0.2);
      }
      .cbap-speed-control {
        display: flex;
        align-items: center;
        gap: 2px;
        background: rgba(255,255,255,0.08);
        border-radius: 999px;
        padding: 0 4px;
      }
      .cbap-speed-value {
        font-size: 0.75rem;
        font-weight: 600;
        min-width: 36px;
        text-align: center;
        letter-spacing: 0.02em;
      }
      .cbap-section-count {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.5);
        margin-right: 8px;
      }
      .cbap-speed-down, .cbap-speed-up {
        font-size: 16px;
        font-weight: 700;
        padding: 6px 8px;
      }
      @media (max-width: 480px) {
        .cbap-controls { padding: 6px 12px; }
        .cbap-btn { padding: 6px; }
      }
    `;
    document.head.appendChild(style);
  }

  // Wait for voices to load (needed on some browsers)
  function ensureVoices(cb) {
    const voices = synth.getVoices();
    if (voices.length) { cb(); return; }
    synth.addEventListener('voiceschanged', () => cb(), { once: true });
    // Timeout fallback
    setTimeout(cb, 1000);
  }

  window.initAudioPlayer = function() {
    if (!('speechSynthesis' in window)) return;
    injectStyles();
    ensureVoices(() => {
      playerEl = createPlayer();
      document.body.appendChild(playerEl);
      // Add bottom padding to body so content isn't hidden behind player
      document.body.style.paddingBottom = '64px';
    });
  };

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.initAudioPlayer());
  } else {
    window.initAudioPlayer();
  }
})();
