import { useEffect } from 'react';

export const isEditableTarget = node => Boolean(node?.closest?.('input, textarea, select, [contenteditable="true"], [role="combobox"]'));
export const hasOpenDialog = () => Array.from(document.querySelectorAll('[role="dialog"], [role="alertdialog"]')).some(n => n.getAttribute('data-state') !== 'closed' && n.getClientRects().length > 0);

export function usePOSSearchFocus(ref, enabled, lifecycle, appendKey) {
  useEffect(() => {
    if (!enabled) return undefined;
    let timer;
    const focus = () => {
      if (document.visibilityState === 'hidden' || hasOpenDialog()) return;
      const active = document.activeElement;
      if (isEditableTarget(active) && active !== ref.current) return;
      ref.current?.focus({ preventScroll: true });
    };
    const schedule = () => { clearTimeout(timer); timer = setTimeout(focus, 80); };
    const key = e => {
      if (e.defaultPrevented || e.isComposing || e.ctrlKey || e.altKey || e.metaKey || e.key.length !== 1 || hasOpenDialog() || isEditableTarget(document.activeElement)) return;
      focus();
      if (document.activeElement === ref.current) { e.preventDefault(); appendKey(e.key); }
    };
    schedule();
    document.addEventListener('focusout', schedule);
    document.addEventListener('pointerup', schedule);
    document.addEventListener('visibilitychange', schedule);
    window.addEventListener('focus', schedule);
    window.addEventListener('keydown', key, true);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('focusout', schedule);
      document.removeEventListener('pointerup', schedule);
      document.removeEventListener('visibilitychange', schedule);
      window.removeEventListener('focus', schedule);
      window.removeEventListener('keydown', key, true);
    };
  }, [ref, enabled, lifecycle, appendKey]);
}
