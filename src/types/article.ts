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

export interface Article {
  id: string;
  slug: string;
  title: string;
  subtitle: string;
  type: string;
  streetName: string;
  period: string;
  birthPlace: string;
  deathPlace: string;
  category: string;
  tags: string[];
  summary: string;
  heroImage: string;
  imageAlt: string;
  imageCredit: string;
  coordinates: Coordinates;
  streetEvidence: StreetEvidence;
  historicalContext: string;
  keyFacts: string[];
  timeline: TimelineEvent[];
  relatedPlaces: RelatedPlace[];
  sources: Source[];
  sourceNotes: string;
  body: string;
}
