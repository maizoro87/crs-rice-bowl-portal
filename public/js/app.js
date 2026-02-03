/**
 * CRS Rice Bowl Portal - Main Application JavaScript
 * Handles data fetching, UI updates, countdown timer, and interactivity
 */

// Configuration
const CONFIG = {
  API_ENDPOINT: '/api/data',
  REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
  COUNTDOWN_UPDATE_INTERVAL: 1000, // 1 second
  AUTO_REFRESH_ENABLED: true,
  GRAND_TOTAL_CUTOFF_DATE: '2026-03-25'
};

// State
let appState = {
  data: null,
  countdownInterval: null,
  refreshInterval: null,
  currentExpandedWeek: null
};

/**
 * Initialize the application
 */
async function init() {
  console.log('🚀 CRS Rice Bowl Portal initializing...');

  try {
    // Initial data fetch
    await fetchData();

    // Setup event listeners
    setupEventListeners();

    // Setup auto-refresh if enabled
    if (CONFIG.AUTO_REFRESH_ENABLED) {
      appState.refreshInterval = setInterval(fetchData, CONFIG.REFRESH_INTERVAL);
      console.log(`🔄 Auto-refresh enabled (every ${CONFIG.REFRESH_INTERVAL / 1000}s)`);
    }

    console.log('✅ Application initialized successfully');
  } catch (error) {
    console.error('❌ Initialization failed:', error);
    showError('Failed to load portal data. Please refresh the page.');
  }
}

/**
 * Fetch data from API
 */
async function fetchData() {
  console.log('📡 Fetching data from API...');

  try {
    const response = await fetch(CONFIG.API_ENDPOINT);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Data fetched successfully:', data);

    appState.data = data;
    populatePage(data);

  } catch (error) {
    console.error('❌ Error fetching data:', error);
    showError('Unable to load data. Please check your connection and try again.');
    throw error;
  }
}

/**
 * Populate all page sections with data
 */
function populatePage(data) {
  console.log('🎨 Populating page with data...');

  // Apply theme
  applyTheme(data.settings?.theme || 'lenten-purple');

  // Set CRS donation link on buttons
  setCRSLinks(data.settings?.crs_donation_link);

  // Display online alms total
  displayOnlineAlms(data.settings?.online_alms_total);

  // Display announcements
  displayAnnouncements(data.announcements || []);

  // Find current week quiz
  const currentWeekQuiz = data.quizzes?.find(q => q.week_number === data.current_week && q.is_visible);

  if (currentWeekQuiz) {
    // Populate quiz section
    populateQuizSection(currentWeekQuiz);

    // Start countdown timer
    startCountdown(currentWeekQuiz.closes_at);
  } else {
    console.warn('⚠️ No current week quiz found');
  }

  // Build past weeks accordion
  buildPastWeeksAccordion(data.quizzes || [], data.current_week);

  // Populate leaderboard
  populateLeaderboard(data.classes || []);

  // Populate top 3 classes showcase
  populateTop3Classes(data.classes || []);

  // Display totals
  displayClassDonationsTotal(data.rice_bowl_total);
  displayGrandTotal(data, data.settings?.show_grand_total);

  // Update thermometer
  updateThermometer(data.grand_total || 0);

  console.log('✅ Page populated successfully');
}

/**
 * Apply theme to page
 */
function applyTheme(theme) {
  document.body.className = theme;
  console.log(`🎨 Applied theme: ${theme}`);
}

/**
 * Set CRS donation links on all buttons
 */
function setCRSLinks(link) {
  if (!link) {
    console.warn('⚠️ No CRS donation link provided');
    return;
  }

  const buttons = document.querySelectorAll('.crs-donate-btn');
  buttons.forEach(btn => {
    btn.href = link;
  });

  console.log(`🔗 Set CRS donation link on ${buttons.length} button(s)`);
}

/**
 * Display online alms total
 */
function displayOnlineAlms(amount) {
  const element = document.getElementById('online-alms-total');
  if (!element) return;

  const formatted = formatCurrency(parseFloat(amount) || 0);
  element.textContent = formatted;
  console.log(`💰 Online alms total: ${formatted}`);
}

