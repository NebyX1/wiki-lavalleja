export interface Coordinates {
  lat: number | null;
  lng: number | null;
  confidence: "alta" | "media" | "baja";
  note: string;
}

export interface StreetEvidence {
  status: "confirmada" | "probable" | "a verificar";
  note: string;
}

export interface TimelineEvent {
  year: string;
  event: string;
}

export interface RelatedPlace {
  name: string;
  description: string;
  type: string;
}

export interface Source {
  label: string;
  url: string;
  kind: "oficial" | "institucional" | "biblioteca" | "mapa" | "referencia" | "imagen";
}

export interface ArticleCategory {
  id: number;
  name: string;
  slug: string;
}

export interface ArticleTag {
  id: number;
  name: string;
  slug: string;
}

export interface ArticleSeo {
  title: string;
  description: string | null;
  canonicalUrl: string | null;
}

export interface HeroMedia {
  id: number;
  uuid: string;
  alt: string;
  credit: string;
  caption: string;
}

export interface Article {
  id: number;
  slug: string;
  title: string;
  subtitle: string | null;
  type: string | null;
  streetName: string | null;
  period: string | null;
  birthPlace: string | null;
  deathPlace: string | null;
  category: ArticleCategory | null;
  tags: ArticleTag[];
  summary: string | null;
  heroImage: string | null;
  heroMedia: HeroMedia | null;
  imageAlt: string | null;
  imageCredit: string | null;
  coordinates: Coordinates | null;
  streetEvidence: StreetEvidence | null;
  historicalContext: string | null;
  keyFacts: string[];
  timeline: TimelineEvent[];
  relatedPlaces: RelatedPlace[];
  sources: Source[];
  sourceNotes: string | null;
  body: string | null;
  status: string;
  featured: boolean;
  publishedAt: string | null;
  updatedAt: string | null;
  seo: ArticleSeo;
}