/**
 * ═══════════════════════════════════════════════════════════
 * AI_CHATBOT.JS - Medical Chatbot Functionality
 * ═══════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', function () {
    const chatToggle = document.getElementById('chatToggle');
    const chatContainer = document.getElementById('chatContainer');
    const chatBody = document.getElementById('chatBody');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatMinimize = document.getElementById('chatMinimize');
    const typingIndicator = document.getElementById('typingIndicator');

    // Toggle Chat
    if (chatToggle) {
        chatToggle.addEventListener('click', () => {
            chatContainer.classList.toggle('active');
            if (chatContainer.classList.contains('active')) {
                chatInput.focus();
            }
        });
    }

    // Minimize Chat
    if (chatMinimize) {
        chatMinimize.addEventListener('click', (e) => {
            e.stopPropagation();
            chatContainer.classList.remove('active');
        });
    }

    // Send Message Function
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add User Message to UI
        appendMessage('user', message);
        chatInput.value = '';

        // Show Typing Indicator
        typingIndicator.style.display = 'block';
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            const response = await fetch('/patient/ai-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            // Hide Typing Indicator
            typingIndicator.style.display = 'none';

            // Add AI Response to UI
            appendMessage('ai', data.response);
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            appendMessage('ai', "Sorry, I'm having trouble connecting to the server. Please try again later.");
        }

        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Append Message to UI
    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'message-user' : 'message-ai');

        // Advanced Markdown-like formatting for AI responses
        if (sender === 'ai' || sender === 'bot') {
            if (text.includes('[[INTENT:BOOKING]]')) {
                renderBookingFlow(msgDiv);
            } else {
                let formattedText = text;
                // Headers # Title
                formattedText = formattedText.replace(/^# (.*$)/gim, '<h4 class="fw-bold text-primary mt-2 mb-1">$1</h4>');
                // Headers ### Title
                formattedText = formattedText.replace(/^### (.*$)/gim, '<h6 class="fw-bold text-dark mt-2 mb-1">$1</h6>');
                // Bold **text**
                formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                // Lists - Item
                formattedText = formattedText.replace(/^- (.*$)/gim, '<div class="ms-3 mb-1">• $1</div>');
                // New lines to <br>
                formattedText = formattedText.replace(/\n/g, '<br>');
                msgDiv.innerHTML = formattedText;
            }
        } else {
            msgDiv.textContent = text;
        }

        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    /* ════ Interactive Booking Engine ════ */
    async function renderBookingFlow(container) {
        container.innerHTML = `
            <div class="booking-flow" style="min-width: 220px;">
                <h6 class="fw-bold text-primary mb-3"><i class="bi bi-calendar-check me-2"></i>AI Booking</h6>
                <div id="bookingContent">
                    <p class="small text-muted mb-2">Identify Specialist:</p>
                    <select id="botDrSelect" class="form-select form-select-sm mb-3 border-0 bg-light" style="border-radius: 8px;">
                        <option value="">Loading doctors...</option>
                    </select>
                </div>
            </div>
        `;

        try {
            const resp = await fetch('/patient/api/doctors/list');
            const doctors = await resp.json();
            const select = container.querySelector('#botDrSelect');
            select.innerHTML = '<option value="">Choose physician</option>';
            doctors.forEach(d => {
                select.innerHTML += `<option value="${d.id}">Dr. ${d.full_name} (${d.specialization})</option>`;
            });

            select.addEventListener('change', () => {
                if (select.value) {
                    const drName = select.options[select.selectedIndex].text;
                    renderDateStep(container, select.value, drName);
                }
            });
        } catch (e) {
            container.innerHTML = '<span class="text-danger small">Error loading staff list.</span>';
        }
    }

    async function renderDateStep(container, drId, drName) {
        const content = container.querySelector('#bookingContent');
        content.innerHTML = '<div class="text-center py-2"><div class="spinner-border spinner-border-sm text-primary"></div></div>';

        let leaveDates = [];
        try {
            const resp = await fetch(`/patient/api/doctors/unavailability?doctor_id=${drId}`);
            leaveDates = await resp.json();
        } catch (e) { console.error(e); }

        content.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3 bg-light p-2 rounded" style="font-size: 0.85rem; border: 1px solid rgba(0,0,0,0.05);">
                <span class="text-primary fw-bold"><i class="bi bi-person-check-fill me-1"></i> ${drName}</span>
                <button id="changeDrBtn" class="btn btn-link btn-sm p-0 text-decoration-none fw-bold" style="font-size: 0.75rem;">Change</button>
            </div>
            
            <div id="leaveAlert" class="alert alert-warning p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-briefcase-fill me-1"></i> ${drName.split('(')[0].trim()} is on leave this day.
            </div>

            <div id="weekendAlert" class="alert alert-warning p-2 small mb-2 d-none" style="border-radius: 8px;">
                <i class="bi bi-clock-history me-1"></i> Hospital is closed on Sundays.
            </div>

            <div id="pastDateAlert" class="alert alert-danger p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-calendar-x me-1"></i> Appointment date cannot be in the past.
            </div>

            <p class="small text-muted mb-2">Select your visit date:</p>
            <input type="date" id="botDateInput" class="form-control form-control-sm mb-3 border-0 bg-light" 
                min="${(() => {
                const now = new Date();
                return `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, '0')}-${now.getDate().toString().padStart(2, '0')}`;
            })()}" style="border-radius: 8px;">
        `;

        content.querySelector('#changeDrBtn').addEventListener('click', () => {
            renderBookingFlow(container);
        });

        const dateInput = content.querySelector('#botDateInput');
        const leaveAlert = content.querySelector('#leaveAlert');
        const weekendAlert = content.querySelector('#weekendAlert');
        const pastDateAlert = content.querySelector('#pastDateAlert');

        dateInput.addEventListener('change', () => {
            if (dateInput.value) {
                const now = new Date();
                now.setHours(0, 0, 0, 0);
                const selectedDate = new Date(dateInput.value);
                selectedDate.setHours(0, 0, 0, 0);

                const day = selectedDate.getDay(); // 0 = Sunday, 6 = Saturday

                // Reset all alerts
                pastDateAlert.classList.add('d-none');
                weekendAlert.classList.add('d-none');
                leaveAlert.classList.add('d-none');

                if (selectedDate < now) {
                    pastDateAlert.classList.remove('d-none');
                } else if (day === 0) { // Sunday
                    weekendAlert.classList.remove('d-none');
                } else if (leaveDates.includes(dateInput.value)) {
                    leaveAlert.classList.remove('d-none');
                } else {
                    renderTimeStep(container, drId, dateInput.value, drName);
                }
            }
        });
    }

    async function renderTimeStep(container, drId, date, drName) {
        const content = container.querySelector('#bookingContent');
        content.innerHTML = '<div class="text-center py-2"><div class="spinner-border spinner-border-sm text-primary"></div></div>';

        let bookedSlots = [];
        try {
            const resp = await fetch(`/patient/api/appointments/booked_slots?doctor_id=${drId}&date=${date}`);
            bookedSlots = await resp.json();
            // Convert '09:00:00' to '09:00' for easier comparison
            bookedSlots = bookedSlots.map(s => s.substring(0, 5));
        } catch (e) { console.error("Could not fetch booked slots"); }

        content.innerHTML = `
            <div class="mb-2 bg-light p-2 rounded" style="font-size: 0.85rem; border: 1px solid rgba(0,0,0,0.05);">
                <div class="d-flex justify-content-between">
                    <span class="text-primary fw-bold"><i class="bi bi-person-check-fill me-1"></i> ${drName}</span>
                    <button id="changeDrBtn" class="btn btn-link btn-sm p-0 text-decoration-none fw-bold" style="font-size: 0.75rem;">Change</button>
                </div>
                <div class="d-flex justify-content-between mt-1 pt-1 border-top border-white">
                    <span class="text-primary fw-bold"><i class="bi bi-calendar-check-fill me-1"></i> ${date}</span>
                    <button id="changeDateBtn" class="btn btn-link btn-sm p-0 text-decoration-none fw-bold" style="font-size: 0.75rem;">Change</button>
                </div>
            </div>
            
            <div id="gapAlert" class="alert alert-danger p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-hourglass-split me-1"></i> Conflict: Doctor needs a 1-hour buffer between visits. 
            </div>

            <div id="bookingAlert" class="alert alert-danger p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-exclamation-triangle-fill me-1"></i> This time is already booked.
            </div>

            <div id="hospitalHoursAlert" class="alert alert-warning p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-clock-history me-1"></i> Hospital hours: 08:00 AM - 08:00 PM.
            </div>

            <div id="pastTimeAlert" class="alert alert-danger p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-clock-fill me-1"></i> Appointment time cannot be in the past.
            </div>

            <div id="sundayAlert" class="alert alert-warning p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-calendar-x me-1"></i> Sunday Hospital is closed.
            </div>

            <p class="small text-muted mb-2">Preferred time slot:</p>
            <input type="time" id="botTimeInput" class="form-control form-control-sm mb-3 border-0 bg-light" 
                min="08:00" max="20:00" value="09:00" style="border-radius: 8px;">
            <p id="bookedSlotsInfo" class="x-small text-muted mb-3 ${bookedSlots.length ? '' : 'd-none'}" style="font-size: 0.7rem;">
                <i class="bi bi-info-circle me-1"></i> Booked: ${bookedSlots.join(', ')}
            </p>
            <button id="botConfirmBtn" class="btn btn-primary btn-sm w-100 py-2 mt-2" style="border-radius: 8px; font-weight: 600;">
                Finalize Booking
            </button>
        `;

        const timeInput = content.querySelector('#botTimeInput');
        const alertDiv = content.querySelector('#bookingAlert');
        const gapAlert = content.querySelector('#gapAlert');
        const pastTimeAlert = content.querySelector('#pastTimeAlert');
        const sundayAlert = content.querySelector('#sundayAlert');
        const hoursAlert = content.querySelector('#hospitalHoursAlert');
        const confirmBtn = content.querySelector('#botConfirmBtn');

        // Helper to check if time is in past for today
        const checkPastTime = (selectedTime) => {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const todayStr = `${year}-${month}-${day}`;

            if (date === todayStr) {
                const nowTime = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');
                return selectedTime < nowTime;
            }
            return false;
        };

        const validate = () => {
            const timeVal = timeInput.value;
            const selectSec = timeToSec(timeVal);
            const isOutsideHours = timeVal < "08:00" || timeVal > "20:00";
            const isBooked = bookedSlots && bookedSlots.includes(timeVal);
            const isPast = checkPastTime(timeVal);

            // Check for 1-hour gap (3600 seconds)
            let hasGapConflict = false;
            if (bookedSlots && bookedSlots.length > 0) {
                hasGapConflict = bookedSlots.some(slot => {
                    const slotSec = timeToSec(slot);
                    return Math.abs(selectSec - slotSec) < 3600;
                });
            }

            // Helper to convert HH:mm to seconds
            function timeToSec(t) {
                const [h, m] = t.split(':').map(Number);
                return h * 3600 + m * 60;
            }

            // Reset all alerts
            hoursAlert && hoursAlert.classList.add('d-none');
            alertDiv && alertDiv.classList.add('d-none');
            gapAlert && gapAlert.classList.add('d-none');
            pastTimeAlert && pastTimeAlert.classList.add('d-none');
            sundayAlert && sundayAlert.classList.add('d-none');
            if (confirmBtn) confirmBtn.disabled = false;

            const isSunday = new Date(date).getUTCDay() === 0;

            if (isSunday) {
                sundayAlert && sundayAlert.classList.remove('d-none');
                if (confirmBtn) confirmBtn.disabled = true;
            } else if (isOutsideHours) {
                hoursAlert && hoursAlert.classList.remove('d-none');
                if (confirmBtn) confirmBtn.disabled = true;
            } else if (isPast) {
                pastTimeAlert && pastTimeAlert.classList.remove('d-none');
                if (confirmBtn) confirmBtn.disabled = true;
            } else if (isBooked) {
                alertDiv && alertDiv.classList.remove('d-none');
                if (confirmBtn) confirmBtn.disabled = true;
            } else if (hasGapConflict) {
                gapAlert && gapAlert.classList.remove('d-none');
                if (confirmBtn) confirmBtn.disabled = true;
            }
        };

        if (timeInput) {
            timeInput.addEventListener('input', validate);
            timeInput.addEventListener('change', validate);
        }

        // Auto-adjust default time if today
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;

        if (date === todayStr) {
            const currentHour = now.getHours();
            const currentMin = now.getMinutes();
            // Round up to next 15 mins for better UX
            let targetHour = currentHour;
            let targetMin = Math.ceil(currentMin / 15) * 15;
            if (targetMin >= 60) {
                targetHour++;
                targetMin = 0;
            }

            const autoTime = targetHour.toString().padStart(2, '0') + ":" + targetMin.toString().padStart(2, '0');

            // Only update if current time is past the default 09:00
            if (autoTime > "09:00" && autoTime < "20:00") {
                timeInput.value = autoTime;
                timeInput.min = autoTime;
            } else if (autoTime >= "20:00") {
                // Past hospital hours
                confirmBtn.disabled = true;
                hoursAlert.classList.remove('d-none');
            }
        }

        validate(); // Initial check

        content.querySelector('#changeDrBtn').addEventListener('click', () => {
            renderBookingFlow(container);
        });

        content.querySelector('#changeDateBtn').addEventListener('click', () => {
            renderDateStep(container, drId, drName);
        });

        confirmBtn.addEventListener('click', () => {
            renderReasonStep(container, drId, date, timeInput.value, drName);
        });
    }

    function renderReasonStep(container, drId, date, time, drName) {
        const content = container.querySelector('#bookingContent');
        content.innerHTML = `
            <div class="mb-2 bg-light p-2 rounded" style="font-size: 0.85rem; border: 1px solid rgba(0,0,0,0.05);">
                <div class="d-flex justify-content-between">
                    <span class="text-primary fw-bold"><i class="bi bi-person-check-fill me-1"></i> ${drName}</span>
                    <button id="changeDrBtn" class="btn btn-link btn-sm p-0 text-decoration-none fw-bold" style="font-size: 0.75rem;">Change</button>
                </div>
                <div class="d-flex justify-content-between mt-1 pt-1 border-top border-white">
                    <span class="text-primary fw-bold"><i class="bi bi-clock-fill me-1"></i> ${date} @ ${time}</span>
                    <button id="changeTimeBtn" class="btn btn-link btn-sm p-0 text-decoration-none fw-bold" style="font-size: 0.75rem;">Change</button>
                </div>
            </div>

            <div id="reasonAlert" class="alert alert-danger p-2 mb-2 small d-none" style="border-radius: 8px;">
                <i class="bi bi-exclamation-circle-fill me-1"></i> Reason for visit is mandatory.
            </div>

            <p class="small text-muted mb-2">Reason for Visit:</p>
            <textarea id="botReasonInput" class="form-control form-control-sm mb-3 border-0 bg-light" 
                placeholder="Briefly describe your symptoms or reason for visit..." rows="3" style="border-radius: 8px; font-size: 0.85rem;"></textarea>

            <button id="botFinalizeBtn" class="btn btn-primary btn-sm w-100 py-2 mt-2" style="border-radius: 8px; font-weight: 600;">
                Confirm & Secure Slot
            </button>
        `;

        content.querySelector('#changeDrBtn').addEventListener('click', () => renderBookingFlow(container));
        content.querySelector('#changeTimeBtn').addEventListener('click', () => renderDateStep(container, drId, drName));

        content.querySelector('#botFinalizeBtn').addEventListener('click', async () => {
            const reason = content.querySelector('#botReasonInput').value.trim();
            const alertDiv = content.querySelector('#reasonAlert');

            if (!reason) {
                alertDiv.classList.remove('d-none');
                return;
            }
            alertDiv.classList.add('d-none');

            content.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary mb-2"></div><div class="small">Processing...</div></div>';

            const formData = new FormData();
            formData.append('doctor_id', drId);
            formData.append('appointment_date', date);
            formData.append('appointment_time', time);
            formData.append('reason', reason);

            try {
                const resp = await fetch('/patient/appointments/book', {
                    method: 'POST',
                    body: formData
                });

                if (resp.redirected) {
                    content.innerHTML = '<div class="text-success small fw-bold text-center py-2"><i class="bi bi-check-circle-fill me-1"></i> Appointment Secured!</div>';
                    setTimeout(() => window.location.href = resp.url, 1500);
                } else {
                    content.innerHTML = '<div class="text-danger small text-center">Slot unavailable. Please try another time.</div>';
                }
            } catch (e) {
                content.innerHTML = '<div class="text-danger small text-center">System unreachable.</div>';
            }
        });
    }

    // Event Listeners
    if (chatSend) {
        chatSend.addEventListener('click', sendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
