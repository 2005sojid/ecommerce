import { useState } from "react";
import { Link } from "react-router-dom";

type Product = {
  id: string;
  name: string;
  description: string | null;
  price: number | string;
  image_url: string | null;
  category_name?: string | null;
  seller_slug?: string | null;
  seller_store_name?: string | null;
  seller_is_verified?: boolean | null;
};

const ICON_PATHS: Record<string, string> = {
  Electronics:
    "M3 6h18v10H3zM2 18h20M9 22h6",
  Clothing:
    "M8 3l-5 4 2 3 3-2v14h8V8l3 2 2-3-5-4-3 1.5L11 5z",
  "Home & Kitchen":
    "M3 10l9-7 9 7v11H3zM10 21v-7h4v7",
  Sports:
    "M12 4a8 8 0 1 0 8 8M12 4a8 8 0 0 1 8 8M4 12c1 4 4 7 8 8M20 12c-1 4-4 7-8 8M12 4v16M4 12h16",
  Books:
    "M4 5a2 2 0 0 1 2-2h5v18H6a2 2 0 0 1-2-2zM13 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5z",
  Cameras:
    "M3 7h4l2-3h6l2 3h4v13H3zM12 11a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z",
  Toys:
    "M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM8 11h.01M16 11h.01M9 15c1 1 2 1.5 3 1.5s2-.5 3-1.5",
  Beauty:
    "M9 3h6l-1 5h-4zM10 8h4l1 13H9z",
};
const DEFAULT_ICON = "M4 7h16l-1 13H5zM8 7V5a4 4 0 0 1 8 0v2";

function iconUrl(category: string | null | undefined): string {
  const d = (category && ICON_PATHS[category]) || DEFAULT_ICON;
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238b91a1' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><path d='${d}'/></svg>`;
  return `url("data:image/svg+xml;utf8,${svg}")`;
}

export default function ProductCard({
  product,
  wishlisted,
  onWishlistToggle,
  featured,
}: {
  product: Product;
  wishlisted?: boolean;
  onWishlistToggle?: () => void;
  featured?: boolean;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImage = !!product.image_url && !imgFailed;

  const onHeart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onWishlistToggle?.();
  };

  return (
    <Link to={`/products/${product.id}`} className="product-card">
      <div
        className="product-image"
        style={
          !showImage
            ? {
                backgroundImage: iconUrl(product.category_name),
                backgroundRepeat: "no-repeat",
                backgroundPosition: "center",
                backgroundSize: "38%",
              }
            : undefined
        }
      >
        {featured && <span className="featured-corner">Featured</span>}
        {showImage && (
          <img
            src={product.image_url!}
            alt={product.name}
            onError={() => setImgFailed(true)}
            loading="lazy"
          />
        )}
        {onWishlistToggle && (
          <button className="wishlist-heart" onClick={onHeart} aria-label="Toggle wishlist">
            <svg width="18" height="18" viewBox="0 0 24 24" fill={wishlisted ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        )}
      </div>
      <div className="product-body">
        {product.seller_store_name && product.seller_slug ? (
          <Link
            to={`/store/${product.seller_slug}`}
            onClick={(e) => e.stopPropagation()}
            className="seller-chip"
          >
            {product.seller_is_verified && (
              <svg className="verified-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="m8 12 3 3 5-6" />
              </svg>
            )}
            {product.seller_store_name}
          </Link>
        ) : (
          <span className="seller-chip muted">Marketplace</span>
        )}
        <strong>{product.name}</strong>
        <div className="muted product-desc">{product.description?.slice(0, 60)}…</div>
        <div className="price">${product.price}</div>
      </div>
    </Link>
  );
}
