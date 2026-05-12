import { useEffect, useState } from "react";

export type CarouselImage = { url: string; alt?: string | null };

export default function Carousel({ images, fallbackAlt }: { images: CarouselImage[]; fallbackAlt?: string }) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (active >= images.length) setActive(0);
  }, [images, active]);

  if (images.length === 0) return null;

  const prev = (e?: React.MouseEvent) => {
    e?.preventDefault();
    setActive((i) => (i - 1 + images.length) % images.length);
  };
  const next = (e?: React.MouseEvent) => {
    e?.preventDefault();
    setActive((i) => (i + 1) % images.length);
  };
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") prev();
    if (e.key === "ArrowRight") next();
  };

  return (
    <div className="carousel" tabIndex={0} onKeyDown={onKey} aria-label="Product image carousel">
      <div className="carousel-stage">
        <img
          src={images[active].url}
          alt={images[active].alt || fallbackAlt || ""}
          onError={(e) => { (e.target as HTMLImageElement).style.opacity = "0.25"; }}
        />
        {images.length > 1 && (
          <>
            <button type="button" className="carousel-nav prev" onClick={prev} aria-label="Previous image">‹</button>
            <button type="button" className="carousel-nav next" onClick={next} aria-label="Next image">›</button>
            <div className="carousel-dots">
              {images.map((_, i) => (
                <button
                  key={i}
                  type="button"
                  className={`carousel-dot ${i === active ? "active" : ""}`}
                  onClick={(e) => { e.preventDefault(); setActive(i); }}
                  aria-label={`Go to image ${i + 1}`}
                />
              ))}
            </div>
          </>
        )}
      </div>
      {images.length > 1 && (
        <div className="carousel-thumbs">
          {images.map((img, i) => (
            <button
              key={i}
              type="button"
              className={`carousel-thumb ${i === active ? "active" : ""}`}
              onClick={(e) => { e.preventDefault(); setActive(i); }}
            >
              <img src={img.url} alt={img.alt || ""} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
