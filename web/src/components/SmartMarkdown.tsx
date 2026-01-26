"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

type SmartMarkdownProps = {
  content: string;
};

export default function SmartMarkdown({ content }: SmartMarkdownProps) {
  return (
    <div className="prose prose-invert max-w-none text-[15px] leading-7">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
        {content || ""}
      </ReactMarkdown>
    </div>
  );
}
