"use client";

import type { PDFDocumentProxy } from "pdfjs-dist";
import { useEffect, useState } from "react";
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

export default function PDFViewerClient({ fileUrl, page }: Props) {
  const [numPages, setNumPages] = useState<number>();
  const [pdfInst, setPdfInst] = useState<PDFDocumentProxy | null>(null);

  useEffect(() => {
    if (pdfInst && page) {
      // React-PDF exposes internal linkService for smooth navigation
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      pdfInst.linkService?.scrollPageIntoView({ pageNumber: page });
    }
  }, [pdfInst, page]);

  if (!fileUrl)
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No PDF selected
      </div>
    );

  const outOfRange = page && numPages && (page < 1 || page > numPages);

  return (
    <div className="overflow-y-scroll h-full bg-gray-50 border-r border-gray-300 p-2">
      <Document
        key={fileUrl}
        file={fileUrl}
        onLoadSuccess={(doc) => {
          setNumPages(doc.numPages);
          setPdfInst(doc);
        }}
        loading={<div className="p-4">Loading…</div>}
      >
        {outOfRange ? (
          <div className="text-center text-sm text-red-600 mt-4">
            File not found (page out of range)
          </div>
        ) : (
          numPages &&
          Array.from({ length: numPages }, (_, i) => i + 1).map((n) => (
            <Page
              key={n}
              pageNumber={n}
              width={500}
              onRenderSuccess={() => {
                if (n === page) {
                  const el = document.querySelector(
                    `[data-page-number="${n}"]`,
                  );
                  el && (el as HTMLElement).scrollIntoView({ behavior: "smooth" });
                }
              }}
            />
          ))
        )}
      </Document>
    </div>
  );
}