/**
 * Display active announcements
 */
function displayAnnouncements(announcements) {
  const container = document.getElementById('announcements-container');
  if (!container) return;

  const activeAnnouncements = announcements.filter(a => a.enabled);

  if (activeAnnouncements.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';

  // Clear existing content
  container.textContent = '';

  // Create announcement elements safely
  activeAnnouncements.forEach(a => {
    const announcementDiv = document.createElement('div');
    announcementDiv.className = 'announcement';

    const iconSpan = document.createElement('span');
    iconSpan.className = 'announcement-icon';
    iconSpan.textContent = '📢';

    const textSpan = document.createElement('span');
    textSpan.className = 'announcement-text';
    textSpan.textContent = a.text;

    announcementDiv.appendChild(iconSpan);
    announcementDiv.appendChild(textSpan);
    container.appendChild(announcementDiv);
  });

  console.log(`📢 Displayed ${activeAnnouncements.length} announcement(s)`);
}

/**
 * Populate quiz section
 */
function populateQuizSection(quiz) {
  // Quiz title
  const titleElement = document.getElementById('quiz-title');
  if (titleElement) {
    titleElement.textContent = `Week ${quiz.week_number}: ${quiz.country_name}`;
  }

  // Quiz description
  const descElement = document.getElementById('quiz-description');
  if (descElement) {
    descElement.textContent = quiz.description || '';
  }

  // Quiz link
  const linkElement = document.getElementById('quiz-link');
  if (linkElement && quiz.forms_link) {
    linkElement.href = quiz.forms_link;
    linkElement.style.display = 'inline-block';
  } else if (linkElement) {
    linkElement.style.display = 'none';
  }

  // Participant count
  const countElement = document.getElementById('participant-count');
  if (countElement) {
    countElement.textContent = quiz.participant_count || 0;
  }

  // Participant list
  const listElement = document.getElementById('participant-list');
  if (listElement) {
    listElement.textContent = ''; // Clear existing

    if (quiz.participants && quiz.participants.length > 0) {
      quiz.participants.forEach(p => {
        const li = document.createElement('li');
        li.textContent = p;
        listElement.appendChild(li);
      });
    } else {
      const li = document.createElement('li');
      li.className = 'no-data';
      li.textContent = 'No participants yet';
      listElement.appendChild(li);
    }
  }

  // Winners
  const winnersElement = document.getElementById('winners-list');
  if (winnersElement) {
    if (quiz.winners && quiz.winners.length > 0) {
      winnersElement.textContent = ''; // Clear existing

      quiz.winners.forEach((w, idx) => {
        const li = document.createElement('li');
        const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉';
        li.textContent = `${medal} ${w}`;
        winnersElement.appendChild(li);
      });

      winnersElement.parentElement.style.display = 'block';
    } else {
      winnersElement.parentElement.style.display = 'none';
    }
  }

  console.log(`📝 Populated quiz section for Week ${quiz.week_number}`);
}

/**
 * Start countdown timer
 */
function startCountdown(closesAt) {
  // Clear existing interval
  if (appState.countdownInterval) {
    clearInterval(appState.countdownInterval);
  }

  const countdownElement = document.getElementById('countdown-timer');
  if (!countdownElement) return;

  const closeDate = new Date(closesAt);

  const updateCountdown = () => {
    const now = new Date();
    const diff = closeDate - now;

    if (diff <= 0) {
      countdownElement.textContent = '';
      const expiredSpan = document.createElement('span');
      expiredSpan.className = 'countdown-expired';
      expiredSpan.textContent = '⏰ Quiz Closed';
      countdownElement.appendChild(expiredSpan);
      countdownElement.classList.remove('countdown-urgent');
      clearInterval(appState.countdownInterval);
      return;
    }

    const formatted = formatCountdown(diff);
    countdownElement.textContent = formatted;

    // Add pulse animation if less than 1 hour remaining
    if (diff < 60 * 60 * 1000) {
      countdownElement.classList.add('countdown-urgent');
    } else {
      countdownElement.classList.remove('countdown-urgent');
    }
  };

  updateCountdown(); // Initial update
  appState.countdownInterval = setInterval(updateCountdown, CONFIG.COUNTDOWN_UPDATE_INTERVAL);

  console.log(`⏱️ Countdown started, closes at: ${closesAt}`);
}

/**
 * Build past weeks accordion
 */
function buildPastWeeksAccordion(quizzes, currentWeek) {
  const container = document.getElementById('past-weeks-accordion');
  if (!container) return;

  const pastWeeks = quizzes
    .filter(q => q.week_number < currentWeek && q.is_visible)
    .sort((a, b) => b.week_number - a.week_number); // Most recent first

  if (pastWeeks.length === 0) {
    container.textContent = '';
    const p = document.createElement('p');
    p.className = 'no-data';
    p.textContent = 'No past weeks available yet.';
    container.appendChild(p);
    return;
  }

  // Clear container
  container.textContent = '';

  pastWeeks.forEach(quiz => {
    // Create accordion item
    const item = document.createElement('div');
    item.className = 'accordion-item';
    item.dataset.week = quiz.week_number;

    // Create header
    const header = document.createElement('div');
    header.className = 'accordion-header';
    header.dataset.week = quiz.week_number;

    const h3 = document.createElement('h3');
    h3.textContent = `Week ${quiz.week_number}: ${quiz.country_name}`;

    const icon = document.createElement('span');
    icon.className = 'accordion-icon';
    icon.textContent = '▼';

    header.appendChild(h3);
    header.appendChild(icon);

    // Create content
    const content = document.createElement('div');
    content.className = 'accordion-content';

    const descP = document.createElement('p');
    descP.className = 'quiz-description';
    descP.textContent = quiz.description || '';
    content.appendChild(descP);

    const statsDiv = document.createElement('div');
    statsDiv.className = 'quiz-stats';

    const participantsP = document.createElement('p');
    const strong = document.createElement('strong');
    strong.textContent = 'Participants:';
    participantsP.appendChild(strong);
    participantsP.appendChild(document.createTextNode(` ${quiz.participant_count || 0}`));
    statsDiv.appendChild(participantsP);

    // Add winners if present
    if (quiz.winners && quiz.winners.length > 0) {
      const winnersDiv = document.createElement('div');
      winnersDiv.className = 'winners-section';

      const winnersStrong = document.createElement('strong');
      winnersStrong.textContent = 'Winners:';
      winnersDiv.appendChild(winnersStrong);

      const winnersList = document.createElement('ol');
      winnersList.className = 'winners-list';

      quiz.winners.forEach((w, idx) => {
        const li = document.createElement('li');
        const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉';
        li.textContent = `${medal} ${w}`;
        winnersList.appendChild(li);
      });

      winnersDiv.appendChild(winnersList);
      statsDiv.appendChild(winnersDiv);
    }

    content.appendChild(statsDiv);

    item.appendChild(header);
    item.appendChild(content);
    container.appendChild(item);
  });

  // Add click handlers for accordion
  setupAccordionHandlers();

  console.log(`📋 Built accordion with ${pastWeeks.length} past week(s)`);
}

/**
 * Setup accordion click handlers
 */
function setupAccordionHandlers() {
  const headers = document.querySelectorAll('.accordion-header');

  headers.forEach(header => {
    header.addEventListener('click', () => {
      const weekNumber = header.dataset.week;
      const item = header.parentElement;
      const icon = header.querySelector('.accordion-icon');

      // Close other items (optional - comment out to allow multiple open)
      document.querySelectorAll('.accordion-item').forEach(otherItem => {
        if (otherItem !== item && otherItem.classList.contains('active')) {
          otherItem.classList.remove('active');
          otherItem.querySelector('.accordion-icon').textContent = '▼';
        }
      });

      // Toggle current item
      const isActive = item.classList.toggle('active');
      icon.textContent = isActive ? '▲' : '▼';

      appState.currentExpandedWeek = isActive ? weekNumber : null;
    });
  });
}

/**
 * Populate leaderboard table
 */
function populateLeaderboard(classes) {
  const tbody = document.querySelector('#leaderboard-table tbody');
  if (!tbody) return;

  // Clear existing content
  tbody.textContent = '';

  if (classes.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;
    td.className = 'no-data';
    td.textContent = 'No class data available yet.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  // Sort by rice_bowl_amount descending
  const sortedClasses = [...classes].sort((a, b) =>
    (parseFloat(b.rice_bowl_amount) || 0) - (parseFloat(a.rice_bowl_amount) || 0)
  );

  sortedClasses.forEach((cls, index) => {
    const rank = index + 1;
    const amount = parseFloat(cls.rice_bowl_amount) || 0;
    const formattedAmount = formatCurrency(amount);

    let rankClass = '';
    let rankDisplay = rank.toString();

    if (rank === 1) {
      rankClass = 'rank-gold';
      rankDisplay = '🥇';
    } else if (rank === 2) {
      rankClass = 'rank-silver';
      rankDisplay = '🥈';
    } else if (rank === 3) {
      rankClass = 'rank-bronze';
      rankDisplay = '🥉';
    }

    const tr = document.createElement('tr');
    if (rankClass) {
      tr.className = rankClass;
    }

    const rankTd = document.createElement('td');
    rankTd.className = 'rank-cell';
    rankTd.textContent = rankDisplay;

    const nameTd = document.createElement('td');
    nameTd.className = 'class-name';
    nameTd.textContent = cls.name;

    const amountTd = document.createElement('td');
    amountTd.className = 'amount-cell';
    amountTd.textContent = formattedAmount;

    tr.appendChild(rankTd);
    tr.appendChild(nameTd);
    tr.appendChild(amountTd);
    tbody.appendChild(tr);
  });

  console.log(`📊 Populated leaderboard with ${sortedClasses.length} class(es)`);
}

/**
 * Display class donations total
 */
function displayClassDonationsTotal(amount) {
  // Update both the leaderboard total and the totals section
  const elements = [
    document.getElementById('class-donations-total'),
    document.getElementById('class-donations-total-display')
  ];

  const formatted = formatCurrency(parseFloat(amount) || 0);

  elements.forEach(element => {
    if (element) element.textContent = formatted;
  });

  console.log(`💰 Class donations total: ${formatted}`);
}

/**
 * Populate top 3 classes showcase
 */
function populateTop3Classes(classes) {
  if (!classes || classes.length === 0) {
    console.log('📊 No classes to display in top 3');
    return;
  }

  // Sort by amount descending
  const sortedClasses = [...classes].sort((a, b) =>
    (parseFloat(b.rice_bowl_amount) || 0) - (parseFloat(a.rice_bowl_amount) || 0)
  );

  // Populate top 3
  for (let i = 0; i < 3 && i < sortedClasses.length; i++) {
    const cls = sortedClasses[i];
    const rank = i + 1;

    const nameEl = document.getElementById(`top-${rank}-name`);
    const amountEl = document.getElementById(`top-${rank}-amount`);

    if (nameEl) nameEl.textContent = cls.name || '--';
    if (amountEl) amountEl.textContent = formatCurrency(parseFloat(cls.rice_bowl_amount) || 0);
  }

  console.log('🏆 Top 3 classes populated');
}

/**
 * Update donation thermometer
 */
function updateThermometer(grandTotal) {
  const fillElement = document.getElementById('thermometer-fill');
  const totalElement = document.getElementById('thermometer-total');

  if (!fillElement || !totalElement) return;

  const amount = parseFloat(grandTotal) || 0;

  // Display the amount
  totalElement.textContent = formatCurrency(amount);

  // Calculate fill percentage (cap at 100%)
  // Using a reasonable max of $10,000 for visual scaling, but no hard limit
  const maxForVisual = 10000;
  const fillPercent = Math.min((amount / maxForVisual) * 100, 100);

  // Animate the fill
  setTimeout(() => {
    fillElement.style.height = `${Math.max(fillPercent, 5)}%`; // Minimum 5% so bulb looks connected
  }, 500);

  console.log(`🌡️ Thermometer: ${formatCurrency(amount)} (${fillPercent.toFixed(1)}% fill)`);
}

/**
 * Display grand total (conditionally)
 */
function displayGrandTotal(data, showGrandTotal) {
  const container = document.getElementById('grand-total-section');
  const element = document.getElementById('grand-total');

  if (!container || !element) return;

  // Check if we should show grand total
  const now = new Date();
  const cutoffDate = new Date(CONFIG.GRAND_TOTAL_CUTOFF_DATE);
  const shouldShow = showGrandTotal || now >= cutoffDate;

  if (!shouldShow) {
    container.style.display = 'none';
    console.log('🔒 Grand total hidden (before cutoff date)');
    return;
  }

  // Calculate grand total
  const riceBowlTotal = parseFloat(data.rice_bowl_total) || 0;
  const onlineAlms = parseFloat(data.settings?.online_alms_total) || 0;
  const grandTotal = riceBowlTotal + onlineAlms;

  const formatted = formatCurrency(grandTotal);
  element.textContent = formatted;
  container.style.display = 'block';

  console.log(`💎 Grand total: ${formatted} (Rice Bowl: ${formatCurrency(riceBowlTotal)} + Online: ${formatCurrency(onlineAlms)})`);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Smooth scroll for navigation links
  document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });

        // Update URL hash
        history.pushState(null, null, targetId);

        // Close mobile menu if open
        closeMobileMenu();
      }
    });
  });

  // Mobile menu toggle
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('nav ul');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    // Close menu when clicking a link
    document.querySelectorAll('nav a').forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('nav') && navMenu.classList.contains('active')) {
        closeMobileMenu();
      }
    });
  }

  console.log('🎯 Event listeners setup complete');
}

