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
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      pdfInst.linkService?.scrollPageIntoView({ pageNumber: page });
    }
  }, [pdfInst, page]);

  if (!fileUrl)
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="w-24 h-24 bg-white rounded-2xl shadow-lg flex items-center justify-center mb-6">
          <svg
            className="w-12 h-12 text-slate-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <p className="text-slate-400 font-medium text-lg mb-2">
          No document selected
        </p>
        <p className="text-slate-400 text-sm">
          Ask a question to view relevant documents
        </p>
      </div>
    );

  const outOfRange = page && numPages && (page < 1 || page > numPages);

  return (
    <div className="h-full bg-slate-100 flex flex-col">
      {/* PDF Info Bar */}
      {numPages && (
        <div className="px-6 py-3 bg-white border-b border-slate-200 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-5 h-5 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                Document Viewer
              </p>
              <p className="text-xs text-slate-500">{numPages} pages total</p>
            </div>
          </div>
          {page && !outOfRange && (
            <div className="px-3 py-1.5 bg-blue-100 border border-blue-200 rounded-lg">
              <span className="text-xs font-semibold text-blue-700">
                Page {page}
              </span>
            </div>
          )}
        </div>
      )}

      {/* PDF Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <Document
          key={`${fileUrl}-${page ?? 0}`}
          className="flex flex-col items-center gap-6"
          file={fileUrl}
          onLoadSuccess={(doc) => {
            setNumPages(doc.numPages);
            setPdfInst(doc);
          }}
          loading={
            <div className="flex flex-col items-center justify-center p-12">
              <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
              <p className="text-slate-600 font-medium">Loading document...</p>
            </div>
          }
        >
          {outOfRange ? (
            <div className="flex flex-col items-center justify-center p-12 bg-red-50 border-2 border-red-200 rounded-xl">
              <svg
                className="w-12 h-12 text-red-500 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-red-700 font-semibold text-lg mb-1">
                Page Not Found
              </p>
              <p className="text-red-600 text-sm">
                The requested page is out of range
              </p>
            </div>
          ) : (
            numPages &&
            Array.from({ length: numPages }, (_, i) => i + 1).map((n) => (
              <div
                key={n}
                className={`shadow-lg rounded-lg overflow-hidden transition-all duration-300 ${
                  n === page ? "ring-4 ring-blue-400 ring-offset-4" : ""
                }`}
              >
                <Page
                  pageNumber={n}
                  width={600}
                  onRenderSuccess={() => {
                    if (n === page) {
                      const el = document.querySelector(
                        `[data-page-number="${n}"]`,
                      );
                      el &&
                        (el as HTMLElement).scrollIntoView({
                          behavior: "smooth",
                          block: "center",
                        });
                    }
                  }}
                />
              </div>
            ))
          )}
        </Document>
      </div>
    </div>
  );
}
