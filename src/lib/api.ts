import axios from "axios";
import type { Article } from "../types/article";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

const client = axios.create({
  baseURL: API_URL,
});

export async function getArticles(): Promise<Article[]> {
  const { data } = await client.get<Article[]>("/articles");
  return data;
}

export async function getArticleBySlug(slug: string): Promise<Article | null> {
  const { data } = await client.get<Article[]>("/articles", {
    params: { slug },
  });
  return data.length > 0 ? data[0] : null;
}