/**
 * Close mobile menu
 */
function closeMobileMenu() {
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('nav ul');

  if (hamburger && navMenu) {
    hamburger.classList.remove('active');
    navMenu.classList.remove('active');
  }
}

/**
 * Show error message to user
 */
function showError(message) {
  // Try to find error container, create if doesn't exist
  let errorContainer = document.getElementById('error-message');

  if (!errorContainer) {
    errorContainer = document.createElement('div');
    errorContainer.id = 'error-message';
    errorContainer.className = 'error-banner';
    document.body.insertBefore(errorContainer, document.body.firstChild);
  }

  errorContainer.textContent = `⚠️ ${message}`;
  errorContainer.style.display = 'block';

  console.error(`⚠️ Error shown to user: ${message}`);
}

/**
 * UTILITY FUNCTIONS
 */

/**
 * Format number as currency
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Format date string
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date);
}

/**
 * Format countdown from milliseconds
 */
function formatCountdown(ms) {
  const days = Math.floor(ms / (1000 * 60 * 60 * 24));
  const hours = Math.floor((ms % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((ms % (1000 * 60)) / 1000);

  const parts = [];
  if (days > 0) parts.push(`${days} day${days !== 1 ? 's' : ''}`);
  if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? 's' : ''}`);
  if (minutes > 0) parts.push(`${minutes} min`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds} sec`);

  return parts.join(', ');
}

/**
 * Escape HTML to prevent XSS (kept for documentation, not used since we use textContent)
 */
function escapeHtml(str) {
  if (!str) return '';

  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Cleanup function (called on page unload)
 */
function cleanup() {
  if (appState.countdownInterval) {
    clearInterval(appState.countdownInterval);
  }
  if (appState.refreshInterval) {
    clearInterval(appState.refreshInterval);
  }
  console.log('🧹 Cleanup complete');
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', cleanup);

// Expose for debugging (remove in production)
if (typeof window !== 'undefined') {
  window.CRSApp = {
    state: appState,
    config: CONFIG,
    fetchData,
    formatCurrency,
    formatDate,
    formatCountdown
  };
}
