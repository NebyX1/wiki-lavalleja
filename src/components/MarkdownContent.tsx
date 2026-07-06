import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { slugify } from "../lib/utils";

interface MarkdownContentProps {
  content: string;
}

function Heading({ level, children }: { level: 2 | 3; children: React.ReactNode }) {
  const text = extractText(children);
  const id = slugify(text);
  const Tag = level === 2 ? "h2" : "h3";
  return <Tag id={id}>{children}</Tag>;
}

function extractText(node: React.ReactNode): string {
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (node == null || typeof node !== "object") return "";
  if (Array.isArray(node)) return node.map(extractText).join("");
  if ("props" in node) {
    const el = node as { props: { children?: React.ReactNode } };
    return extractText(el.props.children);
  }
  return "";
}

const components = {
  h2: ({ children }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Heading level={2}>{children}</Heading>
  ),
  h3: ({ children }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Heading level={3}>{children}</Heading>
  ),
};

export default function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="wiki-article-body wl-prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
