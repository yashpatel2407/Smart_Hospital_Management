/**
 * ═══════════════════════════════════════════════════════════
 * MAIN.JS - SmartCare Hospital Management System
 * Sidebar toggle, search, and global UI interactions
 * ═══════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar Toggle (Mobile) ───────────────────────────
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // ── Auto-dismiss Alerts ───────────────────────────────
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Smooth stat card animation on load ────────────────
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(function (card, index) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(function () {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });

    // ── Dashboard table row animation ─────────────────────
    const tableRows = document.querySelectorAll('.dashboard-table tbody tr');
    tableRows.forEach(function (row, index) {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-10px)';
        setTimeout(function () {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, 200 + (index * 50));
    });

    // ── Global Search (basic client-side filter) ──────────
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase().trim();
            const tables = document.querySelectorAll('.dashboard-table tbody');
            tables.forEach(function (tbody) {
                const rows = tbody.querySelectorAll('tr');
                rows.forEach(function (row) {
                    const text = row.textContent.toLowerCase();
                    if (query === '' || text.includes(query)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });
    }
});
