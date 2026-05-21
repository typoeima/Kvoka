function startTimer() {
    if (timer) return;
    
    // Добавляем анимацию пульсации
    const timerCard = document.querySelector('.timer-card');
    timerCard.classList.add('active-focus');
    
    timer = setInterval(() => {
        if (timeLeft <= 0) {
            clearInterval(timer);
            timer = null;
            isRunning = false;
            
            // Убираем анимацию пульсации
            timerCard.classList.remove('active-focus');
            timerCard.classList.remove('active-break');
            
            // Добавляем анимацию завершения
            timerCard.classList.add('timer-complete');
            setTimeout(() => {
                timerCard.classList.remove('timer-complete');
            }, 500);
            
            if (currentMode === 'focus') {
                const plan = planText.value;
                const done = planDone.checked;
                const sessionMinutes = focusMinutes;
                saveSessionToServer(sessionMinutes, plan, done);
                
                // Показываем красивое уведомление вместо alert
                showNotification('✅ Фокус завершён! Время перерыва ☕', 'success');
                
                setMode('break');
                timerCard.classList.remove('active-focus');
                timerCard.classList.add('active-break');
                startBtn.disabled = false;
                pauseBtn.disabled = true;
                warningMsg.style.display = 'none';
                isRunning = false;
                timer = null;
                startTimer(); // Автоматически запускаем перерыв
            } else {
                showNotification('✨ Перерыв окончен! Готов к новому фокусу?', 'info');
                setMode('focus');
                startBtn.disabled = false;
                pauseBtn.disabled = true;
                warningMsg.style.display = 'none';
                isRunning = false;
                timer = null;
            }
        } else {
            timeLeft--;
            updateDisplay();
        }
    }, 1000);
    
    isRunning = true;
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    warningMsg.style.display = 'flex';
}

function pauseTimer() {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
    isRunning = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    warningMsg.style.display = 'none';
    
    // Убираем анимацию пульсации
    const timerCard = document.querySelector('.timer-card');
    timerCard.classList.remove('active-focus');
    timerCard.classList.remove('active-break');
}

function resetTimer() {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
    isRunning = false;
    setMode('focus');
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    warningMsg.style.display = 'none';
    
    // Убираем анимацию пульсации
    const timerCard = document.querySelector('.timer-card');
    timerCard.classList.remove('active-focus');
    timerCard.classList.remove('active-break');
}

// Красивое уведомление вместо alert
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    let icon = '✅';
    let bgColor = '#FF9F66';
    
    if (type === 'success') {
        icon = '✅';
        bgColor = '#10b981';
    } else if (type === 'info') {
        icon = '✨';
        bgColor = '#FF9F66';
    } else if (type === 'warning') {
        icon = '⚠️';
        bgColor = '#f59e0b';
    }
    
    notification.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: ${bgColor};
        color: white;
        padding: 14px 24px;
        border-radius: 2rem;
        font-size: 0.9rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
    `;
    
    notification.innerHTML = `<span style="font-size: 1.2rem;">${icon}</span> ${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
    
    notification.addEventListener('click', () => notification.remove());
}

// Анимация обновления стрика
function updateStreakDisplay() {
    fetch('/api/get-user-stats/')
        .then(response => response.json())
        .then(data => {
            const streakBadge = document.querySelector('.timer-status .status-badge:first-child strong');
            if (streakBadge) {
                streakBadge.classList.add('streak-update');
                streakBadge.textContent = data.current_days;
                setTimeout(() => {
                    streakBadge.classList.remove('streak-update');
                }, 400);
            }
        });
}