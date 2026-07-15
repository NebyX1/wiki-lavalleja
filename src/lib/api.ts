import axios, { type AxiosInstance } from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api/v1";

const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 15000,
});

export interface PaginationMeta {
  page: number;
  perPage: number;
  total: number;
  pages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface ArticleListResponse {
  items: ArticleSummary[];
  pagination: PaginationMeta;
}

export interface ArticleSummary {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  type: string | null;
  streetName: string | null;
  period: string | null;
  category: { id: number; name: string; slug: string } | null;
  summary: string | null;
  heroImage: string | null;
  imageAlt: string | null;
  tags: { id: number; name: string; slug: string }[];
  status: string;
  featured: boolean;
  publishedAt: string | null;
  updatedAt: string | null;
}

export interface ArticleDetail {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  type: string | null;
  streetName: string | null;
  period: string | null;
  birthPlace: string | null;
  deathPlace: string | null;
  category: { id: number; name: string; slug: string } | null;
  tags: { id: number; name: string; slug: string }[];
  summary: string | null;
  heroImage: string | null;
  heroMedia: { id: number; uuid: string; alt: string; credit: string; caption: string } | null;
  imageAlt: string | null;
  imageCredit: string | null;
  coordinates: { lat: number | null; lng: number | null; confidence: string; note: string } | null;
  streetEvidence: { status: string; note: string } | null;
  historicalContext: string | null;
  keyFacts: string[];
  timeline: { year: string; event: string }[];
  relatedPlaces: { name: string; description: string; type: string }[];
  sources: { label: string; url: string; kind: string }[];
  sourceNotes: string | null;
  body: string | null;
  status: string;
  featured: boolean;
  publishedAt: string | null;
  updatedAt: string | null;
  seo: { title: string; description: string | null; canonicalUrl: string | null };
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  sortOrder: number;
  isActive: boolean;
  articleCount?: number;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
  articleCount?: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: unknown;
    requestId: string;
  };
}

export interface ArticleQueryParams {
  q?: string;
  category?: string;
  type?: string;
  tag?: string;
  featured?: boolean;
  page?: number;
  perPage?: number;
  sort?: "newest" | "oldest" | "title" | "updated";
}

export async function getArticles(params?: ArticleQueryParams): Promise<ArticleListResponse> {
  const res = await client.get<ArticleListResponse>("/articles", { params });
  return res.data;
}

export async function getArticleBySlug(slug: string): Promise<ArticleDetail | null> {
  try {
    const res = await client.get<ArticleDetail>(`/articles/${slug}`);
    return res.data;
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function getCategories(): Promise<Category[]> {
  const res = await client.get<Category[]>("/categories");
  return res.data;
}

export async function getTags(): Promise<Tag[]> {
  const res = await client.get<Tag[]>("/tags");
  return res.data;
}

export function resolveMediaUrl(path: string): string {
  if (path.startsWith("http")) return path;
  const base = API_URL.replace(/\/api\/v1$/, "");
  return `${base}${path}`;
}

export { client as apiClient };