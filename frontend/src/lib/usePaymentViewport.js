import { useEffect, useState } from 'react';

// visualViewport also handles the space remaining above a mobile software keyboard.
export function usePaymentViewport(open) {
  const [style, setStyle] = useState({});
  useEffect(() => {
    if (!open) return undefined;
    const viewport = window.visualViewport;
    const update = () => {
      const height = viewport?.height || window.innerHeight;
      const width = viewport?.width || window.innerWidth;
      setStyle({
        '--payment-viewport-height': `${height}px`,
        '--payment-viewport-width': `${width}px`,
        '--payment-top': `${(viewport?.offsetTop || 0) + height / 2}px`,
        '--payment-left': `${(viewport?.offsetLeft || 0) + width / 2}px`,
      });
    };
    update();
    window.addEventListener('resize', update);
    viewport?.addEventListener('resize', update);
    viewport?.addEventListener('scroll', update);
    return () => {
      window.removeEventListener('resize', update);
      viewport?.removeEventListener('resize', update);
      viewport?.removeEventListener('scroll', update);
    };
  }, [open]);
  return style;
}
