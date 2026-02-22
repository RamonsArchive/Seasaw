"use client";

import { useEffect, useRef, useState } from "react";

export default function Navbar() {
  const [hidden, setHidden] = useState(false);
  const lastScrollY = useRef(0);

  useEffect(() => {
    let ticking = false;

    const onScroll = () => {
      if (ticking) return;
      ticking = true;

      requestAnimationFrame(() => {
        const y = window.scrollY;
        if (y > 60) {
          if (y - lastScrollY.current > 8) setHidden(true);
          else if (lastScrollY.current - y > 8) setHidden(false);
        } else {
          setHidden(false);
        }
        lastScrollY.current = y;
        ticking = false;
      });
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className={`navbar ${hidden ? "navbar-hidden" : ""}`}>
      <div className="navbar-inner">
        <a href="/" className="navbar-logo">
          <span className="navbar-logo-icon">⚖️</span>
          <span className="navbar-logo-text">Seasaw</span>
        </a>
      </div>
    </nav>
  );
}
