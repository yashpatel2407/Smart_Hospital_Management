"""
=============================================================
DATA STRUCTURES - Smart Care Hospital Management System
=============================================================

This module implements core data structures used across the
hospital management system:

1. AppointmentQueue (Queue - FIFO)
   WHERE USED: Managing appointment waiting list. When patients
   book appointments, they enter the queue.

2. sort_appointments (Merge Sort)
   WHERE USED: Sorting appointment lists by date/time/status
   in admin dashboard, doctor panel, and patient views.

3. linear_search_patients (Linear Search)
   WHERE USED: Searching patients by name/email/phone in
   admin patient management and search bar.

4. Session Dictionaries
   WHERE USED: Flask session stores user data as dictionary:
   session = {'user_id': 1, 'role': 'admin', 'full_name': '...'}
   Used across ALL routes for authentication and authorization.
=============================================================
"""


class AppointmentQueue:
    """
    Queue Data Structure (FIFO - First In, First Out)
    for managing the appointment waiting list.

    WHERE USED:
    - Patient books appointment → enqueue()
    - Check queue position → get_position()
    - View waiting list → get_all()

    Internal storage: Python list acting as queue
    """

    def __init__(self):
        self._queue = []  # Internal list to store queue elements

    def enqueue(self, appointment):
        """
        Add an appointment to the END of the queue.
        Called when a patient books a new appointment.

        Args:
            appointment: Dictionary with appointment details
                {id, patient_name, doctor_name, date, time, status}
        """
        self._queue.append(appointment)

    def is_empty(self):
        """Check if the queue has no appointments"""
        return len(self._queue) == 0

    def size(self):
        """Return the number of appointments in the queue"""
        return len(self._queue)

    def get_all(self):
        """
        Return all appointments in queue order (list copy).
        Used to display the full waiting list on dashboards.
        """
        return list(self._queue)

    def get_position(self, appointment_id):
        """
        Find the position of an appointment in the queue.
        Used to show patients their queue position.

        Args:
            appointment_id: Integer ID of the appointment

        Returns:
            Position (1-indexed) or -1 if not found
        """
        for i, apt in enumerate(self._queue):
            if apt.get('id') == appointment_id:
                return i + 1  # 1-indexed position
        return -1

    def remove(self, appointment_id):
        """
        Remove a specific appointment from the queue (cancellation).

        Args:
            appointment_id: Integer ID of the appointment to remove

        Returns:
            True if removed, False if not found
        """
        for i, apt in enumerate(self._queue):
            if apt.get('id') == appointment_id:
                self._queue.pop(i)
                return True
        return False

    def __len__(self):
        return len(self._queue)

    def __repr__(self):
        return f"AppointmentQueue(size={self.size()})"


# ── Merge Sort ─────────────────────────────────────────────

def sort_appointments(appointments, key='appointment_date', reverse=False):
    """
    Merge Sort implementation for sorting appointment lists.

    WHERE USED:
    - Admin dashboard: Sort appointments by date, status, or doctor
    - Doctor panel: Sort today's appointments by time
    - Patient view: Sort appointment history by date (newest first)

    Time Complexity: O(n log n) - efficient for large appointment lists
    Space Complexity: O(n)

    Args:
        appointments: List of appointment dictionaries
        key: Dictionary key to sort by (e.g., 'appointment_date',
             'appointment_time', 'status', 'patient_name')
        reverse: If True, sort descending (newest first)

    Returns:
        New sorted list of appointment dictionaries
    """
    if len(appointments) <= 1:
        return list(appointments)

    mid = len(appointments) // 2
    left_half = sort_appointments(appointments[:mid], key, reverse)
    right_half = sort_appointments(appointments[mid:], key, reverse)

    return _merge(left_half, right_half, key, reverse)


def _merge(left, right, key, reverse):
    """
    Helper function for merge sort - merges two sorted halves.

    Args:
        left: Left sorted sub-list
        right: Right sorted sub-list
        key: Dictionary key to compare
        reverse: Sort direction

    Returns:
        Merged sorted list
    """
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        left_val = str(left[i].get(key, ''))
        right_val = str(right[j].get(key, ''))

        if reverse:
            if left_val >= right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        else:
            if left_val <= right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

    # Append remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ── Linear Search ──────────────────────────────────────────

def linear_search_patients(patients, search_term):
    """
    Linear Search to find patients by name, email, or phone.

    WHERE USED:
    - Admin dashboard search bar: Real-time patient search
    - Doctor panel: Finding patients for prescription
    - Patient management: Filtering patient list

    Time Complexity: O(n) - checks each patient record
    Suitable for: Flexible multi-field text search

    Args:
        patients: List of patient dictionaries
        search_term: String to search for (case-insensitive)

    Returns:
        List of matching patient dictionaries
    """
    results = []
    search_lower = search_term.lower().strip()

    if not search_lower:
        return patients

    for patient in patients:
        name = patient.get('full_name', '').lower()
        email = patient.get('email', '').lower()
        phone = str(patient.get('phone', ''))

        if (search_lower in name or
                search_lower in email or
                search_lower in phone):
            results.append(patient)

    return results


# ── Global Queue Instance ──────────────────────────────────
# Single queue instance shared across the application
# Populated from database on app startup / route access

appointment_queue = AppointmentQueue()
