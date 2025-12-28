export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'warning' | 'info';
	duration?: number;
}

class ToastStore {
	toasts = $state<Toast[]>([]);

	add(toast: Omit<Toast, 'id'>) {
		const id = crypto.randomUUID();
		const newToast: Toast = { ...toast, id };

		this.toasts = [...this.toasts, newToast];

		// Auto-remove after duration
		const duration = toast.duration ?? 5000;
		if (duration > 0) {
			setTimeout(() => this.remove(id), duration);
		}

		return id;
	}

	remove(id: string) {
		this.toasts = this.toasts.filter((t) => t.id !== id);
	}

	success(message: string, duration?: number) {
		return this.add({ message, type: 'success', duration });
	}

	error(message: string, duration?: number) {
		return this.add({ message, type: 'error', duration });
	}

	warning(message: string, duration?: number) {
		return this.add({ message, type: 'warning', duration });
	}

	info(message: string, duration?: number) {
		return this.add({ message, type: 'info', duration });
	}

	clear() {
		this.toasts = [];
	}
}

export const toasts = new ToastStore();
