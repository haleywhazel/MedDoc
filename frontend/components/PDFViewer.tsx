"use client";

import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface Props {
  fileUrl: string | null;
  page?: number | null;
}

export default function PDFViewer({ fileUrl, page }: Props) {
  const [numPages, setNumPages] = useState<number>();
  const containerRef = useRef<HTMLDivElement>(null);

  // reset when file changes
  useEffect(() => setNumPages(undefined), [fileUrl]);

  // scroll to requested page when ready
  useEffect(() => {
    if (page && containerRef.current) {
      const el = containerRef.current.querySelector(
        `[data-page-number="${page}"]`,
      );
      el && (el as HTMLElement).scrollIntoView({ behavior: "smooth" });
    }
  }, [page, numPages, fileUrl]);

  if (!fileUrl)
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No PDF selected
      </div>
    );

  const outOfRange = page && numPages && (page < 1 || page > numPages);

  return (
    <div
      ref={containerRef}
      className="overflow-y-scroll h-full bg-gray-50 border-r border-gray-300 p-2"
    >
      <Document
        file={fileUrl}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
        loading={<div className="p-4">Loading…</div>}
      >
        {outOfRange ? (
          <div className="text-center text-sm text-red-600 mt-4">
            File not found (page out of range)
          </div>
        ) : (
          numPages &&
          Array.from({ length: numPages }, (_, i) => i + 1).map((n) => (
            <Page key={n} pageNumber={n} width={500} />
          ))
        )}
      </Document>
    </div>
  );
}
