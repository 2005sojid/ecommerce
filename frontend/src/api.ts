import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("access_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    return Promise.reject(err);
  }
);

export type User = { id: string; email: string; name: string; role: "customer" | "admin" | "seller" };

export function getToken() {
  return localStorage.getItem("access_token");
}

export function saveTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export const wishlistApi = {
  list: (page = 1, per_page = 20) => api.get('/wishlist', { params: { page, per_page } }).then(r => r.data),
  ids: () => api.get<string[]>('/wishlist/ids').then(r => r.data),
  add: (product_id: string) => api.post('/wishlist', { product_id }),
  remove: (product_id: string) => api.delete(`/wishlist/${product_id}`),
};

export type Address = {
  id: string; user_id: string; label: string | null;
  recipient_name: string; line1: string; line2: string | null;
  city: string; state: string | null; postal_code: string; country: string;
  phone: string | null; is_default: boolean; created_at: string;
};
export const addressApi = {
  list: () => api.get<Address[]>('/addresses').then(r => r.data),
  create: (data: Partial<Address>) => api.post<Address>('/addresses', data).then(r => r.data),
  update: (id: string, data: Partial<Address>) => api.patch<Address>(`/addresses/${id}`, data).then(r => r.data),
  remove: (id: string) => api.delete(`/addresses/${id}`),
  setDefault: (id: string) => api.post<Address>(`/addresses/${id}/default`).then(r => r.data),
};
export function formatAddress(a: Address): string {
  const parts = [a.recipient_name, a.line1, a.line2, `${a.city}${a.state ? ', ' + a.state : ''} ${a.postal_code}`, a.country, a.phone ? 'Tel: ' + a.phone : null];
  return parts.filter(Boolean).join('\n');
}

export type Notification = {
  id: string; type: string; title: string; body: string | null;
  link: string | null; is_read: boolean; created_at: string;
};
export const notificationsApi = {
  list: (page = 1, per_page = 20, unread_only = false) =>
    api.get('/notifications', { params: { page, per_page, unread_only } }).then(r => r.data),
  unreadCount: () => api.get<{count: number}>('/notifications/unread-count').then(r => r.data.count),
  markRead: (id: string) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post<{updated: number}>('/notifications/read-all').then(r => r.data),
};

export type Seller = { id: string; user_id: string; store_name: string; slug: string; description: string | null; logo_url: string | null; banner_url: string | null; is_verified: boolean; is_active: boolean; created_at: string };
export const sellerApi = {
  register: (data: any) => api.post<Seller>('/sellers/register', data).then(r => r.data),
  me: () => api.get<Seller>('/sellers/me').then(r => r.data),
  update: (data: any) => api.patch<Seller>('/sellers/me', data).then(r => r.data),
  products: (page = 1, per_page = 20) => api.get('/sellers/me/products', { params: { page, per_page } }).then(r => r.data),
  createProduct: (data: any) => api.post('/sellers/me/products', data).then(r => r.data),
  updateProduct: (id: string, data: any) => api.patch(`/sellers/me/products/${id}`, data).then(r => r.data),
  deleteProduct: (id: string) => api.delete(`/sellers/me/products/${id}`),
  orders: (page = 1, per_page = 20) => api.get('/sellers/me/orders', { params: { page, per_page } }).then(r => r.data),
  analytics: () => api.get('/sellers/me/analytics').then(r => r.data),
  publicStore: (slug: string) => api.get<Seller>(`/sellers/${slug}`).then(r => r.data),
  publicProducts: (slug: string, page = 1, per_page = 20) => api.get(`/sellers/${slug}/products`, { params: { page, per_page } }).then(r => r.data),
};

export type Coupon = { id: string; code: string; discount_type: 'percent' | 'fixed'; discount_value: number; scope: 'platform' | 'seller'; seller_id: string | null; min_order_amount: number | null; max_uses: number | null; used_count: number; valid_from: string | null; valid_to: string | null; is_active: boolean; created_at: string };
export const couponsApi = {
  validate: (code: string, order_total: number) => api.post('/coupons/validate', { code, order_total }).then(r => r.data),
  list: (page = 1, per_page = 50) => api.get('/coupons', { params: { page, per_page } }).then(r => r.data),
  create: (data: any) => api.post<Coupon>('/coupons', data).then(r => r.data),
  update: (id: string, data: any) => api.patch<Coupon>(`/coupons/${id}`, data).then(r => r.data),
  remove: (id: string) => api.delete(`/coupons/${id}`),
};

