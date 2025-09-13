import dynamic from "next/dynamic";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PDFViewer: any = dynamic(() => import("./PDFViewerClient"), { ssr: false });

export default PDFViewer;
