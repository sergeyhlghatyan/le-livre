/**
 * Diff Navigator - Navigate between changes in comparison view
 *
 * Features:
 * - Next/Previous buttons
 * - Keyboard shortcuts (Arrow keys or n/p)
 * - Visual highlighting of current diff
 * - Skips unchanged rows
 * - Counter display
 */

class DiffNavigator {
    constructor() {
        // Get all diff rows that are NOT unchanged
        this.diffs = Array.from(document.querySelectorAll('.diff-row'))
            .filter(row => !row.classList.contains('unchanged'));

        this.currentIndex = 0;

        if (this.diffs.length === 0) {
            console.log('No diffs found on page');
            return;
        }

        this.setupEventListeners();
        this.updateCounter();
        this.highlightCurrent();
    }

    setupEventListeners() {
        const nextBtn = document.getElementById('next-diff');
        const prevBtn = document.getElementById('prev-diff');

        if (!nextBtn || !prevBtn) {
            console.error('Navigation buttons not found');
            return;
        }

        nextBtn.addEventListener('click', () => this.next());
        prevBtn.addEventListener('click', () => this.prev());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Don't interfere if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            if (e.key === 'ArrowDown' || e.key === 'n') {
                e.preventDefault();
                this.next();
            } else if (e.key === 'ArrowUp' || e.key === 'p') {
                e.preventDefault();
                this.prev();
            }
        });
    }

    next() {
        if (this.currentIndex < this.diffs.length - 1) {
            this.currentIndex++;
            this.scrollToCurrent();
        }
    }

    prev() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.scrollToCurrent();
        }
    }

    scrollToCurrent() {
        const current = this.diffs[this.currentIndex];

        // Remove highlight from all
        this.diffs.forEach(d => d.classList.remove('current-diff'));

        // Highlight current
        current.classList.add('current-diff');

        // Scroll into view with smooth animation
        current.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        this.updateCounter();
    }

    highlightCurrent() {
        const current = this.diffs[this.currentIndex];
        if (current) {
            current.classList.add('current-diff');
        }
    }

    updateCounter() {
        const counter = document.getElementById('diff-counter');
        if (counter) {
            counter.textContent = `Diff ${this.currentIndex + 1} of ${this.diffs.length}`;
        }

        // Disable buttons at boundaries
        const prevBtn = document.getElementById('prev-diff');
        const nextBtn = document.getElementById('next-diff');

        if (prevBtn) {
            prevBtn.disabled = this.currentIndex === 0;
        }

        if (nextBtn) {
            nextBtn.disabled = this.currentIndex === this.diffs.length - 1;
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new DiffNavigator();
});