export type ReturnReq = { id: string; order_id: string; user_id: string; status: string; reason: string; refund_amount: number | null; admin_note: string | null; created_at: string };
export const returnsApi = {
  create: (order_id: string, reason: string) => api.post<ReturnReq>('/returns', { order_id, reason }).then(r => r.data),
  list: (page = 1, per_page = 20) => api.get('/returns', { params: { page, per_page } }).then(r => r.data),
  adminList: (page = 1, per_page = 50, status?: string) => api.get('/returns/admin', { params: { page, per_page, status } }).then(r => r.data),
  adminUpdate: (id: string, data: any) => api.patch<ReturnReq>(`/returns/admin/${id}`, data).then(r => r.data),
};

export type Conversation = { id: string; buyer_id: string; seller_id: string; seller_store_name: string | null; buyer_name: string | null; last_message: string | null; last_message_at: string | null; unread_count: number; created_at: string };
export type Message = { id: string; conversation_id: string; sender_user_id: string; body: string; is_read: boolean; created_at: string };
export const chatApi = {
  start: (seller_id: string) => api.post<Conversation>('/chat/conversations', { seller_id }).then(r => r.data),
  conversations: () => api.get<Conversation[]>('/chat/conversations').then(r => r.data),
  messages: (conversation_id: string, page = 1, per_page = 50) => api.get(`/chat/conversations/${conversation_id}/messages`, { params: { page, per_page } }).then(r => r.data),
  send: (conversation_id: string, body: string) => api.post<Message>(`/chat/conversations/${conversation_id}/messages`, { body }).then(r => r.data),
};

export const reviewsApi = {
  vote: (review_id: string, vote: 1 | -1) => api.post<{helpful_count: number}>(`/reviews/${review_id}/vote`, { vote }).then(r => r.data),
  unvote: (review_id: string) => api.delete<{helpful_count: number}>(`/reviews/${review_id}/vote`).then(r => r.data),
  respond: (review_id: string, response: string) => api.post(`/reviews/${review_id}/respond`, { response }).then(r => r.data),
  adminList: (page = 1, per_page = 50, approved?: boolean) => api.get('/reviews/admin', { params: { page, per_page, approved } }).then(r => r.data),
  adminModerate: (review_id: string, is_approved: boolean) => api.patch(`/reviews/admin/${review_id}`, { is_approved }).then(r => r.data),
};

export type ProductImage = { id: string; product_id: string; url: string; alt: string | null; position: number; created_at: string };
export const imagesApi = {
  list: (product_id: string) => api.get<ProductImage[]>(`/products/${product_id}/images`).then(r => r.data),
  add: (product_id: string, data: { url: string; alt?: string | null; position?: number }) => api.post<ProductImage>(`/products/${product_id}/images`, data).then(r => r.data),
  remove: (product_id: string, image_id: string) => api.delete(`/products/${product_id}/images/${image_id}`),
};
export type Category = { id: string; name: string; slug: string; parent_id: string | null };
export const categoriesApi = {
  list: () => api.get<Category[]>('/categories').then(r => r.data),
  create: (data: Partial<Category>) => api.post<Category>('/categories', data).then(r => r.data),
  update: (id: string, data: Partial<Category>) => api.patch<Category>(`/categories/${id}`, data).then(r => r.data),
  remove: (id: string) => api.delete(`/categories/${id}`),
};

export type Settlement = { id: string; seller_id: string; settlement_date: string; gross_revenue: number; fees: number; net_payout: number; order_count: number; created_at: string };
export const settlementsApi = {
  mine: (page = 1, per_page = 30) => api.get<Settlement[]>('/settlements/me', { params: { page, per_page } }).then(r => r.data),
};
