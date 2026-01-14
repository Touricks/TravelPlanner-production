import { useEffect, useMemo, useRef } from "react";

/**
 * Debounce a function with a stable reference.
 * Calls are delayed by `delay` ms; only the last one runs.
 * Latest `fn` is always used.
 * Pending timer is cleared on unmount or when `delay` changes.
 */
export default function useDebounced(fn, delay = 250) {
  const fnRef = useRef(fn);
  const timerRef = useRef(null);

  // keep the latest function
  useEffect(() => {
    fnRef.current = fn;
  }, [fn]);

  // clear on unmount / delay change
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [delay]);

  // stable debounced callback
  return useMemo(() => {
    const debounced = (...args) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => fnRef.current(...args), delay);
    };
    debounced.cancel = () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
    return debounced;
  }, [delay]);
}
