import dynamic from "next/dynamic";

export interface PDFViewerProps {
  fileUrl: string | null;
  page?: number | null;
}

// Dynamically import the client-side viewer with proper props typing
const PDFViewer = dynamic<PDFViewerProps>(
  () => import("./PDFViewerClient"),
  { ssr: false },
);

export default PDFViewer;
